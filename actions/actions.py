from logging import shutdown
from typing import Text, List, Any, overload
import logging
from copy import deepcopy

from rasa_sdk.types import DomainDict
from rasa_sdk import FormValidationAction, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    ActiveLoop,
    ActionExecutionRejected,
    UserUtteranceReverted,
    UserUttered,
)

logger = logging.getLogger(__name__)


class ValidateGreetForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_greet_form"

    def should_deactivate(self, tracker: Tracker) -> bool:
        return "q" in tracker.latest_message.get("text")
    
    def get_second_intent_parse_data(self, tracker: Tracker) -> dict:
        intent_ranking = tracker.latest_message.get("intent_ranking", [])
        if len(intent_ranking) < 2:
            return {}
        return intent_ranking[1]

    def compose_parse_data(self, tracker, override_intent_data):
        parse_data = deepcopy(tracker.latest_message)
        parse_data["intent"] = override_intent_data
        parse_data["intent"]["confidence"] = 1.0
        parse_data["intent_ranking"] = []
        return parse_data

    async def run(
        self,
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> List[Any]:
        if self.should_deactivate(tracker):
            override_intent_data = self.get_second_intent_parse_data(tracker)
            events = [
                SlotSet("requested_slot", None),
                SlotSet("name", None),
                ActiveLoop(None),
                ActionExecutionRejected(self.form_name()),
                UserUttered(
                    tracker.latest_message.get("text"), parse_data=self.compose_parse_data(tracker, override_intent_data)
                ),
            ]
            return events

        return await super().run(dispatcher, tracker, domain)
