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
        if (
            not tracker.active_loop
            or not tracker.get_slot("form_initialized")
        ):
            return {"form_initialized": False}
        else:
            return {"form_initialized": True}


class CustomFormValidationAction(FormValidationAction, ABC):
    def name(self) -> Text:
        return "custom_form_validation_action"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        events = []
        if not tracker.get_slot("form_initialized") or tracker.get_slot("last_active_loop")!= self.form_name():
            events.extend([SlotSet("last_active_loop", self.form_name())])
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
        events = await super().extra_run_logic(dispatcher, tracker, domain)
        dispatcher.utter_message(text="I am the first form")
        return events


class ValidateSecondIntroForm(CustomFormValidationAction):
    def name(self) -> Text:
        return "validate_second_intro_form"

    def validate_name(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict):
        last_user_event_index = [-i for i, event in enumerate(reversed(tracker.events)) if event.get("event")=="user"][0]
        events_since_last_message = tracker.events[last_user_event_index:]
        if any([event.get("event")=="active_loop" and event.get("name")==None for event in events_since_last_message]):
            return {"name": None}
        return {"name": slot_value}

    async def extra_run_logic(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ):
        events = await super().extra_run_logic(dispatcher, tracker, domain)
        dispatcher.utter_message(text="I am the second form")
        events.append(SlotSet("name", None))
        return events
