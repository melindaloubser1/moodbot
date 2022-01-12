from typing import Text, List, Any
import logging

from rasa_sdk.types import DomainDict
from rasa_sdk import FormValidationAction, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    ActiveLoop,
    ActionExecutionRejected,
)

logger = logging.getLogger(__name__)


class ValidateIntroForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_intro_form"

    def should_deactivate(self, tracker: Tracker, domain: DomainDict) -> bool:
        ignored_intents = domain.get("forms").get(self.form_name()).get("ignored_intents")
        logger.error(ignored_intents)
        return tracker.latest_message.get("intent").get("name") in ignored_intents

    async def run(
        self,
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> List[Any]:
        if self.should_deactivate(tracker, domain):
            logger.error("deactivating")
            events = [
                SlotSet("requested_slot", None),
                SlotSet("name", None),
                ActiveLoop(None),
                ActionExecutionRejected(self.form_name())
            ]
            return events

        return await super().run(dispatcher, tracker, domain)
