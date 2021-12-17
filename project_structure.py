"""
This is a helper script to infer and enforce a prescriptive structure for your NLU data.
N.B. if using to infer a project structure, manually review the results!
There are a few details of how training data is loaded by Rasa that can have unexpected results.
E.g. synonyms in both the short (inline) and long formats have equal status in loaded training data.
This means a file can be found to contain a synonym when it has no explicit "synonym:" section.
"""
import asyncio

from collections import OrderedDict, defaultdict
import argparse
import logging
import os

from ruamel.yaml import StringIO

from rasa.shared.importers.rasa import RasaFileImporter
import rasa.shared.data
import rasa.shared.utils.io
from rasa.shared.nlu.training_data.training_data import TrainingData
from rasa.shared.nlu.training_data.formats.rasa_yaml import RasaYAMLWriter

logger = logging.getLogger(__file__)

DEFAULT_PROJECT_STRUCTURE_FILE = "./project_structure.yml"
DEFAULT_NLU_DATA_PATH = "./data/nlu"
DEFAULT_NLU_TARGET_FILE = "./data/nlu/nlu.yml"

class OrderedDefaultdict(OrderedDict):
    """ A defaultdict with OrderedDict as its base class. """

    def __init__(self, default_factory=None, *args, **kwargs):
        if not (default_factory is None or callable(default_factory)):
            raise TypeError('first argument must be callable or None')
        super(OrderedDefaultdict, self).__init__(*args, **kwargs)
        self.default_factory = default_factory  # called by __missing__()

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key,)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):  # Optional, for pickle support.
        args = (self.default_factory,) if self.default_factory else tuple()
        return self.__class__, args, None, None, iter(self.items())

    def __repr__(self):  # Optional.
        return '%s(%r, %r)' % (self.__class__.__name__, self.default_factory, self.items())



class SortableTrainingData(TrainingData):
    def get_intent_order(self):
        intent_order = list(
            dict.fromkeys([ex.data["intent"] for ex in self.training_examples])
        )
        return intent_order

    def sort_synonyms(self):
        self.entity_synonyms = OrderedDict(
            sorted(
                [(synonym, value) for synonym, value in self.entity_synonyms.items()],
                key=lambda x: (x[1], x[0]),
            )
        )

    def sort_lookup_values(self):
        self.lookup_tables = sorted(
            [
                {"name": lookup["name"], "elements": sorted(lookup["elements"])}
                for lookup in self.lookup_tables
            ],
            key=lambda x: x["name"],
        )

    def get_examples_per_intent(self, intent_list):
        examples_per_intent = {
            intent: [ex for ex in self.training_examples if ex.data["intent"] == intent]
            for intent in intent_list
        }
        return examples_per_intent

    def sort_intent_examples(self):
        intent_order = self.get_intent_order()
        examples_per_intent = self.get_examples_per_intent(intent_order)
        sorted_examples = [
            ex for intent in intent_order for ex in examples_per_intent.get(intent, [])
        ]
        self.training_examples = sorted_examples

    def sort_data(self):
        self.sort_synonyms()
        self.sort_lookup_values()
        self.sort_intent_examples()

    def get_all_keys_present(self):
        intents = set(self.get_intent_order())
        synonyms = set(self.entity_synonyms.values())
        regexes = set([reg.get("name") for reg in self.regex_features])
        lookups = set([lookup.get("name") for lookup in self.lookup_tables])
        return {
            "intents": intents,
            "synonyms": synonyms,
            "regexes": regexes,
            "lookups": lookups,
        }


class ProjectStructure:
    def __init__(
        self,
        nlu_data_path=DEFAULT_NLU_DATA_PATH,
        default_intent_file=DEFAULT_NLU_TARGET_FILE,
        default_synonym_file=DEFAULT_NLU_TARGET_FILE,
        default_regex_file=DEFAULT_NLU_TARGET_FILE,
        default_lookup_file=DEFAULT_NLU_TARGET_FILE,
    ):
        self.nlu_data_path = os.path.relpath(nlu_data_path)
        self.default_intent_file = os.path.relpath(default_intent_file)
        self.default_synonym_file = os.path.relpath(default_synonym_file)
        self.default_regex_file = os.path.relpath(default_regex_file)
        self.default_lookup_file = os.path.relpath(default_lookup_file)
        self.intents = ordered_dict_from_list([])
        self.synonyms = ordered_dict_from_list([])
        self.regexes = ordered_dict_from_list([])
        self.lookups = ordered_dict_from_list([])

    def update_project_structure(self, section="", keys=[], value=""):
        attrib_to_update = getattr(self, section)
        for key in keys:
            attrib_to_update[key] = value

    def update_project_structure_for_file(self, nlu_file):
        nlu_data = load_sortable_nlu_data(nlu_file)
        intents = nlu_data.get_intent_order()
        synonyms = sorted(set(nlu_data.entity_synonyms.values()))
        regexes = sorted(set([reg.get("name") for reg in nlu_data.regex_features]))
        lookups = sorted(set([lookup.get("name") for lookup in nlu_data.lookup_tables]))

        nlu_file_relative_path = os.path.relpath(nlu_file)

        self.update_project_structure("intents", intents, nlu_file_relative_path)
        self.update_project_structure("synonyms", synonyms, nlu_file_relative_path)
        self.update_project_structure("regexes", regexes, nlu_file_relative_path)
        self.update_project_structure("lookups", lookups, nlu_file_relative_path)

    def infer_structure_from_files(self):
        nlu_data = load_sortable_nlu_data(self.nlu_data_path)
        self.intents = ordered_dict_from_list(nlu_data.get_intent_order())
        self.synonyms = ordered_dict_from_list(
            sorted(set(nlu_data.entity_synonyms.values()))
        )
        self.regexes = ordered_dict_from_list(
            sorted(set([reg.get("name") for reg in nlu_data.regex_features]))
        )
        self.lookups = ordered_dict_from_list(
            sorted(set([lookup.get("name") for lookup in nlu_data.lookup_tables]))
        )

        nlu_files = rasa.shared.data.get_data_files(
            self.nlu_data_path, rasa.shared.data.is_nlu_file
        )
        for nlu_file in nlu_files:
            self.update_project_structure_for_file(nlu_file)

        self.group_sections_by_file_then_original_order()

    def group_section_by_file_then_original_order(self, section):
        section_to_update = getattr(self, section)
        current_order = {ix: intent for intent, ix in enumerate(section_to_update)}
        file_order = {
            ix: filename
            for filename, ix in enumerate(
                list(
                    dict.fromkeys([nlu_file for nlu_file in section_to_update.values()])
                )
            )
        }
        grouped_section = OrderedDict(
            sorted(
                section_to_update.items(),
                key=lambda x: (file_order.get(x[1]), current_order.get(x[0])),
            )
        )
        setattr(self, section, grouped_section)

    def group_sections_by_file_then_original_order(self):
        for section in ["intents", "synonyms", "regexes", "lookups"]:
            self.group_section_by_file_then_original_order(section)

    def as_dict(self):
        return OrderedDict(
            {
                "nlu_data_path": os.path.relpath(self.nlu_data_path),
                "default_target_files": {
                    "intents": os.path.relpath(self.default_intent_file),
                    "synonyms": os.path.relpath(self.default_synonym_file),
                    "regexes": os.path.relpath(self.default_regex_file),
                    "lookups": os.path.relpath(self.default_lookup_file),
                },
                "target_files": {
                    "intents": self.intents,
                    "synonyms": self.synonyms,
                    "regexes": self.regexes,
                    "lookups": self.lookups,
                },
            }
        )

    def as_inverted_dict(self):
        target_files = self.as_dict()["target_files"]
        filenames = set(
            [fname for section in target_files.values() for fname in section.values()]
        )
        keys_per_file = OrderedDefaultdict(lambda: OrderedDefaultdict(list)) #  {filename: OrderedDict() for filename in filenames}
        for filename in filenames:
            for section in target_files.keys():
                keys_per_file[filename][section] = [
                    key
                    for key, value in target_files[section].items()
                    if value == filename
                ]

        return keys_per_file

    def get_handled_keys(self):
        return {
            section: set(values.keys())
            for section, values in self.as_dict()["target_files"].items()
        }

    def from_dict(self, project_structure_dict):
        self.nlu_data_path = project_structure_dict["nlu_data_path"]
        self.default_intent_file = project_structure_dict["default_target_files"][
            "intents"
        ]
        self.default_synonym_file = project_structure_dict["default_target_files"][
            "synonyms"
        ]
        self.default_regex_file = project_structure_dict["default_target_files"][
            "regexes"
        ]
        self.default_lookup_file = project_structure_dict["default_target_files"][
            "lookups"
        ]
        self.intents = project_structure_dict["target_files"]["intents"]
        self.synonyms = project_structure_dict["target_files"]["synonyms"]
        self.regexes = project_structure_dict["target_files"]["regexes"]
        self.lookups = project_structure_dict["target_files"]["lookups"]

    def load_structure_from_file(self, input_file):
        loaded_structure = rasa.shared.utils.io.read_yaml_file(input_file)
        self.from_dict(loaded_structure)

    def as_yaml_string(self):
        stream = StringIO()
        rasa.shared.utils.io.write_yaml(self.as_dict(), stream, True)
        return stream.getvalue()

    def write_structure_to_file(self, output_file):
        rasa.shared.utils.io.write_yaml(self.as_dict(), output_file, True)

def load_sortable_nlu_data(nlu_data_path):
    nlu_files = rasa.shared.data.get_data_files([nlu_data_path], rasa.shared.data.is_nlu_file)
    training_data_importer = RasaFileImporter(training_data_paths=nlu_files)
    loop = asyncio.get_event_loop()
    nlu_data = loop.run_until_complete(training_data_importer.get_nlu_data())
    nlu_data.__class__ = SortableTrainingData
    return nlu_data

def ordered_dict_from_list(items):
    return OrderedDict({item: "" for item in items})


def get_training_data_for_keys(nlu_data, included_keys):
    training_data_for_keys = TrainingData()
    training_data_for_keys.training_examples = [
        ex
        for ex in nlu_data.training_examples
        if ex.data.get("intent") in included_keys["intents"]
    ]
    training_data_for_keys.entity_synonyms = OrderedDict(
        {
            syn_value: syn_name
            for syn_value, syn_name in nlu_data.entity_synonyms.items()
            if syn_name in included_keys["synonyms"]
        }
    )
    training_data_for_keys.regex_features = [
        reg
        for reg in nlu_data.regex_features
        if reg.get("name") in included_keys["regexes"]
    ]
    training_data_for_keys.lookup_tables = [
        lookup
        for lookup in nlu_data.lookup_tables
        if lookup.get("name") in included_keys["lookups"]
    ]
    return training_data_for_keys


def apply_project_structure(project_structure: ProjectStructure):
    nlu_data = load_sortable_nlu_data(project_structure.nlu_data_path)
    all_keys_in_data = nlu_data.get_all_keys_present()
    all_keys_in_project_structure = project_structure.get_handled_keys()
    new_keys = {
        key: all_keys_in_data[key] - all_keys_in_project_structure[key]
        for key in all_keys_in_data.keys()
    }

    target_keys_per_file = project_structure.as_inverted_dict()

    for section, filename in project_structure.as_dict()[
        "default_target_files"
    ].items():
        target_keys_per_file[filename][section].extend(new_keys[section])

    existing_nlu_files = set(rasa.shared.data.get_data_files(project_structure.nlu_data_path, rasa.shared.data.is_nlu_file))
    existing_and_new_nlu_files = existing_nlu_files.union(set(target_keys_per_file.keys()))

    writer = RasaYAMLWriter()
    for filename in existing_and_new_nlu_files:
        target_keys =  target_keys_per_file.get(filename, [])
        if not target_keys and filename in existing_nlu_files:
            logger.warning(f"No data found for file {filename}; deleting {filename}")
            os.remove(filename)
            continue
        contents_per_file = get_training_data_for_keys(
            nlu_data, target_keys
        )
        logger.warning(f"Writing data to file {filename}")
        writer.dump(filename, contents_per_file)


def log_inference_warning(
    nlu_data_path,
    project_structure_file,
):
    logger.warning(
        "\n"
        f"WARNING: Inferring project structure from {nlu_data_path}"
        "\nThis is just a helper script to bootstrap your project structure."
        "\nIf an intent/synonym/etc. is found in multiple files, the last file it appears in will be taken as the target file.\n"
        f"Manually review the the output in {project_structure_file} to make sure the structure is what you want in the future."
        "\n"
    )


def infer_project_structure(
    nlu_data_path, project_structure_file, default_nlu_target_file
):
    log_inference_warning(nlu_data_path, project_structure_file)
    project_structure = ProjectStructure(
        nlu_data_path,
        default_nlu_target_file,
        default_nlu_target_file,
        default_nlu_target_file,
        default_nlu_target_file,
    )
    project_structure.infer_structure_from_files()
    project_structure.write_structure_to_file(project_structure_file)


def log_enforcement_info(project_structure_file, nlu_data_path):
    logger.warning(
        "\n"
        f"Enforcing project structure from {project_structure_file} on data in {nlu_data_path}"
    )

    logger.warning(
        "\n"
        f"Note that synonyms, regexes & lookups will be sorted alphabetically."
        "\nTherefore you may see a large diff the first time you run this command.\n"
    )


def enforce_project_structure(project_structure_file):
    project_structure = ProjectStructure()
    project_structure.load_structure_from_file(project_structure_file)
    log_enforcement_info(project_structure_file, project_structure.nlu_data_path)
    apply_project_structure(project_structure)


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect data for scorecard.")
    parser.add_argument(
        "-infer",
        action="store_true",
        help=("Infer project structure from project directory."),
    )

    parser.add_argument(
        "-enforce",
        action="store_true",
        help=(
            "Enforce project structure from project structure file onto project directory"
        ),
    )

    parser.add_argument(
        "--project_structure_file",
        help=("YAML file where project structure will be read from and written to."),
        default=DEFAULT_PROJECT_STRUCTURE_FILE,
    )
    parser.add_argument(
        "--nlu_data_path",
        help=(
            "Path to NLU data directory. Only used with -infer, -enforce determines directory from project structure file."
        ),
        default=DEFAULT_NLU_DATA_PATH,
    )
    parser.add_argument(
        "--default_nlu_target_file",
        help=(
            "Default target file for items that don't already have a target file."
            " Only used with '-infer', '-enforce' uses the defaults from the project structure file."
        ),
        default=DEFAULT_NLU_TARGET_FILE,
    )

    return parser


if __name__ == "__main__":
    parser = _create_argument_parser()
    args = parser.parse_args()
    infer = args.infer
    enforce = args.enforce
    nlu_data_path = args.nlu_data_path
    project_structure_file = args.project_structure_file
    default_nlu_target_file = args.default_nlu_target_file

    if not (infer or enforce):
        parser.error("You must specify either '-infer' or '-enforce'")

    if infer:
        infer_project_structure(
            nlu_data_path, project_structure_file, default_nlu_target_file
        )

    if enforce:
        enforce_project_structure(project_structure_file)
