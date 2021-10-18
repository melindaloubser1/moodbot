## What is this branch about?

`forced_followup_action_featurization` contains an example of a forced follow up action. It is intended to show the effect of using a forced followup action when not reverting the action immediately (as happens in two stage fallback, for example).


In this example, the action `utter_forced_followup` does not appear in any stories or rules. There's only this story:
```
- story: force followup then greet
  steps:
  - intent: followup
  - action: action_force_followup # This action forces `utter_forced_followup`
  - action: utter_greet
```

To test the effect of a forced followup action, train a model, start `rasa shell --debug --enable-api` and `rasa run actions` in a separate shell, and enter `/followup` at the shell prompt (there's no training data for this intent).

You should see a log like the one below. Notice that:
* `utter_forced_followup` becomes part of the tracker state
* Therefore `utter_greet` cannot be predicted by MemoizationPolicy - there is no matching set of states in any memorized story
* The final `action_listen` is predicted by TEDPolicy instead

See [here](https://github.com/RasaHQ/rasa/blob/1441d29702e8e112f90e560981c5556261555231/rasa/core/featurizers/single_state_featurizer.py#L258-L263) to further inspect the featurization of the state added by the forced follow up action; also see the script `inspect_model.py` for a very rough starting point to look inside a model's featurizers.

```
Bot loaded. Type a message and press enter (use '/stop' to exit): 
Your input ->  /followup
...
rasa.core.processor  - Received user message '/followup' with intent '{'name': 'followup', 'confidence': 1.0}' and entities '[]'
rasa.core.processor  - Logged UserUtterance - tracker now has 4 events.
rasa.core.policies.memoization  - Current tracker state:
[state 1] user intent: followup | previous action name: action_listen
rasa.core.policies.memoization  - There is a memorised next action 'action_force_followup'
rasa.core.policies.rule_policy  - Current tracker state:
[state 1] user text: /followup | previous action name: action_listen
rasa.core.policies.rule_policy  - There is no applicable rule.
rasa.core.policies.rule_policy  - Current tracker state:
[state 1] user intent: followup | previous action name: action_listen
rasa.core.policies.rule_policy  - There is no applicable rule.

rasa.core.policies.ted_policy  - TED predicted 'action_force_followup' based on user intent.
rasa.core.policies.ensemble  - Made prediction using user intent.
rasa.core.policies.ensemble  - Added `DefinePrevUserUtteredFeaturization(False)` event.
rasa.core.policies.ensemble  - Predicted next action using policy_0_MemoizationPolicy.
rasa.core.processor  - Predicted next action 'action_force_followup' with confidence 1.00.
rasa.core.actions.action  - Calling action endpoint to run action 'action_force_followup'.
rasa.core.processor  - Policy prediction ended with events '[<rasa.shared.core.events.DefinePrevUserUtteredFeaturization object at 0x162fe0070>]'.
rasa.core.processor  - Action 'action_force_followup' ended with events '[<rasa.shared.core.events.FollowupAction object at 0x162fed040>]'.
rasa.core.processor  - Current slot values: 
        session_started_metadata: None
rasa.core.processor  - Predicted next action 'utter_forced_followup' with confidence 1.00.
rasa.core.processor  - Policy prediction ended with events '[]'.
rasa.core.processor  - Action 'utter_forced_followup' ended with events '[BotUttered('I'm a force follow up action!', {"elements": null, "quick_replies": null, "buttons": null, "attachment": null, "image": null, "custom": null}, {"utter_action": "utter_forced_followup"}, 1634561917.1866848)]'.
rasa.core.policies.memoization  - Current tracker state:
[state 1] user intent: followup | previous action name: action_listen
[state 2] user intent: followup | previous action name: action_force_followup
[state 3] user intent: followup | previous action name: utter_forced_followup
rasa.core.policies.memoization  - There is no memorised next action
rasa.core.policies.rule_policy  - Current tracker state:
[state 1] user intent: followup | previous action name: action_listen
[state 2] user intent: followup | previous action name: action_force_followup
[state 3] user intent: followup | previous action name: utter_forced_followup
rasa.core.policies.rule_policy  - There is no applicable rule.

rasa.core.policies.ted_policy  - TED predicted 'action_listen' based on user intent.
rasa.core.policies.ensemble  - Predicted next action using policy_3_TEDPolicy.
rasa.core.processor  - Predicted next action 'action_listen' with confidence 0.86.
rasa.core.processor  - Policy prediction ended with events '[]'.
rasa.core.processor  - Action 'action_listen' ended with events '[]'.
rasa.core.lock_store  - Deleted lock for conversation 'fecf4707a8184ad39e5c89f45ea2bd8b'.
...
I'm a force follow up action!
```
