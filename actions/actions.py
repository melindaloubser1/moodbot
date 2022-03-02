from typing import Text, List
import logging

from abc import ABC

from rasa_sdk import FormValidationAction, Tracker
from rasa_sdk.events import EventType
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

logger = logging.getLogger(__name__)

class CustomFormValidationAction(FormValidationAction, ABC):
    def name(self):
        return

    async def run(
        self,
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> List[EventType]:
        events = await super().run(dispatcher, tracker, domain)
        logger.error("Run method!")
        logger.error(f"active loop {tracker.active_loop}")

        await self.extra_run_logic(dispatcher, tracker, domain, events)
        return events

    async def extra_run_logic(self, dispatcher, tracker, domain, events):
        return


class ValidateIntroForm(CustomFormValidationAction):

    def name(self) -> Text:
        return "validate_intro_form"

    async def extra_run_logic(self, dispatcher, tracker, domain, events):
        if tracker.get_slot("requested_slot") is None:
            dispatcher.utter_message(text="I am the extra run logic and I should run at the beginning of a form!")
        events.extend(await self.validate(dispatcher, tracker, domain))

        return events


