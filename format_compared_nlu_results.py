import os
from typing import Dict, List, Text, Optional
from collections import defaultdict
import logging
from pytablewriter import MarkdownTableWriter
import json

logger = logging.getLogger(__file__)

INTENT_REPORT_NAME = "intent_report"
ENTITY_REPORT_NAME = "entity_report"
RESPONSE_SELECTION_REPORT_NAME = "response_selection_report"


class RasaNLUTestResult:
    intent_report_label_type = "intents"
    entity_report_label_type = "entities"
    response_selection_report_label_type = "retrieval_intents"
    intent_report_filename = "intent_report.json"
    entity_report_filename = "DIETClassifier_report.json"
    response_selection_report_filename = "response_selection_report.json"

    def __init__(self, results_dir=None, name=None):
        self.results_directory = results_dir
        self.name = name or results_dir
        self.intent_report = {}
        self.entity_report = {}
        self.response_selection_report = {}

    def load_from_results_dir(self):
        self.intent_report = self.load_report(self.intent_report_filename)
        self.entity_report = self.load_report(self.entity_report_filename)
        self.response_selection_report = self.load_report(
            self.response_selection_report_filename
        )

    def load_report(self, filename) -> Dict:
        filepath = os.path.join(self.results_directory, filename)
        try:
            with open(filepath, "r") as f:
                data = json.loads(f.read())
        except FileNotFoundError:
            return {}
        return data

    @classmethod
    def label_type_for_report(cls, report_type):
        return getattr(cls, f"{report_type}_label_type")

    @classmethod
    def remove_excluded_classes(cls, classes):
        for excluded_class in ["accuracy"]:
            try:
                classes.remove(excluded_class)
            except:
                pass
        return classes

    def intents(self) -> List:
        intents = list(self.intent_report.keys())
        return self.remove_excluded_classes(intents)

    def entities(self) -> List:
        entities = list(self.entity_report.keys())
        return self.remove_excluded_classes(entities)

    def retrieval_intents(self) -> List:
        retrieval_intents = list(self.response_selection_report.keys())
        return self.remove_excluded_classes(retrieval_intents)

    @classmethod
    def format_report_cell(cls, metric, value):
        if not value:
            return "N/A"
        if metric in ["f1-score", "precision", "recall"]:
            try:
                formatted = f"{float(value):.3f}"
                return formatted
            except ValueError:
                return value
        if metric.startswith("confused_with"):
            return ", ".join(
                [
                    f"{label_confused_with}({num_times_confused})"
                    for label_confused_with, num_times_confused in value.items()
                ]
            )
        else:
            return value

    def create_table(
        self, name, report_type, metrics=["support", "f1-score"], sort_by="support"
    ):
        report = getattr(self, report_type)()
        label_type = self.label_type_for_report(report_type)

        writer = MarkdownTableWriter()
        writer.table_name = name
        writer.headers = [label_type] + metrics

        labels = getattr(self, label_type)()
        labels.sort(key=lambda x: report[x][sort_by], reverse=True)
        writer.value_matrix = [
            [label]
            + [
                self.format_report_cell(metric, report[label].get(metric))
                for metric in metrics
            ]
            for label in labels
        ]

        return writer.dumps()

    def intent_table(
        self,
        name="Intent Evaluation Report",
        metrics=["support", "f1-score", "confused_with"],
        sort_by="support",
    ) -> Text:
        return self.create_table(name, INTENT_REPORT_NAME, metrics, sort_by)

    def entity_table(
        self,
        name="Entity Evaluation Report",
        metrics=["support", "f1-score", "precision", "recall"],
        sort_by="support",
    ) -> Text:
        return self.create_table(name, ENTITY_REPORT_NAME, metrics, sort_by)

    def response_selection_table(
        self,
        name="Response Selection Report",
        metrics=["support", "f1-score", "confused_with"],
        sort_by="support",
    ) -> Text:
        return self.create_table(name, RESPONSE_SELECTION_REPORT_NAME, metrics, sort_by)


class CombinedRasaNLUTestResults(RasaNLUTestResult):
    def __init__(self, results_to_combine: List[RasaNLUTestResult]):
        self.results = results_to_combine

    def collect_labels(self, label_type):
        labels = set(
            [item for report in self.results for item in getattr(report, label_type)()]
        )
        return list(labels)

    def combine_reports(self, report_type) -> Dict:
        label_type = self.label_type_for_report(report_type)
        reports = {item: {} for item in getattr(self, label_type)()}
        for attrib in getattr(self, label_type)():
            for report in self.results:
                reports[attrib][report.name] = getattr(report, report_type).get(
                    attrib, {}
                )
        return reports

    def results_directories(self) -> List:
        return [report.results_directory for report in self.results]

    def result_sets_names(self) -> List:
        return [report.name for report in self.results]

    def intents(self) -> List:
        return self.collect_labels("intents")

    def entities(self) -> List:
        return self.collect_labels("entities")

    def retrieval_intents(self) -> List:
        return self.collect_labels("retrieval_intents")

    def intent_report(self) -> Dict:
        return self.combine_reports(INTENT_REPORT_NAME)

    def entity_report(self) -> Dict:
        return self.combine_reports(ENTITY_REPORT_NAME)

    def response_selection_report(self) -> Dict:
        return self.combine_reports(RESPONSE_SELECTION_REPORT_NAME)

    def combined_reports(self) -> Dict:
        combined_reports = {
            "result_sets_combined": self.result_sets_names(),
            "combined_intent_report": self.intent_report(),
            "combined_entity_report": self.entity_report(),
            "combined_response_selection_report": self.response_selection_report(),
        }
        return combined_reports

    @classmethod
    def format_report_cell(cls, metric, value):
        if not value:
            formatted = "N/A"
        elif any(
            [
                float_metric in metric
                for float_metric in ["f1-score", "precision", "recall"]
            ]
        ):
            try:
                formatted = f"{float(value):.3f}"
                if "Change" in metric and float(value) > 0:
                    formatted = "+" + formatted
                    logger.error(formatted)
            except ValueError:
                formatted = value
        
        elif "confused_with" in metric:
            formatted = ", ".join(
                [
                    f"{label_confused_with}({num_times_confused})"
                    for label_confused_with, num_times_confused in value.items()
                ]
            )
        else:
            formatted = value
        return formatted

    @classmethod
    def difference_column_name(cls, base_report_name, other_report_name, metric):
        return f"Change in {metric} ({other_report_name} - {base_report_name})"

    @classmethod
    def difference_between_reports(
        cls, report, base_report_name, other_report_name, label, metric
    ):
        base_report_metric = report.get(label, {}).get(base_report_name, {}).get(metric)
        other_report_metric = (
            report.get(label, {}).get(other_report_name, {}).get(metric)
        )
        try:
            difference = other_report_metric - base_report_metric
        except TypeError:
            if not base_report_metric and not other_report_metric:
                difference = f"Label not present in either report"
            else:
                report_present = (
                    other_report_name if other_report_metric else base_report_name
                )
                difference = f"Label only present in {report_present}"
        return difference

    # def get_comparison_for_metric(self, report_type, metric):
    #     label_type = self.label_type_for_report(report_type)
    #     report = getattr(self, report_type)()
    #     base_report = self.results[0]
    #     labels = getattr(self, label_type)()
    #     differences = {
    #         self.difference_column_name(base_report.name, other_report.name, metric): {
    #             label: self.difference_between_reports(
    #                 report, base_report.name, other_report.name, label, metric
    #             )
    #             for label in labels
    #         }
    #         for other_report in self.results[1:]
    #     }

    #     return differences

    def get_columns(self, metrics, include_difference_columns=True):
        base_report_name = self.result_sets_names()[0]
        columns = []
        for metric in metrics:
            for ix, name in enumerate(self.result_sets_names()):
                columns.append(f"{metric} ({name})")
                if include_difference_columns and ix > 0 and metric != "confused_with":
                    columns.append(
                        self.difference_column_name(base_report_name, name, metric)
                    )
        return columns

    def get_row_values(self, report, label, metrics, include_difference_columns):
        base_report_name = self.result_sets_names()[0]
        row_values = []
        for metric in metrics:
            for ix, name in enumerate(self.result_sets_names()):
                row_values.append(self.format_report_cell(metric, report[label][name].get(metric)))
                if include_difference_columns and ix > 0 and metric != "confused_with":
                    row_values.append(
                        self.format_report_cell(self.difference_column_name(base_report_name, name, metric), self.difference_between_reports(
                            report, base_report_name, name, label, metric
                        ))
                    )
        return row_values

    def create_table(
        self,
        name,
        report_type,
        metrics=["support", "f1-score"],
        sort_by="support",
        include_difference_columns=True,
    ):
        report = getattr(self, report_type)()
        first_report = getattr(self.results[0], report_type)
        label_type = self.label_type_for_report(report_type)

        writer = MarkdownTableWriter()
        writer.table_name = name

        columns = self.get_columns(metrics, include_difference_columns)
        writer.headers = [label_type] + columns

        labels = getattr(self, label_type)()
        labels.sort(key=lambda x: first_report.get(x, {}).get(sort_by, 0), reverse=True)
        writer.value_matrix = [
            [label]
            + self.get_row_values(report, label, metrics, include_difference_columns)
            for label in labels
        ]

        return writer.dumps()

    def write_combined_json_report(self, filepath=""):
        report_to_write = self.combined_reports()
        if not filepath:
            filepath = f"combined_nlu_reports.json"
        with open(filepath, "w+") as fh:
            json.dump(report_to_write, fh, indent=2)

    @classmethod
    def results_from_combined_reports(cls, combined_reports):
        result_names = combined_reports["result_sets_combined"]
        combined_results = {name: defaultdict(dict) for name in result_names}
        for report_type in [
            INTENT_REPORT_NAME,
            ENTITY_REPORT_NAME,
            RESPONSE_SELECTION_REPORT_NAME,
        ]:
            for label, values in combined_reports[f"combined_{report_type}"].items():
                for report_name, metrics in values.items():
                    if metrics:
                        combined_results[report_name][report_type][label] = metrics

        results = []
        for name, reports in combined_results.items():
            result = RasaNLUTestResult(name=name)
            for report_type in [
                INTENT_REPORT_NAME,
                ENTITY_REPORT_NAME,
                RESPONSE_SELECTION_REPORT_NAME,
            ]:
                setattr(result, report_type, reports[report_type])
            results.append(result)
        return results

    @classmethod
    def load_from_combined_json_report(cls, filepath=""):
        if not filepath:
            filepath = f"combined_nlu_reports.json"
        with open(filepath, "r") as fh:
            loaded_report = json.load(fh)
        return cls(cls.results_from_combined_reports(loaded_report))


base_results = RasaNLUTestResult("results/1", "Stable")
base_results.load_from_results_dir()
other_results = RasaNLUTestResult("results/2", "Incoming")
other_results.load_from_results_dir()
combined_results = CombinedRasaNLUTestResults([base_results, other_results])
combined_results.write_combined_json_report()

loaded_results = CombinedRasaNLUTestResults.load_from_combined_json_report()

intent_table = loaded_results.intent_table("Intent Results Comparison")
entity_table = loaded_results.entity_table("Entity Results Comparison")
response_selection_table = loaded_results.response_selection_table(
    "Response Selection Results Comparison"
)

with open("results.md", "w+") as f:
    f.write(intent_table)
    f.write("\n\n\n")
    f.write(entity_table)
    f.write("\n\n\n")
    f.write(response_selection_table)
