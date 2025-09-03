from typing import Any, Dict, List
import mysql.connector
from mysql.connector import Error
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from .config import DB_CONFIG
from .utils import normalize_maintenance_status

MAINTENANCE_TABLE = "maintenances"


class ActionCheckMaintenanceStatus(Action):
    def name(self) -> str:
        return "action_check_maintenance_status"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> List[Dict[str, Any]]:
        # bắt buộc phải có user_id trong metadata
        md = tracker.latest_message.get("metadata", {}) or {}
        user_id = md.get("user_id")
        if not user_id:
            dispatcher.utter_message(
                text="Vui lòng đăng nhập để xem tình trạng bảo trì.")
            return []

        # lấy slot trạng thái (có thể là '__skip__' hoặc để trống)
        raw_status = tracker.get_slot("maintenance_status")
        norm_status = normalize_maintenance_status(raw_status)

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            query = (
                f"SELECT id, status, issue_description, preferred_date, updated_at "
                f"FROM {MAINTENANCE_TABLE} "
                f"WHERE user_id = %s"
            )
            params = [user_id]

            if norm_status:
                query += " AND status = %s"
                params.append(norm_status)

            query += " ORDER BY updated_at DESC LIMIT 3"

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            if not rows:
                dispatcher.utter_message(
                    text="Không tìm thấy đơn bảo trì nào với điều kiện này.")
                return []

            lines = []
            for r in rows:
                line = f"- Mã đơn #{r['id']}: **{r.get('status') or 'Không rõ'}**"
                if r.get("issue_description"):
                    line += f" · Vấn đề: {r['issue_description']}"
                if r.get("preferred_date"):
                    line += f" · Ngày hẹn: {r['preferred_date']}"
                if r.get("updated_at"):
                    line += f" · Cập nhật: {r['updated_at']}"
                lines.append(line)

            msg = "Tình trạng các đơn bảo trì gần đây:\n" + "\n".join(lines)
            dispatcher.utter_message(text=msg)

            return []

        except Error as err:
            dispatcher.utter_message(text=f"Lỗi cơ sở dữ liệu: {err}")
            return []
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
