import json
import logging
import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from app.models.datasource import DataSource, Dataset
from app.schemas.datasource import DataSourceCreate
from app.services.file_parser import FileParser
from app.services.field_mapper import FieldMapper, auto_detect_mappings
from app.tasks.analyze import run_funnel_analysis, run_rfm_analysis
from app.config import get_settings

logger = logging.getLogger(__name__)


async def create_datasource(
    db: AsyncSession,
    user_id: int,
    data: DataSourceCreate,
    config: Optional[dict] = None,
) -> DataSource:
    datasource = DataSource(
        user_id=user_id,
        name=data.name,
        type=data.type,
        config=config or {},
    )
    db.add(datasource)
    await db.commit()
    await db.refresh(datasource)
    return datasource


async def get_user_datasources(db: AsyncSession, user_id: int) -> list[DataSource]:
    result = await db.execute(
        select(DataSource)
        .where(DataSource.user_id == user_id)
        .order_by(DataSource.created_at.desc())
    )
    return result.scalars().all()


async def get_datasource(db: AsyncSession, datasource_id: int, user_id: int) -> Optional[DataSource]:
    result = await db.execute(
        select(DataSource)
        .where(DataSource.id == datasource_id, DataSource.user_id == user_id)
    )
    return result.scalar_one_or_none()


def save_file(content: bytes, filename: str, storage_path: Optional[str] = None) -> str:
    """
    Save file content to storage directory with unique filename.

    Args:
        content: File content bytes
        filename: Original filename (used only for extension)
        storage_path: Directory to save file (defaults to STORAGE_PATH from settings)

    Returns:
        Absolute path to saved file
    """
    settings = get_settings()
    save_dir = storage_path or settings.STORAGE_PATH
    logger.info(f"[SAVE_FILE] save_dir={save_dir}, filename={filename}")

    # Ensure storage directory exists
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"[SAVE_FILE] Directory ensured: {save_dir}")

    # Generate unique filename
    ext = os.path.splitext(filename)[1] if filename else ""
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(save_dir, unique_filename)
    logger.info(f"[SAVE_FILE] Saving to: {file_path}")

    # Write file content
    try:
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"[SAVE_FILE] File written successfully, size={len(content)} bytes")
    except OSError as e:
        logger.error(f"[SAVE_FILE] OS error writing file: {e}")
        raise

    return file_path


def validate_file_size(content: bytes) -> None:
    """
    Validate file size against MAX_FILE_SIZE.

    Raises:
        ValueError: If file exceeds MAX_FILE_SIZE
    """
    settings = get_settings()
    if len(content) > settings.MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE / (1024*1024):.0f}MB")


async def upload_and_parse(
    db: AsyncSession,
    user_id: int,
    file: UploadFile,
    name: str,
) -> Dict[str, Any]:
    """
    Upload file, parse it, detect mappings, and trigger analysis.

    Args:
        db: Database session
        user_id: User ID
        file: Uploaded file
        name: DataSource name

    Returns:
        Dict with task_id, parsed data, and mappings
    """
    settings = get_settings()
    logger.info(f"[UPLOAD] Starting upload for user_id={user_id}, filename={file.filename}, name={name}")

    try:
        # 1. Read file content and validate size
        logger.info(f"[UPLOAD] Step 1: Reading file content...")
        content = await file.read()
        logger.info(f"[UPLOAD] File read complete, size={len(content)} bytes")
        validate_file_size(content)

        # Reset file position for potential re-reads
        await file.seek(0)

        # 2. Save file to storage
        logger.info(f"[UPLOAD] Step 2: Saving file to storage...")
        file_path = save_file(content, file.filename)
        logger.info(f"[UPLOAD] File saved to: {file_path}")

        # 3. Parse file content
        logger.info(f"[UPLOAD] Step 3: Parsing file content...")
        parsed = FileParser.parse(content, file.filename)
        logger.info(f"[UPLOAD] Parse complete, columns={parsed['columns']}, rows={parsed['row_count']}")

        # 4. Auto-detect field mappings
        logger.info(f"[UPLOAD] Step 4: Auto-detecting field mappings...")
        mappings = auto_detect_mappings(parsed["columns"])
        logger.info(f"[UPLOAD] Mappings detected: {mappings}")

        # 5. Create datasource record
        logger.info(f"[UPLOAD] Step 5: Creating datasource record...")
        data = DataSourceCreate(name=name, type="file")
        config = {
            "file_path": file_path,
            "original_filename": file.filename,
        }
        datasource = await create_datasource(db, user_id=user_id, data=data, config=config)
        logger.info(f"[UPLOAD] Datasource created with id={datasource.id}")

        # 6. Convert data to standard format
        logger.info(f"[UPLOAD] Step 6: Converting data to standard format...")
        mapper = FieldMapper(mappings)
        try:
            parsed_data = json.loads(parsed["data"])
        except json.JSONDecodeError as e:
            logger.error(f"[UPLOAD] JSON parse error: {e}")
            raise ValueError(f"Failed to parse file data as JSON: {e}")
        standard_data = mapper.to_standard(parsed_data)
        logger.info(f"[UPLOAD] Data converted, standard_data rows={len(standard_data)}")

        # 7. Trigger Celery analysis tasks (both funnel and RFM)
        logger.info(f"[UPLOAD] Step 7: Triggering Celery tasks...")
        funnel_task_id = None
        rfm_task_id = None
        try:
            funnel_task = run_funnel_analysis.delay(standard_data, user_id, datasource.id)
            rfm_task = run_rfm_analysis.delay(standard_data, user_id, datasource.id)
            funnel_task_id = funnel_task.id
            rfm_task_id = rfm_task.id
            logger.info(f"[UPLOAD] Celery tasks queued: funnel={funnel_task_id}, rfm={rfm_task_id}")
        except Exception as celery_err:
            logger.warning(f"[UPLOAD] Celery task queue failed (tasks will not run): {celery_err}")
            # Don't fail the upload if Celery is unavailable

        logger.info(f"[UPLOAD] Upload completed successfully for datasource_id={datasource.id}")
        return {
            "task_id": funnel_task_id,
            "rfm_task_id": rfm_task_id,
            "datasource_id": datasource.id,
            "parsed": parsed,
            "mappings": mappings,
        }

    except ValueError as ve:
        logger.error(f"[UPLOAD] Validation error: {ve}")
        raise
    except Exception as e:
        logger.exception(f"[UPLOAD] Unexpected error during upload: {e}")
        raise
