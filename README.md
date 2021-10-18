## What is this branch about?

This branch provides an example of using multi-intents. See the intents `greet+ask_how_are_you`, `mood_great+ask_how_are_you`, and the corresponding settings in the NLU pipeline.
There are intentionally no stories for the intent `mood_great+ask_how_are_you`. This means TEDPolicy will make a prediction on what should happen after this intent based on stories for the composing intents. 
