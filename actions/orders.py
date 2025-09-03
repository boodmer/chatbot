# actions/orders.py (hoặc thêm dưới maintenance.py nếu bạn chưa tách file)
from typing import Any, Dict, List
import mysql.connector
from mysql.connector import Error
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from .config import DB_CONFIG
from .utils import normalize_order_status

ORDERS_TABLE = "orders"
ORDER_ITEMS_TABLE = "order_items"

class ActionCheckOrderStatus(Action):
    def name(self) -> str:
        return "action_check_order_status"

    def run(self, dispatcher, tracker, domain):
        md = tracker.latest_message.get("metadata", {}) or {}
        user_id = md.get("user_id")
        if not user_id:
            dispatcher.utter_message("Vui lòng đăng nhập để xem tình trạng đơn hàng.")
            return []

        raw_status = tracker.get_slot("order_status")
        status_filter = normalize_order_status(raw_status)

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            # SQL với join
            query = """
                SELECT 
                    o.id            AS order_id,
                    o.order_date,
                    o.total_amount,
                    o.payment_method,
                    o.payment_status,
                    o.status        AS order_status,
                    o.updated_at    AS order_updated,
                    oi.product_id,
                    oi.quantity,
                    oi.price,
                    p.name          AS product_name
                FROM {orders} o
                JOIN {items} oi ON oi.order_id = o.id
                JOIN products p ON p.id = oi.product_id
                WHERE o.user_id = %s
            """.format(orders=ORDERS_TABLE, items=ORDER_ITEMS_TABLE)

            params = [user_id]
            if status_filter:
                query += " AND o.status = %s"
                params.append(status_filter)

            query += " ORDER BY o.updated_at DESC LIMIT 3"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            if not rows:
                dispatcher.utter_message("Không tìm thấy đơn hàng nào.")
                return []

            # gom nhóm theo order_id
            orders: Dict[int, Dict[str, Any]] = {}
            for r in rows:
                oid = r["order_id"]
                if oid not in orders:
                    orders[oid] = {
                        "info": r,
                        "items": []
                    }
                orders[oid]["items"].append(r)

            # render message
            blocks = []
            for oid, data in orders.items():
                info = data["info"]
                items = data["items"]

                block = [
                    f"- Đơn #{oid}: **{info['order_status']}**",
                    f"  Ngày đặt: {info['order_date']} · Tổng: {int(info['total_amount']):,} VND",
                    f"  Thanh toán: {info['payment_status']} ({info['payment_method']})",
                ]
                if info.get("order_updated"):
                    block.append(f"  Cập nhật: {info['order_updated']}")

                block.append("  Sản phẩm:")
                for it in items[:3]:
                    block.append(
                        f"    + {it['product_name']} x{it['quantity']} @ {int(it['price']):,} VND"
                    )
                if len(items) > 3:
                    block.append(f"    + ... và {len(items)-3} sản phẩm khác")

                blocks.append("\n".join(block))

            msg = "Các đơn hàng gần đây của bạn:\n" + "\n".join(blocks)
            dispatcher.utter_message(text=msg)
            return []

        except Error as err:
            dispatcher.utter_message(text=f"Lỗi CSDL: {err}")
            return []
        finally:
            try: cursor.close()
            except: pass
            try: conn.close()
            except: pass
