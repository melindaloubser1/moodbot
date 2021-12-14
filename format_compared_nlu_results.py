import os
from typing import Dict, List, Text
import logging
from pytablewriter import MarkdownTableWriter
import json

logger = logging.getLogger(__file__)

class RasaNLUTestResult:
    intent_report_attribute = "intents"
    entity_report_attribute = "entities"
    response_selection_report_attribute = "retrieval_intents"
    intent_report_filename = "intent_report.json"
    entity_report_filename = "DIETClassifier_report.json"
    response_selection_report_filename = "response_selection_report.json"

    def __init__(self, results_dir, name=None):
        self.directory = results_dir
        self.name = name or results_dir
        self.intent_report = self.load_report(self.intent_report_filename)
        self.entity_report = self.load_report(self.entity_report_filename)
        self.response_selection_report = self.load_report(self.response_selection_report_filename)

    def load_report(self, filename) -> Dict:
        filepath = os.path.join(self.directory, filename)
        try:
            with open(filepath, "r") as f:
                data = json.loads(f.read())
        except FileNotFoundError:
            return {}
        return data

    @classmethod
    def remove_excluded_classes(cls, classes):
        for excluded_class in ["accuracy"]:
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

    @classmethod
    def format_report_cell(cls, data, label, metric):
        if not data[label].get(metric):
            return "N/A"
        if any([float_metric in metric for float_metric in ["f1-score", "precision", "recall"]]):
            return f"{data[label][metric]:.3f}"
        if "confused_with" in metric:
            return ", ".join([f"{label_confused_with}({num_times_confused})" for label_confused_with, num_times_confused in data[label][metric].items()])
        else:
            return data[label][metric]

    def create_table(self, name, report_type, metrics = ["support", "f1-score"], sort_by = "support"):
        report = getattr(self, report_type)
        attribute = getattr(self, f"{report_type}_attribute")

        writer = MarkdownTableWriter()
        writer.table_name = name
        writer.headers = [attribute] + metrics

        labels = getattr(self, attribute)
        labels.sort(key=lambda x: report[x][sort_by], reverse=True)
        writer.value_matrix = [
            [label] + [self.__class__.format_report_cell(report, label, metric) for metric in metrics] for label in labels
        ]

        return writer.dumps()

    def intent_table(self, name = "Intent Evaluation Report", metrics = ["support", "f1-score", "confused_with"], sort_by = "support") -> Text:
        return self.create_table(name, "intent_report", metrics, sort_by)

    def entity_table(self, name = "Entity Evaluation Report", metrics = ["support", "f1-score", "precision", "recall"], sort_by = "support") -> Text:
        return self.create_table(name, "entity_report", metrics, sort_by)

    def response_selection_table(self, name = "Response Selection Report", metrics = ["support", "f1-score", "confused_with"], sort_by = "support") -> Text:
        return self.create_table(name, "response_selection_report", metrics, sort_by)



class RasaNLUTestResultComparison(RasaNLUTestResult):
    def __init__(self, reports_to_compare: List[RasaNLUTestResult]):
        self.reports_to_compare = reports_to_compare

    def collect_attribute(self, attribute):
        attrib = set([item for report in self.reports_to_compare for item in getattr(report, attribute)])
        return list(attrib)

    def combine_reports(self, report_type) -> Dict:
        attribute = getattr(self, f"{report_type}_attribute")
        reports = {item:{} for item in getattr(self, attribute)}
        for attrib in getattr(self, attribute):
            for report in self.reports_to_compare:
                reports[attrib][report.name] = getattr(report, report_type).get(attrib, {})
        return reports

    @property
    def directories(self) -> List:
        return [report.directory for report in self.reports_to_compare]

    @property
    def names(self) -> List:
        return [report.name for report in self.reports_to_compare]

    @property
    def intents(self) -> List:
        return self.collect_attribute("intents")

    @property
    def entities(self) -> List:
        return self.collect_attribute("entities")

    @property
    def retrieval_intents(self) -> List:
        return self.collect_attribute("retrieval_intents")

    @property
    def intent_report(self) -> Dict:
        return self.combine_reports("intent_report")

    @property
    def entity_report(self) -> Dict:
        return self.combine_reports("entity_report")

    @property
    def response_selection_report(self) -> Dict:
        return self.combine_reports("response_selection_report")

    @classmethod
    def format_report_cell(cls, data, label, report_name, metric):
        if not data[label][report_name].get(metric):
            return "N/A"
        if any([float_metric in metric for float_metric in ["f1-score", "precision", "recall"]]):
            return f"{data[label][report_name][metric]:.3f}"
        if "confused_with" in metric:
            return ", ".join([f"{label_confused_with}({num_times_confused})" for label_confused_with, num_times_confused in data[label][report_name][metric].items()])
        else:
            return data[label][report_name][metric]

    def create_table(self, name, report_type, metrics = ["support", "f1-score"], sort_by = "support"):
        report = getattr(self, report_type)
        first_report = getattr(self.reports_to_compare[0], report_type)
        attribute = getattr(self, f"{report_type}_attribute")

        writer = MarkdownTableWriter()
        writer.table_name = name

        columns = [f"{metric} ({name})" for metric in metrics for name in self.names]
        writer.headers = [attribute] + columns

        labels = getattr(self, attribute)
        labels.sort(key=lambda x: first_report.get(x,{}).get(sort_by, 0), reverse=True)
        writer.value_matrix = [
            [label] + [self.__class__.format_report_cell(report, label, report_name, metric) for metric in metrics for report_name in self.names] for label in labels
        ]

        return writer.dumps()


base_results = RasaNLUTestResult("results/1", "Incoming")
other_results = RasaNLUTestResult("results/2", "Stable")
results_comparison = RasaNLUTestResultComparison([base_results, other_results])

intent_table = results_comparison.intent_table("Intent Results Comparison")
entity_table = results_comparison.entity_table("Entity Results Comparison")
response_selection_table = results_comparison.response_selection_table("Response Selection Results Comparison")

with open("results.md", "w+") as f:
    f.write(intent_table)
    f.write("\n\n\n")
    f.write(entity_table)
    f.write("\n\n\n")
    f.write(response_selection_table)
