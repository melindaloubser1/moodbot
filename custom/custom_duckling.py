from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from typing import Dict, Text, Any, Optional

from rasa.nlu.config import RasaNLUModelConfig
from rasa.nlu.extractors.duckling_entity_extractor import DucklingEntityExtractor
from rasa.nlu.model import Metadata

logger = logging.getLogger(__name__)


class CustomDucklingExtractor(DucklingEntityExtractor):
    @classmethod
    def create(
        cls, component_config: Dict[Text, Any], config: RasaNLUModelConfig
    ) -> "CustomDucklingExtractor":

        return cls(component_config, config.language)

    @classmethod
    def load(cls,
             meta: Dict[Text, Any],
             model_dir: Text = None,
             model_metadata: Metadata = None,
             cached_component: Optional['CustomDucklingExtractor'] = None,
             **kwargs: Any
             ) -> 'CustomDucklingExtractor':

        return cls(meta, model_metadata.get("language"))

    @classmethod
    def load(
        cls,
        meta: Dict[Text, Any],
        model_dir: Text,
        model_metadata: Optional[Metadata] = None,
        cached_component: Optional["CustomDucklingExtractor"] = None,
        **kwargs: Any,
    ) -> "CustomDucklingExtractor":
        """Loads trained component (see parent class for full docstring)."""
        language = model_metadata.get("language") if model_metadata else None
        return cls(meta, language)
