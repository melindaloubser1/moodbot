from typing import Text, List, Any
import logging

from abc import ABC

from rasa_sdk import FormValidationAction, ValidationAction, Tracker
from rasa_sdk.events import EventType, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

logger = logging.getLogger(__name__)

class ValidatePredefinedSlots(ValidationAction):
    def extract_form_initialized(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ):
        if not tracker.active_loop or not tracker.get_slot("form_initialized"):
            return {"form_initialized": False}
        else:
            return {"form_initialized": True}

class CustomFormValidationAction(FormValidationAction, ABC):
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        events = []
        if not tracker.get_slot("form_initialized"):
            events.extend(await self.extra_run_logic(dispatcher, tracker, domain))
        events.extend(await super().run(dispatcher, tracker, domain))
        return events

    def validate_form_initialized(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ):
        return {"form_initialized": True}

    async def extra_run_logic(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ):
        return []


class ValidateIntroForm(CustomFormValidationAction):

    def name(self) -> Text:
        return "validate_intro_form"

    async def extra_run_logic(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ):
        events = await super().extra_run_logic()
        dispatcher.utter_message(text="I am the extra run logic and I should run at the beginning of a form!")
        events.append(SlotSet("example_slot_to_set_on_form_entry", "value"))
        return events

