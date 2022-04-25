## What is this branch about?

This branch is an example Rasa 3.x bot that includes a rule which runs two forms consecutively, without a user message after the submission of the first form. The second form includes slots that the last message provided to the first form would usually set. A custom validation method ensures the second form rejects the slot value set by the last user message of the previous form and reprompts for it. 
