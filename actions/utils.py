from typing import Any, Dict, List, Optional
import re

def normalize_category(category: str) -> Optional[str]:
    cat = category.lower().strip()
    if "địa hình" in cat or "mountain" in cat:
        return "Xe đạp địa hình"
    if "trẻ" in cat or "kid" in cat:
        return "Xe đạp trẻ em"
    if any(k in cat for k in ["đường phố", "city", "touring"]):
        return "Xe đạp thể thao đường phố"
    if "đua" in cat or "road" in cat:
        return "Xe đạp đua"
    return None

def normalize_discount(text: str) -> Optional[Dict[str, Any]]:
    if text == "__skip__":
        return None
    text = str(text).lower().strip()
    m = re.search(r"(trên|dưới|từ)?\s*(\d+)\s*%?", text)
    if not m:
        return None
    op_map = {"trên": ">", "hơn": ">", "dưới": "<", "ít hơn": "<", "từ": ">=", None: ">="}
    return {"operator": op_map.get(m.group(1), ">="), "value": int(m.group(2))}

def normalize_budget(text: str) -> Optional[Dict[str, Any]]:
    if text == "__skip__":
        return None
    text = str(text).lower().strip()
    if "rẻ" in text:
        return {"operator": "<", "value": 4_000_000}
    if "đắt" in text:
        return {"operator": ">", "value": 10_000_000}
    import re
    raw_num = re.sub(r"[^\d]", "", text)
    if raw_num.isdigit() and len(raw_num) > 5:
        return {"operator": "=", "value": int(raw_num)}
    m = re.search(r"(\d+(?:[.,]?\d*)?)\s*(triệu|tr|trieu)?", text)
    if not m:
        return None
    num = float(m.group(1).replace(',', '.'))
    value = int(num * 1_000_000)
    if "dưới" in text:
        return {"operator": "<", "value": value}
    if "trên" in text:
        return {"operator": ">", "value": value}
    if any(k in text for k in ["khoảng", "tầm", "~"]):
        return {"operator": "~", "value": (int(value*0.9), int(value*1.1))}
    return {"operator": "=", "value": value}

def build_product_query(category, budget, discount, name) -> (str, List[Any]):
    query = "SELECT id, name, price, description FROM products WHERE stock > 0"
    params: List[Any] = []
    if category:
        nc = normalize_category(category)
        if nc:
            query += " AND category = %s"; params.append(nc)
    if budget:
        nb = normalize_budget(budget)
        if nb:
            op, val = nb["operator"], nb["value"]
            if op in ("<", ">", "<=", ">="):
                query += f" AND price {op} %s"; params.append(val)
            elif op == "=":
                query += " AND price <= %s"; params.append(val)
            elif op == "~":
                query += " AND price BETWEEN %s AND %s"; params.extend(val)
    if discount:
        nd = normalize_discount(discount)
        if nd:
            query += f" AND discount {nd['operator']} %s"; params.append(nd["value"])
    if name:
        query += " AND name LIKE %s"; params.append(f"%{name}%")
    query += " ORDER BY price ASC LIMIT 3"
    return query, params


def normalize_maintenance_status(text: Optional[str]) -> Optional[str]:
    """
    Trả về 1 trong 3 giá trị chuẩn:
    - 'Đang xử lý'
    - 'Hoàn thành'
    - 'Hủy'
    hoặc None nếu không khớp / '__skip__'
    """
    if text is None or text == "__skip__":
        return None

    t = str(text).lower().strip()

    # Đang xử lý
    if any(k in t for k in [
        "đang xử lý", "dang xu ly", "processing", "đang làm", "dang lam",
        "chờ xử lý", "cho xu ly", "pending"
    ]):
        return "Đang xử lý"

    # Hoàn thành
    if any(k in t for k in [
        "hoàn thành", "hoan thanh", "xong", "đã xong", "da xong",
        "done", "complete", "completed", "finish", "finished"
    ]):
        return "Hoàn thành"

    # Hủy
    if any(k in t for k in [
        "hủy", "huy", "canceled", "cancelled", "cancel", "đã hủy", "da huy"
    ]):
        return "Hủy"

    return None

    # actions/utils.py (hoặc cùng file đang chứa normalize_*)
from typing import Optional

def normalize_order_status(text: Optional[str]) -> Optional[str]:
    """
    Chuẩn về 1 trong 6 giá trị:
      - 'Chờ thanh toán'
      - 'Đang xử lý'
      - 'Đã giao'
      - 'Đã hủy'
      - 'Giao hàng'
      - 'Chờ xác nhận hủy'
    Trả None nếu '__skip__' hoặc không khớp.
    """
    if text is None or text == "__skip__":
        return None

    t = str(text).lower().strip()

    if any(k in t for k in ["chờ thanh toán", "cho thanh toan", "chua thanh toan", "unpaid", "pending payment"]):
        return "Chờ thanh toán"
    if any(k in t for k in ["đang xử lý", "dang xu ly", "processing"]):
        return "Đang xử lý"
    if any(k in t for k in ["đã giao", "da giao", "delivered", "đã giao hàng", "da giao hang"]):
        return "Đã giao"
    if any(k in t for k in ["đã hủy", "da huy", "hủy", "huy", "canceled", "cancelled"]):
        return "Đã hủy"
    if any(k in t for k in ["giao hàng", "giao hang", "shipping", "đang giao", "dang giao"]):
        return "Giao hàng"
    if any(k in t for k in ["chờ xác nhận hủy", "cho xac nhan huy", "pending cancel", "awaiting cancel"]):
        return "Chờ xác nhận hủy"

    return None
