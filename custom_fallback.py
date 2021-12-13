import logging
from typing import Any, List, Type, Text, Dict, Union, Tuple, Optional

from rasa.shared.constants import DEFAULT_NLU_FALLBACK_INTENT_NAME

from rasa.nlu.classifiers.fallback_classifier import (
    FallbackClassifier,
    THRESHOLD_KEY,
    AMBIGUITY_THRESHOLD_KEY,
)
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.constants import (
    INTENT,
    INTENT_NAME_KEY,
    PREDICTED_CONFIDENCE_KEY,
    RESPONSE_SELECTOR,
)
from rasa.nlu.constants import (
    RESPONSE_SELECTOR_RETRIEVAL_INTENTS,
    RESPONSE_SELECTOR_DEFAULT_INTENT,
    RESPONSE_SELECTOR_RANKING_KEY,
)

logger = logging.getLogger(__name__)

 
class ResponseSelectorFallbackClassifier(FallbackClassifier):
    def _should_fallback(self, message: Message) -> bool:
        """Check if the fallback intent should be predicted based on ResponseSelector confidence

        Args:
            message: The current message and its intent predictions.

        Returns:
            `True` if the fallback intent should be predicted.
        """
        intent_name = message.data[INTENT].get(INTENT_NAME_KEY)
        if intent_name not in self._all_response_selector_intents(message):
            return False

        below_threshold, nlu_confidence = self._nlu_confidence_below_threshold(message)
        intent_name = self._full_response_selector_intent_name(message)

        if below_threshold:
            logger.debug(
                f"ResponseSelector confidence {nlu_confidence} for intent '{intent_name}' is lower "
                f"than ResponseSelector threshold {self.component_config[THRESHOLD_KEY]:.2f}."
            )
            return True

        ambiguous_prediction, confidence_delta = self._nlu_prediction_ambiguous(message)
        if ambiguous_prediction:
            logger.debug(
                f"The difference in NLU confidences "
                f"for the top two ResponseSelector sub-intents ({confidence_delta}) is lower than "
                f"the ambiguity threshold "
                f"{self.component_config[AMBIGUITY_THRESHOLD_KEY]:.2f}. Predicting "
                f"intent '{DEFAULT_NLU_FALLBACK_INTENT_NAME}' instead of "
                f"'{intent_name}'."
            )
            return True

        return False

    def _nlu_confidence_below_threshold(
        self,
        message: Message,
        response_selector_intent: str = RESPONSE_SELECTOR_DEFAULT_INTENT,
    ) -> Tuple[bool, float]:
        nlu_confidence = message.data[RESPONSE_SELECTOR][response_selector_intent][
            RESPONSE_SELECTOR_RANKING_KEY
        ][0][PREDICTED_CONFIDENCE_KEY]
        return nlu_confidence < self.component_config[THRESHOLD_KEY], nlu_confidence

    def _nlu_prediction_ambiguous(
        self,
        message: Message,
        response_selector_intent: str = RESPONSE_SELECTOR_DEFAULT_INTENT,
    ) -> Tuple[bool, Optional[float]]:
        sub_intents = self._response_selector_rankings(
            message, response_selector_intent
        )
        if len(sub_intents) >= 2:
            first_confidence = sub_intents[0].get(PREDICTED_CONFIDENCE_KEY, 1.0)
            second_confidence = sub_intents[1].get(PREDICTED_CONFIDENCE_KEY, 1.0)
            difference = first_confidence - second_confidence
            return (
                difference < self.component_config[AMBIGUITY_THRESHOLD_KEY],
                difference,
            )
        return False, None

    def _all_response_selector_intents(self, message: Message) -> List:
        return message.data.get(RESPONSE_SELECTOR, {}).get(
            RESPONSE_SELECTOR_RETRIEVAL_INTENTS, []
        )

    def _response_selector_rankings(
        self,
        message: Message,
        response_selector_intent: str = RESPONSE_SELECTOR_DEFAULT_INTENT,
    ) -> List[Dict[Text, Any]]:
        return message.data[RESPONSE_SELECTOR][response_selector_intent][
            RESPONSE_SELECTOR_RANKING_KEY
        ]

    def _full_response_selector_intent_name(
        self,
        message: Message,
        response_selector_intent: str = RESPONSE_SELECTOR_DEFAULT_INTENT,
    ) -> str:
        return message.data[RESPONSE_SELECTOR][response_selector_intent][
            RESPONSE_SELECTOR_RANKING_KEY
        ][0]["intent_response_key"]
