## What is this branch about?

A demo of how to use `ignored_intents` to allow some buttons from earlier in the conversation to take priority over forms.

## To run the scenario
1. start `rasa shell`
2. type `start` to get a list of buttons
3. click the `/intro` button to start a form
4. answer a question or interrupt the form:
   1. to simulate re-clicking an existing button higher up in the convo, send one of the payloads `deeplink_tiger` or `deeplink_panda`.
   

## What should happen?

The form will allow the rule for the deeplink button to take precedence for a turn, then it will immediately reprompt for the slot it was trying to fill e.g.:

```
Bot loaded. Type a message and press enter (use '/stop' to exit): 
Your input ->  start                                                                                                                             
Buttons:
1: tiger (/deeplink_tiger)
2: panda (/deeplink_panda)
These buttons are left in the conversation for later use
? Please click the button below to continue 1: Do intro form (/intro)                                                                            
What is your name?
Your input ->  Melinda                                                                                                                           
What is your title?
Your input ->  /deeplink_tiger                                                                                                                   
A tiger!
Image: https://i.imgur.com/nGF1K8f.jpg
What is your title?
Your input ->  Ms                                                                                                                                
Hey! How are you Ms Melinda?
```




When there are **no `ignored_intents`** for the `intro_form`, this would happen - this is the default form behaviour to compare with:

```
Bot loaded. Type a message and press enter (use '/stop' to exit): 
Your input ->  start                                                                                                                             
Buttons:
1: tiger (/deeplink_tiger)
2: panda (/deeplink_panda)
These buttons are left in the conversation for later use
? Please click the button below to continue 1: Do intro form (/intro)
Your input ->  /intro
What is your name?
Your input ->  Melinda
What is your title?
Your input ->  /deeplink_tiger
Hey! How are you /deeplink_tiger Melinda?
```
