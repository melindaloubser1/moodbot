import logging
from typing import Any, Dict, List, Optional, Text, Type

from rasa.nlu.components import Component
from rasa.shared.nlu.constants import ENTITIES
from rasa.nlu.extractors.extractor import EntityExtractor
from rasa.shared.nlu.training_data.message import Message

logger = logging.getLogger(__name__)

class CustomEntityMapper(EntityExtractor):
    @classmethod
    def required_components(cls) -> List[Type[Component]]:
        return [EntityExtractor]

    def process(self, message: Message, **kwargs: Any) -> None:
        updated_entities = message.get(ENTITIES, [])[:]
        self.replace_normalized_numbers(updated_entities)
        message.set(ENTITIES, updated_entities, add_to_output=True)

    def replace_normalized_numbers(self, entities: List[Dict[Text, Any]]) -> None:
        """This is where you could chooose entities to normalize
        You could also have a `load` method that allows specifying entities to normalize in the config (like duckling dimensions)
        """
        for entity in entities:
            if entity["entity"] == "number":
                entity_value = str(entity["value"])
                entity["value"] = self.normalize_number_from_text(entity_value)
                self.add_processor_name(entity)

    def normalize_number_from_text(
        self, number_text: Optional[Text]
    ) -> float:
        """This is where actual normalization logic would go
        This is a completely naive example assuming the number was given in the right format
        """
        number = float(number_text)
        return number

