## What is this branch about?

This branch shows an example of an entity normalization component for numbers. It's intended only to show the required methods & base class for such a component, there's only naive normalization logic in there.

It normalizes the `number` entity to a floating point value instead of text (as long as the text is only digits, no validation is happening!).

After training with `rasa train nlu`, you should see this parse in `rasa shell nlu` if you enter a sequence of digits.

```
{
  "text": "124",
  "intent": {
    "id": -5539137410972909607,
    "name": "inform",
    "confidence": 0.9982847571372986
  },
  "entities": [
    {
      "entity": "number",
      "start": 0,
      "end": 3,
      "value": 124.0,
      "extractor": "RegexEntityExtractor",
      "processors": [
        "CustomEntityMapper"
      ]
    },
    {
      "entity": "number",
      "start": 0,
      "end": 3,
      "confidence_entity": 0.9988024234771729,
      "value": 124.0,
      "extractor": "DIETClassifier",
      "processors": [
        "CustomEntityMapper"
      ]
    }
  ],
  ...
}
```
