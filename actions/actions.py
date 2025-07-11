from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

MOCK_PRODUCTS = {
    "laptop": [
        {"name": "BudgetBook", "price": 499},
        {"name": "UltraBook Pro", "price": 999}
    ],
    "phone": [
        {"name": "Phone Lite", "price": 399},
        {"name": "Phone Max", "price": 799}
    ]
}

class ActionRecommendProduct(Action):
    def name(self):
        return "action_recommend_product"

    def run(self, dispatcher, tracker: Tracker, domain):
        ptype = tracker.get_slot("product_type")

        if not ptype:
            dispatcher.utter_message("I need to know what kind of product you're looking for.")
            return []

        options = MOCK_PRODUCTS.get(ptype.lower(), [])
        if not options:
            dispatcher.utter_message(f"Sorry, I don't have any recommendations for '{ptype}'.")
            return []

        message = f"Here are some {ptype}s you might like:"
        for item in options:
            message += f"\n- {item['name']} (${item['price']})"

        dispatcher.utter_message(message)
        return []
