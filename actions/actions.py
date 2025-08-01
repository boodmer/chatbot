from typing import Any, List, Dict, Optional
import mysql.connector
from mysql.connector import Error

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

import re
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME"),
    'port': int(os.getenv("DB_PORT", 3306))
}

APP_URL = os.getenv("APP_URL", "http://127.0.0.1:8000")


# --- Normalization Functions ---

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
    match = re.search(r"(trên|dưới|từ)?\s*(\d+)\s*%?", text)

    if not match:
        return None

    op_map = {
        "trên": ">",
        "hơn": ">",
        "dưới": "<",
        "ít hơn": "<",
        "từ": ">=",
        None: ">="
    }

    op_word = match.group(1)
    value = int(match.group(2))
    operator = op_map.get(op_word, ">=")

    return {"operator": operator, "value": value}


def normalize_budget(text: str) -> Optional[Dict[str, Any]]:
    if text == "__skip__":
        return None

    text = str(text).lower().strip()

    if "rẻ" in text:
        return {"operator": "<", "value": 4_000_000}
    if "đắt" in text:
        return {"operator": ">", "value": 10_000_000}

    raw_num = re.sub(r"[^\d]", "", text)
    if raw_num.isdigit() and len(raw_num) > 5:
        return {"operator": "=", "value": int(raw_num)}

    match = re.search(r"(\d+(?:[.,]?\d*)?)\s*(triệu|tr|trieu)?", text)
    if not match:
        return None

    num = float(match.group(1).replace(',', '.'))
    value = int(num * 1_000_000)

    if "dưới" in text:
        return {"operator": "<", "value": value}
    if "trên" in text:
        return {"operator": ">", "value": value}
    if any(k in text for k in ["khoảng", "tầm", "~"]):
        return {"operator": "~", "value": (int(value * 0.9), int(value * 1.1))}

    return {"operator": "=", "value": value}


# --- SQL Query Helper ---

def build_product_query(category, budget, discount, name) -> (str, List[Any]):
    query = "SELECT id, name, price, description FROM products WHERE stock > 0"
    params = []

    if category:
        norm_category = normalize_category(category)
        if norm_category:
            query += " AND category = %s"
            params.append(norm_category)

    if budget:
        norm_budget = normalize_budget(budget)
        if norm_budget:
            op = norm_budget["operator"]
            val = norm_budget["value"]
            if op in ("<", ">", "<=", ">="):
                query += f" AND price {op} %s"
                params.append(val)
            elif op == "=":
                query += " AND price <= %s"
                params.append(val)
            elif op == "~":
                query += " AND price BETWEEN %s AND %s"
                params.extend(val)

    if discount:
        norm_discount = normalize_discount(discount)
        if norm_discount:
            op = norm_discount["operator"]
            val = norm_discount["value"]
            query += f" AND discount {op} %s"
            params.append(val)

    if name:
        query += " AND name LIKE %s"
        params.append(f"%{name}%")

    query += " ORDER BY price ASC LIMIT 3"
    return query, params


# --- Actions ---

class ActionRecommendBicycle(Action):
    def name(self) -> str:
        return "action_recommend_bicycle"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[Dict[str, Any]]:
        category = tracker.get_slot("category")
        budget = tracker.get_slot("budget")
        discount = tracker.get_slot("discount")
        name = tracker.get_slot("name")

        if not any([category, budget, name]):
            dispatcher.utter_message(text="Vui lòng cung cấp ít nhất tên, loại xe hoặc ngân sách.")
            return []

        try:
            query, params = build_product_query(category, budget, discount, name)

            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()

            if not results:
                message = "Không tìm thấy sản phẩm nào phù hợp với yêu cầu của bạn."
            else:
                message = "Dưới đây là những mẫu xe phù hợp với nhu cầu của bạn:\n" + "\n".join([
                    f'<p><a href="{APP_URL}/details/{row["id"]}" target="_blank">'
                    f'- {row["name"]} ({row["price"]:,} VND)</a></p>'
                    for row in results
                ])

            dispatcher.utter_message(text=message)

            cursor.close()
            conn.close()

            return [{"event": "slot", "name": "recommended_products", "value": message}]

        except Error as err:
            dispatcher.utter_message(text=f"Lỗi cơ sở dữ liệu: {err}")
            return []


class ActionShowCategoryDetail(Action):
    def name(self) -> str:
        return "action_show_category_detail"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[Dict[str, Any]]:
        category = tracker.get_slot("category_detail")

        if not category:
            dispatcher.utter_message(text="Bạn muốn biết thêm thông tin về loại xe nào?")
            return []

        norm_category = normalize_category(category)
        if not norm_category:
            dispatcher.utter_message(text="Tôi chưa rõ loại xe bạn muốn hỏi. Bạn có thể nói rõ hơn không?")
            return []

        detail_text = {
            "Xe đạp địa hình": (
                "Xe đạp địa hình được thiết kế để đi trên các địa hình gồ ghề như núi, rừng.\n"
                "- Khung xe chắc chắn, thường làm bằng hợp kim hoặc carbon\n"
                "- Lốp to, gai dày, giúp bám đường tốt\n"
                "- Phanh đĩa an toàn khi đổ dốc"
            ),
            "Xe đạp trẻ em": (
                "Xe đạp trẻ em nhỏ gọn, an toàn cho các bé.\n"
                "- Thiết kế dễ thương, màu sắc nổi bật\n"
                "- Có bánh phụ giữ thăng bằng\n"
                "- Yên và tay lái điều chỉnh được"
            ),
            "Xe đạp thể thao đường phố": (
                "Xe đạp đường phố nhẹ, linh hoạt, phù hợp di chuyển hàng ngày.\n"
                "- Kiểu dáng hiện đại, dễ đạp\n"
                "- Phù hợp đi làm, đi học trong nội đô\n"
                "- Thường có chắn bùn, gác ba-ga"
            ),
            "Xe đạp đua": (
                "Xe đạp đua dành cho tốc độ trên đường nhựa.\n"
                "- Khung siêu nhẹ\n"
                "- Ghi đông cong khí động học\n"
                "- Bánh mảnh giúp tăng tốc nhanh"
            )
        }

        dispatcher.utter_message(text=detail_text.get(norm_category, f"Tôi chưa có thông tin chi tiết về loại xe '{norm_category}'."))
        return []
