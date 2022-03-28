from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher


class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_check_successive_intent_repetitions"

    def get_full_intent_name(self, user_event: Dict):
        basic_intent = user_event["parse_data"]["intent"]["name"]
        full_intent = user_event["parse_data"]["response_selector"].get(basic_intent, {}).get("ranking",[{}])[0].get("intent_response_key", "basic_intent")
        return full_intent

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        intents = [self.get_full_intent_name(e) for e in reversed(tracker.events) if e["event"] == "user"]
        current_intent = intents.pop(0)

        successive_intent_repetitions = 0
        for intent in intents:
            if intent != current_intent:
                break
            successive_intent_repetitions += 1

        return [SlotSet("successive_intent_repetitions", successive_intent_repetitions)]
