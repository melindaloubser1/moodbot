import asyncio
import logging
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

from rasa.core.agent import Agent
from rasa.core.channels.channel import UserMessage
from rasa.utils.endpoints import EndpointConfig

MODEL_PATH = "models/core-20211018-155223.tar.gz"
ACTION_SERVER_ENDPOINT_URL = "http://localhost:5055"

## Inspect by sending message and then inspecting tracker
INPUT_MESSAGE = "/followup"
SENDER_ID = "default"
message = UserMessage(INPUT_MESSAGE, sender_id=SENDER_ID) 

action_server_endpoint = EndpointConfig(ACTION_SERVER_ENDPOINT_URL)
agent = Agent.load(MODEL_PATH, action_endpoint=action_server_endpoint)

loop = asyncio.get_event_loop()
bot_response = loop.run_until_complete(agent.handle_message(message))
# for some reason this was not hitting the action server so `utter_forced_followup` never shows up #TODO
tracker = agent.tracker_store.retrieve(SENDER_ID)

## Inspect by directly fetching featurization
all_actions = agent.domain.action_names_or_texts
# the feature vector for each action should be this big
print(len(all_actions)) 

ted_policy = agent.policy_ensemble.policies[2]
ted_state_featurizer = ted_policy._Policy__featurizer.state_featurizer
featurized_actions = ted_state_featurizer.encode_all_labels(agent.domain, agent.interpreter)
single_featurized_action = featurized_actions[0]["action_name"][0].features
# the feature vector for each action is a one-hot encoding over all actions
print(len(single_featurized_action[0]))
