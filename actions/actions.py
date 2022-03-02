from typing import Text, List
import logging

from abc import ABC
from rasa.core.actions import actions

from rasa_sdk import FormValidationAction, ValidationAction, Tracker
from rasa_sdk.events import EventType, FollowupAction
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

        # Placeholder method that can be overwritten to add logic to the run method
        await self.extra_run_logic(dispatcher, tracker, domain, events)
        return events

    async def extra_run_logic(self, dispatcher, tracker, domain, events):
        return


class ValidateIntroForm(CustomFormValidationAction):

    def name(self) -> Text:
        return "validate_intro_form"

    async def entry_logic(self, dispatcher, tracker, domain, events):
        dispatcher.utter_message(text="I am the extra run logic and i should only be at the beginning of a form!")
        return []

