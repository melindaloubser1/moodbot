from typing import Dict, List, Text
from pytablewriter import MarkdownTableWriter
import json

class CrossValResult:
    def __init__(self, results_dir):
        self.directory = results_dir
        self.intent_report = self.load_intent_report()
        self.entity_report = self.load_entity_report()
        self.response_selection_report = self.load_response_selection_report()

    @staticmethod
    def load_report(filepath) -> Dict:
        try:
            with open(filepath, "r") as f:
                data = json.loads(f.read())
        except FileNotFoundError:
            return {}
        return data

    def load_intent_report(self) -> Dict:
        return self.load_report(f"{self.directory}/intent_report.json")

    def load_entity_report(self) -> Dict:
        return self.load_report(f"{self.directory}/DIETClassifier_report.json")

    def load_response_selection_report(self) -> Dict:
        return self.load_report(f"{self.directory}/response_selection_report.json")

    def intent_table(self) -> Text:
        def format_cell(data, c, k):
            if not data[c].get(k):
                return "N/A"
            if k == "f1-score":
                return f"{data[c][k]:.3f}"
            if k == "confused_with":
                return ", ".join([f"{k}({v})" for k, v in data[c][k].items()])
            else:
                return data[c][k]

        writer = MarkdownTableWriter()
        writer.table_name = "Intent Cross-Validation Results"

        cols = ["support", "f1-score", "confused_with"]
        writer.headers = ["class"] + cols

        classes = list(self.intent_report.keys())
        try:
            classes.remove("accuracy")
        except:
            pass
        classes.sort(key=lambda x: self.intent_report[x]["support"], reverse=True)
        writer.value_matrix = [
            [c] + [format_cell(self.intent_report, c, k) for k in cols] for c in classes
        ]

        return writer.dumps()

    def entity_table(self) -> Text:
        def format_cell(data, c, k):
            if not data[c].get(k):
                return "N/A"
            else:
                return data[c][k]

        writer = MarkdownTableWriter()
        writer.table_name = "Entity Cross-Validation Results"

        cols = ["support", "f1-score", "precision", "recall"]
        writer.headers = ["entity"] + cols

        classes = list(self.entity_report.keys())
        classes.sort(key=lambda x: self.entity_report[x]["support"], reverse=True)

        writer.value_matrix = [
            [c] + [format_cell(self.entity_report, c, k) for k in cols] for c in classes
        ]

        return writer.dumps()

    @classmethod
    def remove_excluded_classes(classes):
        for excluded_class in ["accuracy", "weighted avg", "macro avg"]:
            try:
                classes.remove(excluded_class)
            except:
                pass
        return classes

    @property
    def intents(self) -> List:
        intents = list(self.intent_report.keys())
        return self.remove_excluded_classes(intents)

    @property
    def entities(self) -> List:
        entities = list(self.entity_report.keys())
        return self.remove_excluded_classes(entities)

    @property
    def retrieval_intents(self) -> List:
        retrieval_intents = list(self.response_selection_report.keys())
        return self.remove_excluded_classes(retrieval_intents)


class CrossValResultComparison:
    def __init_(self, base_report: CrossValResult, reports_to_compare: List[CrossValResult]):
        self.base_report = base_report
        self.reports_to_compare = reports_to_compare
        self.all_intents = self.collect_intents()
        self.all_entities = self.collect_entities()

    def collect_intents(self):
        base_intents = set(self.base_report.intents)
        other_report_intents = set([intent for report in self.reports_to_compare for intent in report.intents])
        return base_intents + other_report_intents

    def collect_entities(self):
        base_entities = set(self.base_report.entities)
        other_report_entities = set([entity for report in self.reports_to_compare for entity in report.entities])
        return base_entities + other_report_entities




def compare_crossval_reports(base_report: CrossValResult, reports_to_compare: List[CrossValResult]):
    
    pass


cross_val_results = CrossValResult("results")
intents = cross_val_results.intent_table()
entities = cross_val_results.entity_table()

with open("results.md", "w") as f:
    f.write(intents)
    f.write("\n\n\n")
    f.write(entities)
