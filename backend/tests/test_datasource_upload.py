import pytest
import os
import tempfile
from io import BytesIO
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import UploadFile

from app.services.datasource import save_file, validate_file_size, upload_and_parse
from app.services.file_parser import FileParser
from app.services.field_mapper import auto_detect_mappings


class TestSaveFile:
    """Test save_file function."""

    def test_save_file_creates_directory(self):
        """Test that save_file creates storage directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = os.path.join(tmp_dir, "uploads")
            content = b"user_id,event_type,amount\n1,purchase,100"

            file_path = save_file(content, "test.csv", storage_path)

            assert os.path.exists(storage_path)
            assert os.path.isfile(file_path)
            assert file_path.endswith(".csv")

    def test_save_file_with_unique_filename(self):
        """Test that save_file generates unique filenames."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage_path = os.path.join(tmp_dir, "uploads")
            content = b"col1\nval1"

            path1 = save_file(content, "test.csv", storage_path)
            path2 = save_file(content, "test.csv", storage_path)

            assert path1 != path2


class TestValidateFileSize:
    """Test validate_file_size function."""

    def test_validate_file_size_within_limit(self):
        """Test that files within limit pass validation."""
        content = b"x" * (10 * 1024 * 1024)  # 10MB
        # Should not raise
        validate_file_size(content)

    def test_validate_file_size_exceeds_limit(self):
        """Test that files exceeding limit raise ValueError."""
        from app.config import get_settings
        settings = get_settings()
        content = b"x" * (settings.MAX_FILE_SIZE + 1)

        with pytest.raises(ValueError, match="exceeds maximum allowed size"):
            validate_file_size(content)


class TestFileParser:
    """Test FileParser.parse method."""

    def test_parse_csv_file(self):
        """Test parsing a CSV file."""
        csv_content = b"""user_id,event_type,amount
        1,purchase,100
        1,click,0
        2,browse,0"""

        result = FileParser.parse(csv_content, "test.csv")

        assert "columns" in result
        assert "column_types" in result
        assert "row_count" in result
        assert "sample_data" in result
        assert "data" in result
        assert result["row_count"] == 3
        assert "user_id" in result["columns"]

    def test_parse_unsupported_file_type(self):
        """Test parsing an unsupported file type raises error."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            FileParser.parse(b"some content", "test.txt")


class TestAutoDetectMappings:
    """Test auto_detect_mappings function."""

    def test_detect_user_id_column(self):
        """Test user_id column detection."""
        columns = ["user_id", "event_type", "amount"]
        mappings = auto_detect_mappings(columns)

        assert mappings.get("user_id") == "user_id"

    def test_detect_event_type_column(self):
        """Test event_type column detection."""
        columns = ["user_id", "event_type", "amount"]
        mappings = auto_detect_mappings(columns)

        assert mappings.get("event_type") == "event_type"

    def test_detect_amount_column(self):
        """Test amount column detection."""
        columns = ["user_id", "event_type", "amount"]
        mappings = auto_detect_mappings(columns)

        assert mappings.get("amount") == "amount"

    def test_detect_chinese_columns(self):
        """Test detection of Chinese column names."""
        columns = ["用户ID", "事件类型", "金额"]
        mappings = auto_detect_mappings(columns)

        # Should detect user and event type columns
        assert "事件类型" in mappings

    def test_no_mappings_for_unknown_columns(self):
        """Test that unknown columns return empty mappings."""
        columns = ["foo", "bar", "baz"]
        mappings = auto_detect_mappings(columns)

        assert len(mappings) == 0


class TestUploadAndParse:
    """Test upload_and_parse function."""

    @pytest.mark.asyncio
    async def test_upload_and_parse_workflow(self):
        """Test the complete upload and parse workflow."""
        # Mock database session
        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # Create a mock file
        csv_content = b"user_id,event_type,amount\n1,purchase,100\n1,click,0"
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.csv"
        mock_file.read = AsyncMock(return_value=csv_content)
        mock_file.seek = AsyncMock()

        # Mock the datasource creation
        mock_datasource = MagicMock()
        mock_datasource.id = 1
        mock_db.add = MagicMock()

        with patch('app.services.datasource.create_datasource', return_value=mock_datasource) as mock_create, \
             patch('app.services.datasource.run_funnel_analysis') as mock_task:

            mock_task.delay.return_value.id = "test-task-id"

            result = await upload_and_parse(
                db=mock_db,
                user_id=1,
                file=mock_file,
                name="Test DataSource"
            )

            # Verify datasource was created
            mock_create.assert_called_once()

            # Verify task was triggered
            mock_task.delay.assert_called_once()

            # Verify result structure
            assert "task_id" in result
            assert "datasource_id" in result
            assert "parsed" in result
            assert "mappings" in result
            assert result["task_id"] == "test-task-id"
