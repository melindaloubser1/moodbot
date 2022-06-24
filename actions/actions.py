from typing import Text, List, Optional

from rasa_sdk import FormValidationAction, Tracker
from rasa_sdk.executor import CollectingDispatcher

import logging
logger = logging.getLogger(__name__)

class ValidateSomeForm(FormValidationAction):

    def name(self) -> Text:
        """Unique identifier of the form. """
        return "validate_some_form"

    async def required_slots(
            self,
            domain_slots: List[Text],
            dispatcher: "CollectingDispatcher",
            tracker: "Tracker",
            domain,
    ) -> Optional[List[Text]]:

        logger.debug("Inside required_slots")
        return []