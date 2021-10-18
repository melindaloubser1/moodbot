
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import EventType, SessionStarted, ActionExecuted
from rasa_sdk.executor import CollectingDispatcher


class ActionSessionStart(Action):

    def name(self) -> Text:
        return "action_session_start"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        """Executes the custom action"""
        # the session should begin with a `session_started` event
        events = [SessionStarted()]

        dispatcher.utter_message(template="default_start_message")
        # add `action_listen` at the end
        events.append(ActionExecuted("action_listen"))

        return events
