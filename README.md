## What is this branch about?

(For 2.8.x, see 3.0_handle_repeated_out_of_scopes for a version using custom slot extraction logic)

Varies the responses for successive `out_of_scope` messages by using a custom action `action_check_successive_intent_repetitions`
to set the slot `successive_intent_repetitions`, and using conditional response variations to make the final response selection.

Try repeatedly entering either "Give me a human" (variations for first 3 entries) or "What is the meaning of life" (enter 6 times to see results).
