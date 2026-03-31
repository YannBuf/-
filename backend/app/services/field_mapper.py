from typing import Dict, List, Optional
from enum import Enum


class StandardField(str, Enum):
    USER_ID = "user_id"
    EVENT_TYPE = "event_type"
    EVENT_TIME = "event_time"
    PRODUCT_ID = "product_id"
    ORDER_ID = "order_id"
    AMOUNT = "amount"


# Event type value mappings
EVENT_TYPE_MAPPINGS = {
    # English
    "impression": "impression",
    "browse": "impression",
    "view": "impression",
    "click": "click",
    "add_to_cart": "add_to_cart",
    "addcart": "add_to_cart",
    "cart": "add_to_cart",
    "remove_from_cart": "remove_from_cart",
    "removecart": "remove_from_cart",
    "checkout": "checkout",
    "begin_checkout": "checkout",
    "purchase": "purchase",
    "buy": "purchase",
    "order": "purchase",
    "paid": "purchase",
    "refund": "refund",
    "return": "refund",
    # Chinese
    "浏览": "impression",
    "访问": "impression",
    "点击": "click",
    "加购": "add_to_cart",
    "加入购物车": "add_to_cart",
    "取消加购": "remove_from_cart",
    "结算": "checkout",
    "下单": "purchase",
    "购买": "purchase",
    "支付": "purchase",
    "付款": "purchase",
    "退款": "refund",
    "退货": "refund",
}


class FieldMapper:
    """Map user column names to standard field names."""

    def __init__(self, column_mappings: Dict[str, str]):
        self.mappings = column_mappings
        self.reverse_mappings = {v: k for k, v in column_mappings.items()}

    def to_standard(self, data: List[Dict]) -> List[Dict]:
        """Convert data from user column names to standard field names."""
        result = []
        for row in data:
            new_row = {}
            for user_col, value in row.items():
                std_col = self.mappings.get(user_col, user_col)
                if std_col == "event_type" and isinstance(value, str):
                    value = self.normalize_event_type(value)
                new_row[std_col] = value
            result.append(new_row)
        return result

    @staticmethod
    def normalize_event_type(value: str) -> str:
        """Normalize event type value to standard enum."""
        value_lower = value.lower().strip()
        return EVENT_TYPE_MAPPINGS.get(value_lower, value_lower)


def auto_detect_mappings(columns: List[str]) -> Dict[str, str]:
    """Auto-detect column mappings based on column names."""
    from app.services.file_parser import detect_event_type_column, detect_user_id_column, detect_amount_column

    mappings = {}

    user_id_col = detect_user_id_column(columns)
    if user_id_col:
        mappings[user_id_col] = StandardField.USER_ID

    event_type_col = detect_event_type_column(columns)
    if event_type_col:
        mappings[event_type_col] = StandardField.EVENT_TYPE

    amount_col = detect_amount_column(columns)
    if amount_col:
        mappings[amount_col] = StandardField.AMOUNT

    return mappings