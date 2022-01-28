from typing import Text, Dict, Any
import logging

from rasa_sdk.types import DomainDict
from rasa_sdk import FormValidationAction, Tracker
from rasa_sdk.executor import CollectingDispatcher

logger = logging.getLogger(__name__)


class ValidateGreetForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_greet_form"

    def validate_name(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        if value=="Me":
            return {"name": value}
        else:
            dispatcher.utter_message(template="utter_no_name")
            return {"name": None}
