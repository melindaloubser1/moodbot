import asyncio
from rasa.core.training import load_data
from rasa.shared.core.domain import Domain


DOMAIN_PATH = "domain.yml"
DATA_PATH = "data/stories"
AUGMENTATION_FACTOR = 0
OUTPUT_PATH = "flattened_stories.yml"

domain = Domain.load(DOMAIN_PATH)

loop = asyncio.get_event_loop()
trackers = loop.run_until_complete(load_data(DATA_PATH, domain, augmentation_factor=AUGMENTATION_FACTOR))

for tracker in trackers:
    tracker.export_stories_to_file(OUTPUT_PATH)
