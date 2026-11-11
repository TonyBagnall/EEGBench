"""Turn raw tsml-eval prediction files into the result files used here.

Two result layouts are supported across the repository:

1. **Wide summary layout** (default in ``results/neuroverse`` for the 76-problem,
   90-classifier study)::

       results/neuroverse/accuracy.csv
       results/neuroverse/balacc.csv
       results/neuroverse/auroc.csv
       results/neuroverse/logloss.csv
       results/neuroverse/classifiers.csv
       results/neuroverse/datasets.csv

   Each metric file holds one row per dataset and one column per classifier.

2. **Multiverse per-estimator layout** (used in ``results/neuroverse_paper_2026``
   and ``aeon-toolkit/multiverse``)::

       results/<archive>/<classifier>/<classifier>_<metric>.csv

   Each file holds one row per dataset and one column per resample, labelled
   ``Resamples:``.

:func:`export_wide_snapshot` builds the wide summary directly from a
``tsml-eval`` category directory tree (``<family>/<classifier>/Predictions/<dataset>/testResample0.csv``),
and :func:`wide_to_multiverse` / :func:`multiverse_to_wide` convert losslessly
between the two layouts.
"""

from __future__ import annotations

__all__ = [
    "ingest",
    "ingest_default",
    "export_wide_snapshot",
    "compute_default_from_predictions",
    "wide_to_multiverse",
    "multiverse_to_wide",
]

import argparse
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from neuroverse.datasets import STUDY_TAXONOMY, metadata, neuroverse, neuroverse_76

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

WIDE_METRICS = ("accuracy", "balacc", "logloss", "auroc")

# Timings are written beside the metrics in Multiverse layout but kept out of
# the leaderboard: the deep learners ran on GPU and the rest on CPU, so they do
# not compare. Both are in milliseconds, as tsml-eval records them.
timings = {
    "fittime": "fit_time",
    "predicttime": "predict_time",
}

# name used here -> directory name in the 2026 paper raw results, where different
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

DEFAULT_SKIP_ESTIMATORS = frozenset({"STC", "FreshPRINCE", "MiniROCKET", "ROCKET"})
DEFAULT_KEEP_HYBRID = frozenset({"HC2-500-pc", "HC2-noTDE-500-pc"})

results_path = Path(__file__).resolve().parents[2] / "results" / "neuroverse"


def _prediction_file(classifier, predictions_path, dataset, resample):
    """Locate one raw prediction file, allowing for the names the runs used."""
    return (
        Path(predictions_path)
        / SOURCE_CLASSIFIERS.get(classifier, classifier)
        / "Predictions"
        / SOURCE_DATASETS.get(dataset, dataset)
        / f"testResample{resample}.csv"
    )


def _write(classifier, datasets, scores, resample, out_root=None):
    """Write one file per column of scores, each with a row per dataset."""
    out = (results_path if out_root is None else Path(out_root)) / classifier
    out.mkdir(parents=True, exist_ok=True)
    for name, values in scores.items():
        series = pd.Series(values, index=datasets)
        series.index.name = "Resamples:"
        series.name = str(resample)
        series.to_csv(out / f"{classifier}_{name}.csv", float_format="%.6f")


def _score_prediction_csv(path: Path) -> tuple[float, float, float, float]:
    """Compute ``(accuracy, balacc, logloss, auroc)`` from a tsml-eval CSV."""
    from sklearn.metrics import roc_auc_score

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    match = re.search(r"Encoder dictionary: \{(.*?)\}", lines[0]) if lines else None
    rows = [line.split(",") for line in lines[3:] if line.strip()]
    if not rows:
        raise ValueError(f"empty prediction rows in {path}")

    y_true = np.array([row[0] for row in rows])
    y_pred = np.array([row[1] for row in rows])
    acc = float(np.mean(y_true == y_pred))
    bal = float(np.mean([np.mean(y_pred[y_true == cls] == cls) for cls in np.unique(y_true)]))
    logloss = float("nan")
    auroc = float("nan")

    try:
        probs = np.array([[float(x) for x in row[3:] if x != ""] for row in rows])
        enc = (
            {
                key: int(val)
                for key, val in re.findall(
                    r"(?:np\.str_\()?'([^']*)'\)?:\s*(\d+)", match.group(1)
                )
            }
            if match
            else {}
        )
        if not all(label in enc for label in y_true):
            enc = {
                label: idx
                for idx, label in enumerate(sorted(set(y_true) | set(y_pred)))
            }
        idx = np.array([enc[label] for label in y_true])
        logloss = float(
            -np.mean(np.log(np.clip(probs[np.arange(len(idx)), idx], 1e-15, 1.0)))
        )
        present = np.unique(idx)
        if len(present) == 2 and probs.shape[1] == 2:
            auroc = float(roc_auc_score(idx == present[1], probs[:, present[1]]))
        elif len(present) > 2:
            sub = probs[:, present]
            sub = sub / np.clip(sub.sum(axis=1, keepdims=True), 1e-15, None)
            auroc = float(
                roc_auc_score(
                    idx, sub, multi_class="ovr", average="macro", labels=present
                )
            )
    except Exception:  # noqa: BLE001 - missing/degenerate probability columns stay NaN
        pass

    return acc, bal, logloss, auroc


def export_wide_snapshot(
    raw_results_dir: Path | str,
    output_dir: Path | str = results_path,
    datasets: list[str] | None = None,
    skip_estimators=DEFAULT_SKIP_ESTIMATORS,
    keep_hybrid=DEFAULT_KEEP_HYBRID,
    resample: int = 0,
    include_default: bool = True,
) -> pd.DataFrame:
    """Export wide ``dataset x classifier`` CSVs from a ``tsml-eval`` results root.

    Parameters
    ----------
    raw_results_dir : Path or str
        Root directory organised as
        ``<family>/<classifier>/Predictions/<dataset>/testResample<id>.csv``.
    output_dir : Path or str
        Target directory for ``accuracy.csv``, ``balacc.csv``, ``logloss.csv``,
        ``auroc.csv``, ``classifiers.csv``, and ``datasets.csv``.
    datasets : list of str or None
        Problems to export. Defaults to :data:`neuroverse.datasets.neuroverse_76`.
    skip_estimators : collection of str
        Superseded estimator directory names to ignore.
    keep_hybrid : collection of str
        Allowed directory names inside ``Hybrid``.
    resample : int, default=0
        Resample index to read.
    include_default : bool, default=True
        Whether to also compute ``Default/Default_<metric>.csv`` from test labels.

    Returns
    -------
    pd.DataFrame
        Long-form table of exported scores.
    """
    raw_root = Path(raw_results_dir)
    out = Path(output_dir)
    selected = list(neuroverse_76 if datasets is None else datasets)
    selected_set = set(selected)
    skip_set = set(skip_estimators)
    hybrid_set = set(keep_hybrid)

    records = []
    pattern = f"*/*/Predictions/*/testResample{resample}.csv"
    for pred_file in raw_root.glob(pattern):
        category, estimator, _, dataset = pred_file.parts[-5:-1]
        if (
            category.startswith("_")
            or category == "NBack"
            or dataset not in selected_set
            or estimator in skip_set
        ):
            continue
        if category == "Hybrid" and estimator not in hybrid_set:
            continue
        acc, bal, ll, auc = _score_prediction_csv(pred_file)
        records.append((category, estimator, dataset, acc, bal, ll, auc))

    frame = pd.DataFrame(
        records,
        columns=["family", "classifier", "dataset", "accuracy", "balacc", "logloss", "auroc"],
    )
    if frame.duplicated(["classifier", "dataset"]).any():
        dups = frame[frame.duplicated(["classifier", "dataset"], keep=False)]
        raise ValueError(
            f"duplicate classifier/dataset entries found: {dups[['family', 'classifier', 'dataset']].to_dict('records')[:5]}"
        )

    out.mkdir(parents=True, exist_ok=True)
    for metric in WIDE_METRICS:
        wide = frame.pivot(index="dataset", columns="classifier", values=metric).reindex(selected)
        wide = wide[sorted(wide.columns, key=str.lower)]
        wide.to_csv(out / f"{metric}.csv", float_format="%.6f")

    (
        frame[["classifier", "family"]]
        .drop_duplicates()
        .sort_values("classifier", key=lambda s: s.str.lower())
        .to_csv(out / "classifiers.csv", index=False)
    )

    ds_rows = [
        {
            "dataset": ds,
            "family": STUDY_TAXONOMY.get(ds, ("", ""))[0],
            "bci_type": STUDY_TAXONOMY.get(ds, ("", ""))[1],
        }
        for ds in selected
    ]
    pd.DataFrame(ds_rows).to_csv(out / "datasets.csv", index=False)

    if include_default:
        compute_default_from_predictions(raw_root, out, datasets=selected, resample=resample)

    return frame


def compute_default_from_predictions(
    raw_results_dir: Path | str,
    output_dir: Path | str = results_path,
    datasets: list[str] | None = None,
    resample: int = 0,
) -> list[str]:
    """Compute the constant test-majority ``Default`` baseline from prediction files."""
    raw_root = Path(raw_results_dir)
    selected = list(neuroverse_76 if datasets is None else datasets)
    expected_test = metadata()["test_size"].to_dict()

    default_scores: dict[str, list[float]] = {m: [] for m in WIDE_METRICS}
    found: list[str] = []

    for dataset in selected:
        exp_n = expected_test.get(dataset)
        chosen_y = None
        for pred_file in raw_root.glob(f"*/*/Predictions/{dataset}/testResample{resample}.csv"):
            lines = pred_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            rows = [line.split(",") for line in lines[3:] if line.strip()]
            if not rows:
                continue
            if exp_n is not None and pd.notna(exp_n) and len(rows) != int(exp_n):
                continue
            chosen_y = np.array([row[0] for row in rows])
            break
        if chosen_y is None:
            continue

        classes, counts = np.unique(chosen_y, return_counts=True)
        p_vec = counts / counts.sum()
        found.append(dataset)
        default_scores["accuracy"].append(float(counts.max() / counts.sum()))
        default_scores["balacc"].append(float(1.0 / len(classes)))
        default_scores["auroc"].append(0.5)
        default_scores["logloss"].append(
            float(-np.sum(p_vec * np.log(np.clip(p_vec, 1e-15, 1.0))))
        )

    if found:
        _write("Default", found, default_scores, resample, out_root=output_dir)
    return found


def wide_to_multiverse(
    wide_dir: Path | str,
    output_dir: Path | str,
    metrics_list: tuple[str, ...] = WIDE_METRICS,
    resample: int = 0,
) -> list[str]:
    """Convert wide ``<metric>.csv`` tables to Multiverse per-estimator directories."""
    src = Path(wide_dir)
    dst = Path(output_dir)
    written: set[str] = set()

    for metric in metrics_list:
        csv_path = src / f"{metric}.csv"
        if not csv_path.is_file():
            continue
        wide = pd.read_csv(csv_path, index_col=0)
        for estimator in wide.columns:
            series = wide[estimator].dropna()
            if series.empty:
                continue
            est_dir = dst / str(estimator)
            est_dir.mkdir(parents=True, exist_ok=True)
            series.index.name = "Resamples:"
            series.name = str(resample)
            series.to_csv(est_dir / f"{estimator}_{metric}.csv", float_format="%.6f")
            written.add(str(estimator))

    return sorted(written, key=str.lower)


def multiverse_to_wide(
    multiverse_dir: Path | str,
    output_dir: Path | str,
    metrics_list: tuple[str, ...] = WIDE_METRICS,
    datasets: list[str] | None = None,
    exclude: tuple[str, ...] = ("Default",),
) -> list[str]:
    """Convert Multiverse per-estimator directories into wide ``<metric>.csv`` tables."""
    src = Path(multiverse_dir)
    dst = Path(output_dir)
    dst.mkdir(parents=True, exist_ok=True)
    excluded = set(exclude)

    estimators = sorted(
        (p.name for p in src.iterdir() if p.is_dir() and p.name not in excluded),
        key=str.lower,
    )
    written_metrics: list[str] = []
    for metric in metrics_list:
        cols: dict[str, pd.Series] = {}
        for estimator in estimators:
            path = src / estimator / f"{estimator}_{metric}.csv"
            if path.is_file():
                frame = pd.read_csv(path, index_col=0)
                cols[estimator] = frame.mean(axis=1)
        if not cols:
            continue
        wide = pd.DataFrame(cols)
        if datasets is not None:
            wide = wide.reindex(datasets)
        wide.index.name = "dataset"
        wide.to_csv(dst / f"{metric}.csv", float_format="%.6f")
        written_metrics.append(metric)

    return written_metrics


def ingest(classifier, predictions_path, datasets=None, resample=0):
    """Write one file per metric for a classifier, and return the datasets used.

    Datasets with no prediction file are left out rather than filled with a
    placeholder, so a classifier that failed on a problem is missing it, which
    is what the leaderboard reports.
    """
    from tsml_eval.evaluation.storage import load_classifier_results

    datasets = sorted(neuroverse) if datasets is None else sorted(datasets)
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
    """Write the majority class baseline, the Default column of the paper."""
    from tsml_eval.evaluation.storage import ClassifierResults, load_classifier_results

    datasets = sorted(neuroverse) if datasets is None else sorted(datasets)
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


def sync_snapshot(snapshot_dir: Path | str, target_dir: Path | str = results_path) -> None:
    """Copy a prepared wide-CSV snapshot directory into ``results/neuroverse``."""
    src = Path(snapshot_dir)
    dst = Path(target_dir)
    dst.mkdir(parents=True, exist_ok=True)
    for filename in (*[f"{m}.csv" for m in WIDE_METRICS], "classifiers.csv", "datasets.csv"):
        candidate = src / filename
        if candidate.is_file():
            shutil.copy2(candidate, dst / filename)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Ingest or sync Neuroverse result tables.")
    parser.add_argument(
        "--wide-from",
        type=Path,
        help="Export wide summary CSVs from a tsml-eval category directory (e.g. D:/Results/EEG).",
    )
    parser.add_argument(
        "--sync-from",
        type=Path,
        help="Sync wide CSVs from an existing snapshot folder (e.g. results/tsml-eval-20261111).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=results_path,
        help="Output results directory (default: results/neuroverse).",
    )
    parser.add_argument(
        "--to-multiverse",
        type=Path,
        help="Convert wide CSVs in --out into Multiverse per-estimator directories at this path.",
    )
    args = parser.parse_args(argv)

    if args.sync_from is not None:
        sync_snapshot(args.sync_from, args.out)
        print(f"Synced wide snapshot from {args.sync_from} -> {args.out}")
    elif args.wide_from is not None:
        frame = export_wide_snapshot(args.wide_from, args.out)
        print(
            f"Exported {len(frame)} results ({frame['classifier'].nunique()} classifiers, "
            f"{frame['dataset'].nunique()} datasets) -> {args.out}"
        )
    if args.to_multiverse is not None:
        written = wide_to_multiverse(args.out, args.to_multiverse)
        print(f"Wrote Multiverse directories for {len(written)} estimators -> {args.to_multiverse}")

    if args.sync_from is None and args.wide_from is None and args.to_multiverse is None:
        raw = Path("D:/Results/EEG")
        if raw.is_dir():
            frame = export_wide_snapshot(raw, args.out)
            print(
                f"Exported {len(frame)} results ({frame['classifier'].nunique()} classifiers, "
                f"{frame['dataset'].nunique()} datasets) -> {args.out}"
            )
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
