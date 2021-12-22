from typing import Dict, List, Optional
import logging
import os
import json
import pandas as pd
import argparse

logger = logging.getLogger(__file__)


class NLUEvaluationResult:
    def __init__(self, name, report_filepath="", label_name=""):
        self.report_filepath = report_filepath
        self.name = name
        self.label_name = label_name
        self.report = self.load_report_from_file()
        self.df = self.load_df()

    def load_report_from_file(self) -> Dict:
        try:
            with open(self.report_filepath, "r") as f:
                report = json.loads(f.read())
        except FileNotFoundError:
            report = {}
        return report

    def load_report_from_df(self) -> Dict:
        report = self.df.T.to_dict()
        return report

    def load_df(self):
        df = pd.DataFrame.from_dict(self.report).transpose()
        df.name = self.name
        df = self.drop_excluded_classes(df)
        return self.set_index_names(df)

    def set_index_names(self, df):
        df = df[:]
        df.columns.set_names("metric", inplace=True)
        df.index.set_names(self.label_name, inplace=True)
        return df

    @classmethod
    def remove_excluded_classes(cls, classes):
        for excluded_class in ["accuracy"]:
            try:
                classes.remove(excluded_class)
            except:
                pass
        return classes

    @classmethod
    def drop_excluded_classes(cls, df):
        for excluded_class in ["accuracy"]:
            try:
                df = df.drop(excluded_class)
            except:
                pass
        return df

    @classmethod
    def drop_non_numeric_metrics(cls, df):
        for non_numeric_metric in ["confused_with"]:
            try:
                df = df.drop(columns=non_numeric_metric)
            except:
                pass
        return df

    @classmethod
    def sort_by_support(cls, df):
        return df.sort_values(by="support", ascending=False)

    def create_html_table(self, df: pd.DataFrame, columns=None):
        if not columns:
            columns = df.columns
        df_for_table = df[columns]
        df_for_table.columns.set_names([None,None], inplace=True)
        html_table = df_for_table.to_html(na_rep="N/A")
        return html_table




class CombinedNLUEvaluationResults(NLUEvaluationResult):
    def __init__(
        self,
        name,
        result_sets_to_combine: Optional[List[NLUEvaluationResult]] = None,
        label_name="",
    ):
        self.name = name
        if not result_sets_to_combine:
            result_sets_to_combine = []
        self.result_sets = result_sets_to_combine
        self.label_name = label_name
        self.df = self.load_joined_df()
        self.report = self.load_joined_report()

    def load_joined_df(self) -> pd.DataFrame:
        if not self.result_sets:
            columns = pd.MultiIndex(levels=[[], []], codes=[[], []])
            index = pd.Index([])
            joined_df = pd.DataFrame(index=index, columns=columns)
        else:
            joined_df = pd.concat(
                [result.df for result in self.result_sets],
                axis=1,
                keys=[result.name for result in self.result_sets],
            )
        self.drop_excluded_classes(joined_df)
        return self.set_index_names(joined_df)

    def set_index_names(self, joined_df):
        joined_df = joined_df.swaplevel(axis="columns")
        joined_df.columns.set_names(["metric", "result_set"], inplace=True)
        joined_df.index.set_names([self.label_name], inplace=True)

        return joined_df

    def load_joined_report(self):
        report = {
            label: {
                metric: self.df.loc[label].xs(metric).to_dict()
                for metric in self.df.loc[label].index.get_level_values("metric")
                if label
            }
            for label in self.df.index
        }
        return report

    def load_result_sets_from_df(self):
        result_sets = []
        for result_set_name in self.df.columns.get_level_values("result_set"):
            result = NLUEvaluationResult(
                name=result_set_name, label_name=self.label_name
            )
            result.df = self.df.swaplevel(axis=1)[result_set_name]
            result.report = result.load_report_from_df()
            result_sets.append(result)
        return result_sets

    @classmethod
    def drop_non_numeric_metrics(cls, df):
        for non_numeric_metric in ["confused_with"]:
            try:
                df = df.drop(columns=non_numeric_metric, level="metric")
            except:
                pass
        return df

    @classmethod
    def sort_by_support(cls, df):
        return df.sort_values(
            by=[("support", df["support"].iloc[:, 0].name)],
            ascending=False
        )

    @classmethod
    def order_metrics(cls, df, metrics_order=None):
        if not metrics_order:
            metrics_order = df.columns.get_level_values("metric")
        metrics_order_dict = {v: k for k, v in enumerate(metrics_order)}
        df = df.sort_index(
            axis=1,
            level="metric",
            key=lambda index: pd.Index(
                [metrics_order_dict.get(x) for x in index], name="metric"
            ),
            sort_remaining=False,
        )
        return df

    @classmethod
    def order_result_sets(cls, df, result_set_order=None):
        if not result_set_order:
            result_set_order = [result.name for result in df.columns.get_level_values("result_set")]
        result_set_order_dict = {v: k for k, v in enumerate(result_set_order)}
        df.sort_index(
            axis="columns",
            level="result_set",
            key=lambda index: pd.Index(
                [result_set_order_dict.get(x) for x in index], name="result_set"
            ),
            sort_remaining=False,
        )
        return df

    def write_combined_json_report(self, filepath):
        with open(filepath, "w+") as fh:
            json.dump(self.report, fh, indent=2)

    def load_df_from_report(self):
        joined_df = pd.DataFrame.from_dict(
            {
                (label, metric): self.report[label][metric]
                for label in self.report.keys()
                for metric in self.report[label].keys()
            },
            orient="index",
        ).unstack()
        return self.set_index_names(joined_df)

    @classmethod
    def load_from_combined_json_report(cls, filepath, label_name):
        combined_results = cls(label_name=label_name)
        with open(filepath, "r") as fh:
            combined_results.report = json.load(fh)
        combined_results.df = combined_results.load_df_from_report()
        combined_results.result_sets = combined_results.load_result_sets_from_df()
        return combined_results

    def get_diff_df(self, base_result_set_name=None, metrics_to_diff=None):
        if not base_result_set_name:
            base_result_set_name = self.result_sets[0].name
        if not metrics_to_diff:
            metrics_to_diff = list(set(self.df.columns.get_level_values("metric")))

        def diff_from_base(x):
            metric = x.name[0]
            if metric == "confused_with":
                return
            try:
                base_result = self.df[(metric, base_result_set_name)]
            except KeyError:
                return
            if metric == "support":
                return x.fillna(0) - base_result.fillna(0)
            return x-base_result


        diff_df = self.df[metrics_to_diff].apply(diff_from_base, result_type="expand",axis=0)
        diff_df.drop(columns=base_result_set_name, level=1, inplace=True)
        diff_df = self.drop_non_numeric_metrics(diff_df)
        diff_df.rename(lambda col: f"({col} - {base_result_set_name})", axis=1, level=1, inplace=True)
        return diff_df

    def show_labels_with_changes(self, base_result_set_name=None, metrics_to_diff=None):
        diff_df = self.get_diff_df(base_result_set_name, metrics_to_diff)
        rows_with_changes = (diff_df != 0).any(axis=1)
        df = self.df.loc[rows_with_changes]
        diff_df_selected = diff_df.loc[rows_with_changes]
        combined_diff_df = pd.concat([df, diff_df_selected], axis=1)
        return combined_diff_df


def compare_and_format_results(result_dirs, outfile):
    with open(outfile, "w+") as fh:
        fh.write("<h1>NLU Cross-Validation Results</h1>")
        fh.write("<body>These tables display only items with changes in at least one metric compared to the last stable result.</body>")

    intent_result_sets = [NLUEvaluationResult(result_dir, f"{result_dir}/intent_report.json", "intent") for result_dir in result_dirs]
    combined_intent_results = CombinedNLUEvaluationResults("Intent Prediction Results", intent_result_sets, "intent")
    combined_intent_results.write_combined_json_report("combined_intent_report.json")

    metrics_to_diff = ["support", "f1-score"]
    intent_result_changes = combined_intent_results.show_labels_with_changes(metrics_to_diff=metrics_to_diff)
    intent_result_changes = combined_intent_results.sort_by_support(intent_result_changes)
    metrics_to_display=["support", "f1-score","confused_with"]
    intent_table = combined_intent_results.create_html_table(intent_result_changes, columns=metrics_to_display)
    with open(outfile, "a") as fh:
        fh.write(f"<h2>{combined_intent_results.name}</h2>")
        fh.write(intent_table)
        fh.write("\n")

    if os.path.exists(os.path.join(result_dirs[0], "DIETClassifier_report.json")):
        entity_result_sets = [NLUEvaluationResult(result_dir, f"{result_dir}/DIETClassifier_report.json", "entity") for result_dir in result_dirs]
        combined_entity_results = CombinedNLUEvaluationResults("Entity Extraction Results", entity_result_sets, "entity")
        combined_entity_results.write_combined_json_report("combined_entity_report.json")

        entity_result_changes = combined_entity_results.show_labels_with_changes(metrics_to_diff = ["support", "f1-score", "precision", "recall"])
        entity_result_changes = combined_entity_results.sort_by_support(entity_result_changes)
        metrics_to_display=["support", "f1-score","precision", "recall"]
        entity_table = combined_entity_results.create_html_table(entity_result_changes, columns=metrics_to_display)
        with open(outfile, "a") as fh:
            fh.write(f"<h2>{combined_entity_results.name}</h2>")
            fh.write(entity_table)
            fh.write("\n")

    if os.path.exists(os.path.join(result_dirs[0], "response_selection_report.json")):
        response_selection_result_sets = [NLUEvaluationResult(result_dir, f"{result_dir}/response_selection_report.json", "retrieval_intent") for result_dir in result_dirs]
        combined_response_selection_results = CombinedNLUEvaluationResults("Response Selection Results", response_selection_result_sets, "retrieval_intent")
        combined_response_selection_results.write_combined_json_report("combined_response_selection_report.json")

        response_selection_result_changes = combined_response_selection_results.show_labels_with_changes(metrics_to_diff = ["support", "f1-score", "precision", "recall"])
        response_selection_result_changes = combined_response_selection_results.sort_by_support(response_selection_result_changes)
        metrics_to_display=["support", "f1-score","precision", "recall"]
        response_selection_table = combined_response_selection_results.create_html_table(response_selection_result_changes, columns=metrics_to_display)

        with open(outfile, "a") as fh:
            fh.write(f"<h2>{combined_response_selection_results.name}</h2>")
            fh.write(response_selection_table)

def _create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare two sets of NLU evaluation results and format them as an HTML table")
    parser.add_argument("--result_dirs", nargs="+", default=["results"], help="List of directories containing separate sets of NLU evaluation results")
    parser.add_argument(
        "--outfile",
        help=(
            "File to write HTML table to"
        ),
        default="formatted_compared_results.html",
    )
    return parser


if __name__ == "__main__":
    parser = _create_argument_parser()
    args = parser.parse_args()
    result_dirs = args.result_dirs
    outfile = args.outfile
    compare_and_format_results(result_dirs, outfile)
