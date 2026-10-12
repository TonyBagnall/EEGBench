# Leaderboards

`python -m eegbench.experiments.tables` builds three pages in `results/eegbench` and the
table in the README.

| Page | Estimators | Datasets |
|---|---|---|
| `leaderboard.html` | Those with a result on all 30 datasets | All 30 |
| `leaderboard_all.html` | All with results | Those every estimator completed |
| `datasets.html` | All with results | All 30, one row each |

A leaderboard has an estimator per row and an average score and average rank for each
metric. It only uses datasets with a result for every estimator on every metric, so each
column describes the same problems. One estimator missing a few datasets would remove
them for everyone, which is why the main page takes only the complete estimators.

Every column is sortable: click a heading to sort by it, and again to reverse.

## Building your own

```python
from eegbench.datasets import by_domain, eegbench
from eegbench.experiments.tables import (
    available_estimators,
    complete_estimators,
    leaderboard,
)

datasets = sorted(eegbench)
leaderboard(
    datasets=datasets,
    estimators=complete_estimators(datasets, available_estimators()),
    metrics=["accuracy", "balacc", "auroc", "logloss"],   # default: all seven
    sort_by="balacc",                                     # orders the rows
    output_path="leaderboard_balacc.html",
)
```

The archive spans three application areas, and what works on one need not work on
another. `by_domain` gives a leaderboard for one of them:

```python
leaderboard(
    datasets=by_domain("Med"),
    estimators=["HC2", "MRHydra", "EEGNet", "DCN", "CSP-SVM", "R-MDM"],
    title="EEGBench: medical",
    output_path="leaderboard_med.html",
)
```

There are 7 medical, 18 BCI and 5 psychology datasets, so average ranks on one area
move a lot with a single dataset.

## Critical difference diagrams

The paper compares classifiers with a critical difference diagram, using pairwise
Wilcoxon signed-rank tests with a Holm correction to form cliques. Add one with
`critical_difference=True`. It is drawn for the `sort_by` metric and, by default, for
the six best-ranked estimators only; `max_cd_estimators=None` shows them all. Ranks in
the diagram are among the estimators shown, so restricting it changes the statistics and
not just the picture.

## The dataset page

`datasets.html` has a row per dataset: the Default baseline, the median, best and worst
over the other estimators, which was best, the gain of the best over the baseline, and
the spread from best to worst. It is sorted by gain, so the problems where nothing beats
the baseline come first. Best is a maximum over many estimators and so is optimistic:
read it as what can currently be done on a problem, not what any one method delivers.
