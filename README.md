## What is this branch about?

(For 2.8.x, see 3.0_handle_repeated_out_of_scopes for a version using custom slot extraction logic)

Handles successive `out_of_scope` with varying responses using a regular custom action that checks
the tracker for how many of the same retrieval intent occurred in a row.
