"""Turn raw tsml-eval prediction files into the result files used here.

The experiment scripts write one file per classifier, dataset and resample

    <predictions_path>/<classifier>/Predictions/<dataset>/testResample<id>.csv

holding the labels, predictions and probability estimates. The leaderboard in
eegbench.experiments.tables reads something smaller: one file per classifier
and metric, with a row per dataset

    results/eegbench/<classifier>/<classifier>_<metric>.csv

This module is the step between the two. Metrics are computed by tsml-eval from
the stored predictions, so they do not depend on what the classifier reported.

The runs behind the paper used a few directory names that differ from the names
used here, which SOURCE_CLASSIFIERS and SOURCE_DATASETS map back.

Edit the settings in main and run it with

    python -m eegbench.experiments.ingest
"""

from pathlib import Path

import numpy as np
import pandas as pd
from tsml_eval.evaluation.storage import (
    ClassifierResults,
    load_classifier_results,
)

from eegbench.datasets import eegbench

# metric name used in the file name -> attribute on a tsml-eval results object
metrics = {
    "accuracy": "accuracy",
    "balacc": "balanced_accuracy",
    "auroc": "auroc_score",
    "f1": "f1_score",
    "logloss": "log_loss",
    "sensitivity": "sensitivity",
    "specificity": "specificity",
}

# Timings are written beside the metrics but kept out of the leaderboard: the
# deep learners ran on GPU and the rest on CPU, so they do not compare. Both
# are in milliseconds, as tsml-eval records them.
timings = {
    "fittime": "fit_time",
    "predicttime": "predict_time",
}

# name used here -> directory name in the raw results, where they differ
SOURCE_CLASSIFIERS = {
    "ROCKET": "rocket",
    "MiniROCKET": "minirocket",
    "QUANT": "quant",
    "FreshPRINCE": "freshprince",
    "RandomForest": "randomforest",
    "LogisticRegression": "logisticregression",
}
SOURCE_DATASETS = {
    "EpilepticSeizures": "Epilepsy",
}

results_path = Path(__file__).resolve().parents[2] / "results" / "eegbench"


def _prediction_file(classifier, predictions_path, dataset, resample):
    """Locate one raw prediction file, allowing for the names the runs used."""
    return (
        Path(predictions_path)
        / SOURCE_CLASSIFIERS.get(classifier, classifier)
        / "Predictions"
        / SOURCE_DATASETS.get(dataset, dataset)
        / f"testResample{resample}.csv"
    )


def _write(classifier, datasets, scores, resample):
    """Write one file per column of scores, each with a row per dataset."""
    out = results_path / classifier
    out.mkdir(parents=True, exist_ok=True)
    for name, values in scores.items():
        series = pd.Series(values, index=datasets)
        series.index.name = "Resamples:"
        series.name = str(resample)
        series.to_csv(out / f"{classifier}_{name}.csv")


def ingest(classifier, predictions_path, datasets=None, resample=0):
    """Write one file per metric for a classifier, and return the datasets used.

    Datasets with no prediction file are left out rather than filled with a
    placeholder, so a classifier that failed on a problem is missing it, which
    is what the leaderboard reports.
    """
    datasets = sorted(eegbench) if datasets is None else sorted(datasets)
    found = [
        d
        for d in datasets
        if _prediction_file(classifier, predictions_path, d, resample).is_file()
    ]

    columns = {**metrics, **timings}
    scores = {name: [] for name in columns}
    for dataset in found:
        results = load_classifier_results(
            str(_prediction_file(classifier, predictions_path, dataset, resample))
        )
        results.calculate_statistics()
        for name, attribute in columns.items():
            scores[name].append(getattr(results, attribute))

    _write(classifier, found, scores, resample)
    return found


def ingest_default(reference, predictions_path, datasets=None, resample=0):
    """Write the majority class baseline, the Default column of the paper.

    Default predicts the most common class in the test set for every case, with
    the test class frequencies as its probability estimates. It needs only the
    true labels, which are read from the prediction files of ``reference``, any
    classifier with a full set of results.

    This is the best any constant prediction can score, so it is a harder floor
    than a classifier that predicts the majority class of the train set, and it
    is not something that could be fitted without seeing the test labels.
    """
    datasets = sorted(eegbench) if datasets is None else sorted(datasets)
    found = [
        d
        for d in datasets
        if _prediction_file(reference, predictions_path, d, resample).is_file()
    ]

    scores = {name: [] for name in metrics}
    for dataset in found:
        labels = load_classifier_results(
            str(_prediction_file(reference, predictions_path, dataset, resample))
        ).class_labels
        counts = np.bincount(labels.astype(int))
        results = ClassifierResults(
            dataset_name=dataset,
            classifier_name="Default",
            n_classes=len(counts),
            class_labels=labels,
            predictions=np.full(len(labels), counts.argmax()),
            probabilities=np.tile(counts / counts.sum(), (len(labels), 1)),
        )
        results.calculate_statistics()
        for name, attribute in metrics.items():
            scores[name].append(getattr(results, attribute))

    _write("Default", found, scores, resample)
    return found


def main():
    from eegbench.estimators import ESTIMATORS

    predictions_path = "C:/Results/EEGResults/Results/Benchmarking"
    classifiers = list(ESTIMATORS)

    for classifier in classifiers:
        found = ingest(classifier, predictions_path)
        missing = sorted(set(eegbench) - set(found))
        print(f"  {classifier}: {len(found)} datasets, {len(metrics)} metrics")
        if missing:
            print(f"    missing: {', '.join(missing)}")

    found = ingest_default("HC2", predictions_path)
    print(f"  Default: {len(found)} datasets, from the test labels")


if __name__ == "__main__":
    main()
