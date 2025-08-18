from typing import Any, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.types import DomainDict
from rasa_sdk.executor import CollectingDispatcher
from .utils import normalize_category

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
