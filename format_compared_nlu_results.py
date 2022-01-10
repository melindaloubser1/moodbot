from typing import Dict, List, Optional, Text, NamedTuple
import logging
import os
import json
import pandas as pd
import argparse

logger = logging.getLogger(__file__)

class NamedResultFile(NamedTuple):
    filepath: Text
    name: Text


class NLUEvaluationResult:
    def __init__(self, name: Text="Evaluation Result", label_name: Text="label", json_report_filepath: Optional[Text]=None):
        self.json_report_filepath = json_report_filepath
        self.name = name
        self.label_name = label_name
        self.report = self.load_report_from_file()
        self.df = self.load_df()

    def load_report_from_file(self) -> Dict:
        try:
            with open(self.json_report_filepath, "r") as f:
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

    def sort_by_metric(self, sort_by_metric: Text):
        return self.df.sort_values(by=sort_by_metric, ascending=False)

    def get_sorted_labels(self, sort_by_metric: Text, labels: List[Text]=None):
        sorted_labels = self.sort_by_metric(sort_by_metric=sort_by_metric).index.tolist()
        avg_labels = [
                        "macro avg",
                        "micro avg",
                        "weighted avg"
                    ]
        labels_avg_first = [label for label in self.df.index.tolist() if label in avg_labels] + [label for label in sorted_labels if label not in avg_labels and (labels is None or label in labels)]
        return labels_avg_first

    def create_html_table(self, columns=None, labels=None, sort_by_metric="support"):
        labels = self.get_sorted_labels(sort_by_metric=sort_by_metric, labels=labels)
        if not columns:
            columns = self.df.columns
        df_for_table = self.df.loc[labels,columns]
        df_for_table.columns.set_names([None, None], inplace=True)
        df_for_table.index.set_names([None], inplace=True)
        html_table = df_for_table.to_html(na_rep="N/A")
        return html_table


class CombinedNLUEvaluationResults(NLUEvaluationResult):
    def __init__(
        self,
        name: Text="Combined Evaluation Results",
        label_name="label",
        result_sets: Optional[List[NLUEvaluationResult]] = None,
    ):
        self.name = name
        if not result_sets:
            result_sets = []
        self.result_sets = result_sets
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

    def sort_by_metric(self, sort_by_metric: Text):
        return self.df.sort_values(
                by=[(sort_by_metric, self.df[sort_by_metric].iloc[:, 0].name)], ascending=False
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
            result_set_order = [
                result.name for result in df.columns.get_level_values("result_set")
            ]
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
                difference = pd.Series(None, index=x.index)
                return difference
            try:
                base_result = self.df[(metric, base_result_set_name)]
            except KeyError:
                difference = pd.Series(None, index=x.index, dtype="float64")
                return difference
            if metric == "support":
                difference = x.fillna(0) - base_result.fillna(0)
            else:
                difference = x - base_result
            return difference

        diff_df = self.df[metrics_to_diff].apply(diff_from_base)
        diff_df.drop(columns=base_result_set_name, level=1, inplace=True)
        diff_df = self.drop_non_numeric_metrics(diff_df)
        diff_df.rename(
            lambda col: f"({col} - {base_result_set_name})",
            axis=1,
            level=1,
            inplace=True,
        )
        return pd.DataFrame(diff_df)

    def find_labels_with_changes(self, base_result_set_name=None, metrics_to_diff=None):
        diff_df = self.get_diff_df(base_result_set_name, metrics_to_diff)
        rows_with_changes = diff_df.apply(lambda x: x.any(), axis=1)
        df = self.df.loc[rows_with_changes]
        diff_df_selected = diff_df.loc[rows_with_changes]
        combined_diff_df = pd.concat([df, diff_df_selected], axis=1)
        return combined_diff_df.index.tolist()


def combine_results(result_files: List[NamedResultFile], label_name: Optional[Text]="label", title="Combined NLU Evaluation Results"):
    result_sets = [
        NLUEvaluationResult(
            name=result_file.name, label_name=label_name, json_report_filepath=result_file.filepath, 
        )
        for result_file in result_files
    ]
    combined_results = CombinedNLUEvaluationResults(
        name=title, result_sets=result_sets, label_name=label_name
    )
    combined_results.write_combined_json_report(f"combined_{label_name}_report.json")
    return combined_results

def parse_var(s):
    """
    Parse a key, value pair, separated by '='

    On the command line (argparse) a declaration will typically look like:
        foo=hello
    or
        foo="hello world"
    """
    items = s.split('=')
    key = items[0].strip()
    if len(items) > 1:
        value = '='.join(items[1:])
    return (key, value)


def parse_vars(items):
    """
    Parse a series of key-value pairs and return a dictionary
    """
    d = {}

    if items:
        for item in items:
            key, value = parse_var(item)
            d[key] = value
    return d

def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Combine & compare multiple sets of Rasa NLU evaluation results of the same type"
                    "(e.g. intent classification, entity extraction) and write the comparison to an HTML table"
    )
    parser.add_argument("result_files",
                        metavar="RESULT_FILEPATH_1=RESULT_LABEL1 RESULT_FILEPATH_2=RESULT_LABEL2 ...",
                        nargs='+',
                        help='The json report files that should be compared and the labels to associate with each of them. '
                            'All results must be of the same type (e.g. intent classification, entity extraction)'
                             'Labels for files should be unique.'
                             'For example: '
                             '\'intent_report.json=1 second_intent_report.json=2\'. '
                             'Do not put spaces before or after the = sign. '
                             'Label values with spaces should be put in double quotes. '
                             'For example: '
                             '\'previous_results/DIETClassifier_report.json="Previous Stable Results" results/DIETClassifier_report.json="New Results"\''
    )

    parser.add_argument(
        "--html_outfile",
        help=("File to which to write HTML table. File will be overwritten unless --append is specified."),
        default="formatted_compared_results.html",
    )

    parser.add_argument(
        "--append",
        help=("Append to html_outfile instead of overwriting it."),
        action='store_true'
    )

    parser.add_argument(
        "--json_outfile",
        help=("File to which to write combined json report."),
        default="combined_results.json",
    )

    parser.add_argument(
        "--title",
        help=("Title of HTML table."),
        default="Compared NLU Evaluation Results",
    )

    parser.add_argument(
        "--label_name",
        help=("Type of labels predicted e.g. 'intent', 'entity', 'retrieval intent'"),
        default="label",
    )

    parser.add_argument(
        "--metrics_to_diff",
        help=("Metrics to consider when determining changes across result sets."),
        nargs="+",
        default=["support", "f1-score"],
    )

    parser.add_argument(
        "--metrics_to_display",
        help=("Metrics to display in resulting HTML table."),
        nargs="+",
        default=["support", "f1-score"],
    )

    parser.add_argument(
        "--sort_by_metric",
        help=("Metrics to sort by (descending) in resulting HTML table."),
        default="support"
    )

    parser.add_argument(
        "--display_only_diff",
        help=("Display only labels with a change in at least one metric across result sets. Default is False"),
        action='store_true'
    )


    return parser

def main():
    parser = create_argument_parser()
    args = parser.parse_args()
    result_files = [NamedResultFile(filepath=filepath, name=name) for filepath, name in parse_vars(args.result_files).items()]
    combined_results = combine_results(result_files=result_files, label_name=args.label_name)

    if args.display_only_diff:
        labels_with_changes = combined_results.find_labels_with_changes(
            metrics_to_diff=args.metrics_to_diff
        )

        table = combined_results.create_html_table(
            labels=labels_with_changes, columns=args.metrics_to_display, sort_by_metric=args.sort_by_metric
        )

    else:
        table = combined_results.create_html_table(columns=args.metrics_to_display, sort_by_metric=args.sort_by_metric)

    mode = "w+"
    if args.append:
        mode = "a+"
    with open(args.html_outfile, mode) as fh:
        fh.write(f"<h1>{args.title}</h1>")
        if args.display_only_diff:
            fh.write(
                f"<body>Only averages and the {args.label_name}(s) that show differences in at least one of the following metrics: {args.metrics_to_diff} are displayed.</body>"
            )
        fh.write(table)


if __name__ == "__main__":
    main()
