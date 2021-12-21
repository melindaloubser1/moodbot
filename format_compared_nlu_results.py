import os
from typing import Dict, List, Text, Optional
from collections import defaultdict
import logging
import json
import pandas as pd

logger = logging.getLogger(__file__)


class NLUEvaluationResult:
    def __init__(self, report_filepath=None, name=None, label_name=None):
        self.report_filepath = report_filepath
        self.name = name or os.path.basename(report_filepath)
        self.label_name = label_name

    def load_report_from_file(self) -> Dict:
        try:
            with open(self.report_filepath, "r") as f:
                self.report = json.loads(f.read())
        except FileNotFoundError:
            self.report = {}
        self.load_df()

    def load_df(self):
        df = pd.DataFrame.from_dict(self.report).transpose()
        df.name = self.name
        df.columns.set_names("metric", inplace=True)
        if self.label_name:
            df.index.set_names(self.label_name, inplace=True)
        self.df = self.drop_excluded_classes(df)

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
                df.drop(excluded_class, inplace=True)
            except:
                pass
        return df

    def sort_by_support(self):
        self.df.sort_values(by="support", ascending=False, inplace=True)

    def create_html_table(self, columns=None):
        if not columns:
            columns = self.df.columns
        html_table = self.df[columns].to_html()
        return html_table


class CombinedNLUEvaluationResults(NLUEvaluationResult):
    def __init__(self, results_to_combine: List[NLUEvaluationResult], label_name=None):
        self.results = results_to_combine
        self.label_name = label_name
        self.df = self.join_dfs()

    def join_dfs(self) -> pd.DataFrame:
        joined_df = pd.concat(
            [result.df for result in self.results],
            axis=1,
            keys=[result.name for result in self.results],
        )
        joined_df.columns.set_names(["result_set", "metric"], inplace=True)
        joined_df = joined_df.swaplevel(axis="columns")
        if self.label_name:
            joined_df.index.set_names([self.label_name], inplace=True)
        self.drop_excluded_classes(joined_df)
        return joined_df

    def order_metrics(self, metrics_order=None):
        if not metrics_order:
            metrics_order = self.df.columns.get_level_values("metric")
        metrics_order_dict = {v: k for k, v in enumerate(metrics_order)}
        self.df.sort_index(
            axis="columns",
            level="metric",
            key=lambda index: pd.Index(
                [metrics_order_dict.get(x) for x in index],
                name="metric"
            ),
            inplace=True,
            sort_remaining=False,
        )

    def order_result_sets(self, result_set_order=None):
        if not result_set_order:
            result_set_order = [result.name for result in self.results]
        result_set_order_dict = {v: k for k, v in enumerate(result_set_order)}
        self.df.sort_index(
            axis="columns",
            level="result_set",
            key=lambda index: pd.Index(
                [result_set_order_dict.get(x) for x in index],
                name="result_set"
            ),
            inplace=True,
            sort_remaining=False,
        )

    def write_combined_json_report(self, filepath):
        report_to_write = self.combined_reports()
        with open(filepath, "w+") as fh:
            json.dump(report_to_write, fh, indent=2)

    @classmethod
    def results_from_combined_reports(cls, combined_reports):
        pass

    @classmethod
    def load_from_combined_json_report(cls, filepath):
        with open(filepath, "r") as fh:
            loaded_report = json.load(fh)
        return cls(cls.results_from_combined_reports(loaded_report))


a = NLUEvaluationResult("results/1/intent_report.json", "a", "intent")
a.load_report_from_file()
a.sort_by_support()

# table = a.create_html_table()
# with open("formatted_result.html", "w") as fh:
#     fh.write(table)

b = NLUEvaluationResult("results/2/intent_report.json", "b", "intent")
b.load_report_from_file()
b.sort_by_support()

c = NLUEvaluationResult("results/2/intent_report.json", "c", "intent")
c.load_report_from_file()
c.sort_by_support()


combined_results = CombinedNLUEvaluationResults([a, b, c], "intent")
combined_results.order_result_sets(["b", "c", "a"])
combined_results.order_metrics(["support","f1-score","precision","recall","confused_with"])
combined_results.df
self = combined_results
