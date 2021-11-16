from typing import Dict, Text, Any, List, Optional, Type

from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.recipes.default_recipe import DefaultV1Recipe
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.constants import ENTITIES
from rasa.nlu.extractors.extractor import EntityExtractorMixin

@DefaultV1Recipe.register(
    [DefaultV1Recipe.ComponentType.ENTITY_EXTRACTOR], is_trainable=False
)
class CustomEntityMapper(GraphComponent, EntityExtractorMixin):
    @classmethod
    def required_components(cls) -> List[Type]:
        return [EntityExtractorMixin]

    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> GraphComponent:

        return cls(config, execution_context.node_name)


    def normalize_number_from_text(
        self, number_text: Optional[Text]
    ) -> float:
        """This is where actual normalization logic would go
        This is a completely naive example assuming the number was given in the right format
        """
        number = float(number_text)
        return number

    def replace_normalized_numbers(self, entities: List[Dict[Text, Any]]) -> None:
        """This is where you could chooose entities to normalize
        You could also have a `load` method that allows specifying entities to normalize in the config (like duckling dimensions)
        """
        for entity in entities:
            if entity["entity"] == "number":
                entity_value = str(entity["value"])
                entity["value"] = self.normalize_number_from_text(entity_value)
                self.add_processor_name(entity)

    def process(self, messages: List[Message]) -> List[Message]:
        for message in messages:
            updated_entities = message.get(ENTITIES, [])[:]
            self.replace_normalized_numbers(updated_entities)
            message.set(ENTITIES, updated_entities, add_to_output=True)
        return messages
