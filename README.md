## What is this branch about?

A demo of how to use `ignored_intents` + a custom validation action to allow some buttons from earlier in the conversation to **completely exit** out of a form.

## To run the scenario
1. train a model with `rasa train` (should take a minute)
1. start `rasa shell`
2. type `start` to get a list of buttons. These are there for reference.
3. you'll be asked to click the `/intro` button to start a form. click it or type "/intro"
4. answer a question or interrupt the form to test the scenario
   1. send one of the payloads `deeplink_tiger` or `deeplink_panda` to simulate clicking a preexisting button


## What should happen?


The form will be silently exited when an ignored intent is received. 
```
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
Your input ->  Ms # Form has been exited, therefore there is not the expected response
Your input -> goodbye
Bye
```


This is the behaviour with **only ignored intents without adding the force-quit behaviour with a custom action**:
```
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




This is the default behaviour when there are **no `ignored_intents`** for the `intro_form` - it assumes the button payload is part of the form input:

```
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
