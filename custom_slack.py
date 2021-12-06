import logging
from typing import Text, Dict, Any, Optional

from rasa.core.channels.slack import SlackInput, SlackBot
from rasa.core.channels.channel import OutputChannel
import logging
from typing import Any, Dict, Optional, Text

from rasa.core.channels.channel import OutputChannel


logger = logging.getLogger(__name__)

class CustomSlackBot(SlackBot):
    async def send_response(self, recipient_id: Text, message: Dict[Text, Any], latest_user_message: Dict[Text, Any]) -> None:
        """Send a message to the client."""

        last_message_confidence = latest_user_message.intent.get("confidence")
        if last_message_confidence and last_message_confidence < 0.5:
            self.slack_channel = None

        await super().send_response(recipient_id, message)


class CustomSlackInput(SlackInput):
    def get_output_channel(
        self, channel: Optional[Text] = None, thread_id: Optional[Text] = None
    ) -> OutputChannel:
        channel = channel or self.slack_channel
        return CustomSlackBot(self.slack_token, channel, thread_id, self.proxy)

