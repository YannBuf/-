from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.report_generator import ReportGenerator
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import os

router = APIRouter()


class ReportRequest(BaseModel):
    report_type: str  # "weekly", "monthly", "funnel", "rfm", "custom"
    title: Optional[str] = None
    data: Dict[str, Any]


class ReportResponse(BaseModel):
    id: str
    title: str
    type: str
    format: str  # "html", "pdf"
    download_url: str
    created_at: str


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a report from analysis data."""
    try:
        # Use storage/reports as output directory
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "reports")
        generator = ReportGenerator(output_dir=output_dir)

        # Generate report
        title = request.title or f"{request.report_type}报告"
        file_path = await generator.generate(
            report_type=request.report_type,
            data=request.data,
            title=title,
        )

        return ReportResponse(
            id=f"report_{datetime.now().timestamp()}",
            title=title,
            type=request.report_type,
            format="pdf",
            download_url=f"/api/reports/download/{file_path.split('/')[-1]}",
            created_at=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_report(filename: str):
    """Download a generated PDF report."""
    # Build the path to the reports directory
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "reports")
    file_path = os.path.join(reports_dir, filename)

    # Security check: ensure filename doesn't contain path traversal
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
    )


@router.get("/list")
async def list_reports(
    db: AsyncSession = Depends(get_db),
):
    """List user's reports."""
    # Mock for now - would query database in production
    return {
        "reports": [
            {
                "id": "1",
                "name": "本周数据周报",
                "type": "weekly",
                "date": "2024-01-15",
                "status": "ready",
            },
            {
                "id": "2",
                "name": "1月数据月报",
                "type": "monthly",
                "date": "2024-01-01",
                "status": "ready",
            },
            {
                "id": "3",
                "name": "转化漏斗分析",
                "type": "funnel",
                "date": "2024-01-14",
                "status": "ready",
            },
            {
                "id": "4",
                "name": "客户分层报告",
                "type": "rfm",
                "date": "2024-01-10",
                "status": "ready",
            },
        ]
    }


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get report details."""
    # Mock for now
    return {
        "id": report_id,
        "name": "报告",
        "type": "weekly",
        "content": "<html>报告内容</html>",
    }
