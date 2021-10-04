import logging
from sanic.request import Request
from typing import Text, Dict, Any, Optional

from rasa.core.channels.rest import RestInput

logger = logging.getLogger(__name__)


class CustomRestInput(RestInput):
    def get_metadata(self, request: Request) -> Optional[Dict[Text, Any]]:
        """Extracts additional information from the incoming request.

         Implementing this function is not required. However, it can be used to extract
         metadata from the request. The return value is passed on to the
         ``UserMessage`` object and stored in the conversation tracker.

        Args:
            request: incoming request with the message of the user

        Returns:
            Metadata which was extracted from the request.
        """
        channel_id = "pretend_id"
        user_id = "more_official_pretend_id"
        return {"user_id": user_id, "channel_id": channel_id}
