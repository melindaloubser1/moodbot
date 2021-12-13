## What is this branch about?

This branch contains a basic example of running a separate NLU server.

Do the following:

1. Train models
```
rasa train nlu --fixed-model-name nlu
rasa train core --fixed-model-name core
```

2. Start servers
```
rasa run --model models/nlu.tar.gz --enable-api --port 5003 --endpoints endpoints_nlu_server.yml --debug
```
Separate terminal:
```
rasa shell --model models/core.tar.gz
```
