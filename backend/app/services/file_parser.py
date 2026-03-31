import pandas as pd
import json
from typing import Dict, List, Any, Optional
from io import BytesIO


class FileParser:
    """Parse CSV and Excel files into standardized format."""

    SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

    @classmethod
    def parse(cls, file_content: bytes, filename: str) -> Dict[str, Any]:
        ext = "." + filename.split(".")[-1].lower()

        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")

        df = cls._read_file(file_content, ext)

        return {
            "columns": list(df.columns),
            "column_types": {col: str(df[col].dtype) for col in df.columns},
            "row_count": len(df),
            "sample_data": df.head(10).to_dict(orient="records"),
            "data": df.to_json(orient="records", date_format="iso"),
        }

    @classmethod
    def _read_file(cls, content: bytes, ext: str) -> pd.DataFrame:
        buffer = BytesIO(content)

        if ext == ".csv":
            return pd.read_csv(buffer, encoding="utf-8-sig")
        elif ext in {".xlsx", ".xls"}:
            return pd.read_excel(buffer, engine="openpyxl" if ext == ".xlsx" else "xlrd")

        raise ValueError(f"Cannot parse extension: {ext}")


def detect_event_type_column(columns: List[str]) -> Optional[str]:
    """Auto-detect which column likely contains event_type data."""
    event_type_patterns = [
        "event", "behavior", "action", "type",
        "事件", "行为", "类型", "操作",
    ]

    for col in columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in event_type_patterns):
            return col
    return None


def detect_user_id_column(columns: List[str]) -> Optional[str]:
    """Auto-detect which column likely contains user_id data."""
    user_id_patterns = [
        "user", "member", "buyer", "customer", "userid", "uid",
        "用户", "会员", "买家", "customer_id", "user_id",
    ]

    for col in columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in user_id_patterns):
            return col
    return None


def detect_amount_column(columns: List[str]) -> Optional[str]:
    """Auto-detect which column likely contains amount/money data."""
    amount_patterns = [
        "amount", "money", "price", "payment", "revenue", "total", "sum",
        "金额", "价格", "付款", "收入", "总价",
    ]

    for col in columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in amount_patterns):
            return col
    return None