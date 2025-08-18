from typing import Any, Dict, List
import mysql.connector
from mysql.connector import Error
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from .config import DB_CONFIG, APP_URL
from .utils import build_product_query

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
            return [{"event": "slot", "name": "recommended_products", "value": message}]
        except Error as err:
            dispatcher.utter_message(text=f"Lỗi cơ sở dữ liệu: {err}")
            return []
        finally:
            try: cursor.close()
            except Exception: pass
            try: conn.close()
            except Exception: pass
