# Leaderboards

`python -m neuroverse.experiments.tables` builds the three-page interactive dashboard in `results/neuroverse/` and updates the summary tables in `README.md` and this document.

## Interactive Dashboard Pages

| Page | Purpose | Scope |
|---|---|---|
| [`results/neuroverse/leaderboard.html`](../results/neuroverse/leaderboard.html) | Classifier leaderboard with problem-type tabs, Standard Metrics vs Split-by-Problem-Type column views, paradigm filters, coverage-mode switches, and critical difference diagrams | 72 distinct classifiers (plus 18 variant/control configs) across 77 scalp EEG problems |
| [`results/neuroverse/matrix.html`](../results/neuroverse/matrix.html) | Interactive problem-by-classifier score heatmap grouped under paradigm banners, with metric selector and multi-metric hover tooltips | 77 problems &times; 72 classifiers (or all 90 configs) |
| [`results/neuroverse/datasets.html`](../results/neuroverse/datasets.html) | Per-problem explorer comparing the `Default` floor, median, best score, winning paradigm, gain over floor, and spread | 77 scalp EEG problems |
| [`results/neuroverse_paper_2026/leaderboard.html`](../results/neuroverse_paper_2026/leaderboard.html) | Archived Rushbrooke et al. (2026) DMLR paper leaderboard | 20 estimators across 30 archive problems |

## Ranking Methodology & Coverage Rules

The result CSVs contain **90 classifier configurations** spanning **72 distinct classifiers** (`CANONICAL_ESTIMATORS`: 11 General TSML, 23 EEG Classical, 32 EEG Supervised DL, 2 EEG Foundation, and 4 Tabular) plus **18 preprocessing, tree-count, and random-weight ablation variants** (`VARIANT_ESTIMATORS`, such as `-BP140`/`-BP830` filter variants, `HC2-noTDE-500-pc`, `DrCIF`, `CBraMod-random`, and `LaBraM-random`). To avoid clone bias in Friedman/Wilcoxon rank tables, the primary leaderboard ranks the **72 distinct canonical classifiers** by default, with a one-click checkbox in `leaderboard.html` to include all 90 configurations.

Because extended cluster experiments include computationally intensive hybrids (`HC2-500-pc`) as well as structurally restricted EEG methods (such as `TRCSP-LDA-MOABB` on binary tasks and `LaBraM` on datasets with standard 10–20 channel labels), requiring 100% completion across all 77 problems would exclude most classifiers.

The leaderboard therefore provides two explicit ranking modes in the UI and Python API:

1. **Common Block (`>=80%` coverage, primary default)**:
   - For a selected problem scope of $N$ problems, every classifier with results on at least $\lceil 0.8 N \rceil$ problems is admitted.
   - Admitted classifiers are then evaluated strictly on their **shared completed problem intersection** (`common_problems`), so mean ranks, mean balanced accuracy, mean accuracy, AUROC, log loss, wins (ties included), and Wilcoxon–Holm critical difference cliques are paired on the exact same problems.
   - Tighter common-block thresholds (`>=90%` and `100%`) can be selected directly in `leaderboard.html`.
2. **All Available (No coverage gate, descriptive mode)**:
   - Admits every classifier with at least one result on the selected tab, normalising within-problem ranks to $[1, M]$ so restricted or partially completed pipelines can be inspected alongside full-archive methods.

## Programmatic Usage

Build a league table in Python for any problem type (`"All"`, `"BCI"`, `"MI"`, `"ME"`, `"ERP"`, `"VEP"`, `"Speech"`, `"Clinical"`, `"Cognitive"`):

```python
from neuroverse.datasets import by_type
from neuroverse.experiments.tables import (
    available_estimators,
    compute_league_table,
    load_metric,
)

estimators = available_estimators(exclude=("Default",))
frames = {
    m: {est: load_metric(est, m) for est in estimators}
    for m in ("balacc", "accuracy", "auroc", "logloss")
}
import pandas as pd
frames = {m: pd.DataFrame(cols) for m, cols in frames.items()}

mi_table, mi_common = compute_league_table(
    datasets=by_type("MI"),
    frames=frames,
    primary_metric="balacc",
    min_coverage_ratio=0.8,
    canonical_only=True,
)
print(mi_table.head(10))
```

The standalone Multiverse single-table HTML builder `leaderboard()` also works directly with both wide summary CSVs and per-estimator directories:

```python
from neuroverse.datasets import by_type
from neuroverse.experiments.tables import complete_estimators, leaderboard

erp_problems = by_type("ERP")
candidates = ["Deep4Net-NB", "EEGNeX-NB", "HC2-500-pc", "MRHydra", "XdawnCov-TS-SVM-MOABB"]
leaderboard(
    datasets=erp_problems,
    estimators=complete_estimators(erp_problems, candidates, metric="balacc"),
    metrics=["balacc", "accuracy", "auroc", "logloss"],
    sort_by="balacc",
    critical_difference=True,
    output_path="erp_leaderboard.html",
)
```

---

## Domain Leaderboards (Top 15 per Problem Type)

<!-- LEADERBOARD_BY_TYPE:START -->
### All Scalp EEG (77 problems; 42 common; 64 classifiers &ge;62/77)

| # | Classifier | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `HC2-500-pc` | General TSML | 63/77 | 11.86 | 54.36% | 56.44% | 4 | 17 |
| 2 | `Arsenal` | General TSML | 74/77 | 17.21 | 52.50% | 54.70% | 1 | 12 |
| 3 | `MRHydra` | General TSML | 69/77 | 18.18 | 51.49% | 53.09% | 4 | 6 |
| 4 | `DrCIF-500` | General TSML | 70/77 | 19.54 | 51.82% | 54.63% | 2 | 11 |
| 5 | `STC-aeon` | General TSML | 72/77 | 19.76 | 51.93% | 54.43% | 2 | 6 |
| 6 | `EEGNeX-NB` | EEG Supervised DL | 75/77 | 21.24 | 48.75% | 48.95% | 6 | 14 |
| 7 | `DE-LR` | EEG Classical | 71/77 | 24.55 | 48.78% | 50.04% | 1 | 10 |
| 8 | `RDST` | General TSML | 66/77 | 25.70 | 49.28% | 51.51% | 1 | 5 |
| 9 | `TIDNet-NB` | EEG Supervised DL | 75/77 | 26.31 | 48.17% | 48.11% | 0 | 3 |
| 10 | `TSLR-MOABB` | EEG Classical | 72/77 | 26.39 | 48.11% | 49.54% | 1 | 3 |
| 11 | `EEGInceptionMI-NB` | EEG Supervised DL | 75/77 | 26.82 | 49.31% | 49.12% | 2 | 4 |
| 12 | `TSEN-MOABB` | EEG Classical | 75/77 | 27.13 | 47.49% | 48.87% | 1 | 3 |
| 13 | `TSSVM-MOABB` | EEG Classical | 75/77 | 27.36 | 47.34% | 49.93% | 1 | 2 |
| 14 | `SincShallowNet-NB` | EEG Supervised DL | 75/77 | 28.18 | 45.97% | 45.08% | 0 | 2 |
| 15 | `FBMSNet-NB` | EEG Supervised DL | 75/77 | 28.40 | 46.97% | 46.57% | 1 | 1 |

### BCI (All) (54 problems; 31 common; 64 classifiers &ge;44/54)

| # | Classifier | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `HC2-500-pc` | General TSML | 46/54 | 9.31 | 52.81% | 53.77% | 4 | 17 |
| 2 | `Arsenal` | General TSML | 52/54 | 15.73 | 50.36% | 51.16% | 1 | 10 |
| 3 | `MRHydra` | General TSML | 51/54 | 16.63 | 49.46% | 50.15% | 3 | 4 |
| 4 | `DrCIF-500` | General TSML | 50/54 | 17.71 | 50.77% | 52.40% | 2 | 10 |
| 5 | `STC-aeon` | General TSML | 50/54 | 18.68 | 50.11% | 51.52% | 2 | 5 |
| 6 | `EEGNeX-NB` | EEG Supervised DL | 53/54 | 21.27 | 46.16% | 45.99% | 5 | 11 |
| 7 | `RDST` | General TSML | 46/54 | 21.29 | 48.38% | 49.60% | 1 | 5 |
| 8 | `TIDNet-NB` | EEG Supervised DL | 53/54 | 25.48 | 46.20% | 45.84% | 0 | 3 |
| 9 | `TSEN-MOABB` | EEG Classical | 52/54 | 26.16 | 45.36% | 46.34% | 0 | 2 |
| 10 | `FBMSNet-NB` | EEG Supervised DL | 53/54 | 26.55 | 44.87% | 43.96% | 0 | 0 |
| 11 | `SPARCNet-NB` | EEG Supervised DL | 53/54 | 26.65 | 43.37% | 43.64% | 0 | 2 |
| 12 | `TDE` | General TSML | 48/54 | 26.81 | 46.15% | 47.37% | 1 | 3 |
| 13 | `TSSVM-MOABB` | EEG Classical | 52/54 | 26.89 | 44.63% | 46.31% | 0 | 1 |
| 14 | `FgMDM-MOABB` | EEG Classical | 53/54 | 27.29 | 44.82% | 45.52% | 0 | 0 |
| 15 | `TSLR-MOABB` | EEG Classical | 52/54 | 27.34 | 45.33% | 46.25% | 0 | 2 |

### Motor Imagery (30 problems; 19 common; 62 classifiers &ge;24/30)

| # | Classifier | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `HC2-500-pc` | General TSML | 25/30 | 11.13 | 61.32% | 62.53% | 3 | 10 |
| 2 | `MRHydra` | General TSML | 28/30 | 16.84 | 58.39% | 59.33% | 2 | 2 |
| 3 | `DrCIF-500` | General TSML | 28/30 | 16.89 | 59.93% | 62.15% | 3 | 8 |
| 4 | `Arsenal` | General TSML | 29/30 | 17.32 | 59.51% | 60.45% | 0 | 7 |
| 5 | `TIDNet-NB` | EEG Supervised DL | 29/30 | 20.29 | 55.24% | 54.81% | 0 | 1 |
| 6 | `STC-aeon` | General TSML | 28/30 | 20.37 | 58.14% | 60.00% | 0 | 4 |
| 7 | `DE-LR` | EEG Classical | 29/30 | 21.63 | 56.20% | 56.80% | 0 | 3 |
| 8 | `TSLR-MOABB` | EEG Classical | 29/30 | 21.82 | 57.14% | 58.24% | 0 | 3 |
| 9 | `DLCSP-shLDA-MOABB` | EEG Classical | 29/30 | 22.26 | 56.98% | 58.95% | 0 | 3 |
| 10 | `FgMDM-MOABB` | EEG Classical | 29/30 | 22.84 | 56.56% | 57.44% | 0 | 2 |
| 11 | `EEGNeX-NB` | EEG Supervised DL | 29/30 | 23.16 | 53.35% | 53.28% | 3 | 6 |
| 12 | `TSEN-MOABB` | EEG Classical | 29/30 | 23.37 | 56.93% | 58.09% | 1 | 2 |
| 13 | `TSSVM-MOABB` | EEG Classical | 29/30 | 23.61 | 56.09% | 58.27% | 0 | 2 |
| 14 | `FBMSNet-NB` | EEG Supervised DL | 29/30 | 24.66 | 54.32% | 52.89% | 0 | 0 |
| 15 | `CSP-LDA-MOABB` | EEG Classical | 29/30 | 24.68 | 56.52% | 58.56% | 0 | 3 |

### Motor Execution (6 problems; 4 common; 68 classifiers &ge;5/6)

| # | Classifier | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `HC2-500-pc` | General TSML | 6/6 | 8.75 | 71.37% | 71.39% | 0 | 2 |
| 2 | `Arsenal` | General TSML | 6/6 | 9.50 | 70.28% | 70.20% | 0 | 1 |
| 3 | `EEGNeX-NB` | EEG Supervised DL | 6/6 | 10.50 | 71.71% | 71.65% | 1 | 3 |
| 4 | `TCFormer-NB` | EEG Supervised DL | 6/6 | 11.00 | 70.25% | 70.19% | 2 | 2 |
| 5 | `TIDNet-NB` | EEG Supervised DL | 6/6 | 12.50 | 69.94% | 69.94% | 0 | 1 |
| 6 | `SPARCNet-NB` | EEG Supervised DL | 6/6 | 14.25 | 68.29% | 68.14% | 0 | 0 |
| 7 | `RotationForest` | Tabular | 5/6 | 15.25 | 68.87% | 68.78% | 0 | 1 |
| 8 | `STC-aeon` | General TSML | 6/6 | 15.50 | 67.98% | 67.90% | 0 | 0 |
| 9 | `Deep4Net-NB` | EEG Supervised DL | 6/6 | 16.00 | 68.28% | 68.22% | 0 | 0 |
| 10 | `CTNet-NB` | EEG Supervised DL | 6/6 | 18.75 | 67.21% | 67.17% | 0 | 1 |
| 11 | `EEGInceptionMI-NB` | EEG Supervised DL | 6/6 | 18.75 | 66.32% | 66.46% | 0 | 1 |
| 12 | `EEGConformer-NB` | EEG Supervised DL | 6/6 | 19.00 | 66.58% | 66.54% | 0 | 2 |
| 13 | `DrCIF-500` | General TSML | 6/6 | 19.00 | 66.53% | 66.58% | 0 | 0 |
| 14 | `TMSANet-NB` | EEG Supervised DL | 6/6 | 20.12 | 66.06% | 65.92% | 0 | 0 |
| 15 | `FBMSNet-NB` | EEG Supervised DL | 6/6 | 20.75 | 65.63% | 65.73% | 0 | 0 |

### ERP / P300 (8 problems; 6 common; 61 classifiers &ge;7/8)

| # | Classifier | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `Deep4Net-NB` | EEG Supervised DL | 8/8 | 9.92 | 68.30% | 62.56% | 0 | 1 |
| 2 | `EEGNeX-NB` | EEG Supervised DL | 8/8 | 11.33 | 68.64% | 61.41% | 0 | 3 |
| 3 | `SPARCNet-NB` | EEG Supervised DL | 8/8 | 11.83 | 66.03% | 60.96% | 0 | 1 |
| 4 | `MRHydra` | General TSML | 7/8 | 12.58 | 63.14% | 79.15% | 1 | 1 |
| 5 | `EEGInceptionMI-NB` | EEG Supervised DL | 8/8 | 12.83 | 69.31% | 71.13% | 1 | 1 |
| 6 | `CTNet-NB` | EEG Supervised DL | 8/8 | 15.25 | 65.19% | 59.06% | 0 | 1 |
| 7 | `EEGSimpleConv-NB` | EEG Supervised DL | 8/8 | 16.83 | 65.08% | 65.60% | 0 | 3 |
| 8 | `TMSANet-NB` | EEG Supervised DL | 8/8 | 17.33 | 61.52% | 50.06% | 0 | 0 |
| 9 | `BrainModule-NB` | EEG Supervised DL | 8/8 | 18.08 | 64.60% | 64.04% | 0 | 3 |
| 10 | `TCFormer-NB` | EEG Supervised DL | 8/8 | 19.08 | 62.14% | 55.68% | 2 | 2 |
| 11 | `IFNet-NB` | EEG Supervised DL | 8/8 | 19.92 | 62.15% | 56.38% | 1 | 2 |
| 12 | `FBMSNet-NB` | EEG Supervised DL | 8/8 | 21.08 | 58.95% | 57.35% | 0 | 0 |
| 13 | `TIDNet-NB` | EEG Supervised DL | 8/8 | 21.33 | 61.75% | 58.80% | 0 | 1 |
| 14 | `EEGNet-NB` | EEG Supervised DL | 8/8 | 21.58 | 63.65% | 52.18% | 0 | 0 |
| 15 | `TRCA-BP640` | EEG Classical | 7/8 | 21.67 | 57.16% | 55.78% | 0 | 0 |

### VEP / SSVEP (6 problems; 3 common; 68 classifiers &ge;5/6)

| # | Classifier | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `STC-aeon` | General TSML | 5/6 | 6.33 | 37.42% | 38.32% | 0 | 1 |
| 2 | `XdawnCov-MDM-MOABB` | EEG Classical | 6/6 | 9.00 | 53.80% | 53.90% | 0 | 2 |
| 3 | `RDST` | General TSML | 6/6 | 10.33 | 31.01% | 31.64% | 0 | 0 |
| 4 | `DrCIF-500` | General TSML | 5/6 | 10.33 | 30.50% | 31.59% | 0 | 1 |
| 5 | `xDAWN-LDA-MOABB` | EEG Classical | 5/6 | 10.67 | 47.63% | 47.87% | 0 | 0 |
| 6 | `QUANT` | General TSML | 6/6 | 10.67 | 29.36% | 30.33% | 0 | 1 |
| 7 | `MRHydra` | General TSML | 6/6 | 10.83 | 30.27% | 30.83% | 0 | 0 |
| 8 | `AUG-TANG-SVM-MOABB` | EEG Classical | 5/6 | 11.00 | 43.12% | 43.89% | 1 | 1 |
| 9 | `HC2-500-pc` | General TSML | 5/6 | 11.67 | 29.43% | 30.00% | 0 | 0 |
| 10 | `TemplateCCA-BP640` | EEG Classical | 5/6 | 12.50 | 50.29% | 50.29% | 0 | 1 |
| 11 | `ERPCov-MDM-MOABB` | EEG Classical | 5/6 | 13.33 | 49.82% | 49.87% | 0 | 1 |
| 12 | `Arsenal` | General TSML | 6/6 | 13.67 | 27.95% | 28.58% | 0 | 1 |
| 13 | `XdawnCov-TS-SVM-MOABB` | EEG Classical | 5/6 | 16.17 | 54.58% | 55.28% | 0 | 2 |
| 14 | `IFNet-NB` | EEG Supervised DL | 6/6 | 21.33 | 47.31% | 46.51% | 0 | 0 |
| 15 | `LaBraM` | EEG Foundation | 6/6 | 21.33 | 22.13% | 22.54% | 0 | 0 |

### Speech BCI (4 problems; 4 common; 66 classifiers &ge;4/4)

| # | Classifier | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `TDE` | General TSML | 4/4 | 3.25 | 35.75% | 35.70% | 1 | 3 |
| 2 | `HC2-500-pc` | General TSML | 4/4 | 3.75 | 35.99% | 35.93% | 2 | 3 |
| 3 | `STC-aeon` | General TSML | 4/4 | 12.00 | 30.07% | 30.12% | 1 | 2 |
| 4 | `RotationForest` | Tabular | 4/4 | 12.50 | 28.95% | 28.88% | 0 | 1 |
| 5 | `RiemannianKNN-OAS-BP140` | EEG Classical | 4/4 | 15.50 | 30.17% | 30.19% | 0 | 1 |
| 6 | `TSSVM-MOABB` | EEG Classical | 4/4 | 21.00 | 28.22% | 28.27% | 0 | 0 |
| 7 | `CBraMod` | EEG Foundation | 4/4 | 21.75 | 25.35% | 25.22% | 0 | 0 |
| 8 | `DrCIF-500` | General TSML | 4/4 | 22.25 | 32.07% | 31.91% | 0 | 2 |
| 9 | `MRHydra` | General TSML | 4/4 | 22.75 | 27.59% | 27.41% | 0 | 0 |
| 10 | `TSEN-MOABB` | EEG Classical | 4/4 | 23.25 | 25.48% | 25.36% | 0 | 0 |
| 11 | `TemplateCCA-BP640` | EEG Classical | 4/4 | 24.75 | 24.84% | 24.91% | 0 | 0 |
| 12 | `Arsenal` | General TSML | 4/4 | 25.50 | 26.85% | 26.85% | 0 | 0 |
| 13 | `RandomForest` | Tabular | 4/4 | 26.25 | 25.93% | 26.02% | 0 | 0 |
| 14 | `FgMDM-MOABB` | EEG Classical | 4/4 | 26.25 | 25.28% | 25.25% | 0 | 0 |
| 15 | `FBCNet-NB` | EEG Supervised DL | 4/4 | 27.25 | 24.77% | 24.90% | 0 | 0 |

### Clinical (15 problems; 8 common; 59 classifiers &ge;12/15)

| # | Classifier | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `DE-SVM` | EEG Classical | 12/15 | 16.56 | 56.42% | 60.40% | 0 | 2 |
| 2 | `Arsenal` | General TSML | 14/15 | 17.88 | 56.99% | 63.33% | 0 | 2 |
| 3 | `EEGNeX-NB` | EEG Supervised DL | 14/15 | 18.69 | 55.46% | 57.43% | 1 | 2 |
| 4 | `DE-LR` | EEG Classical | 12/15 | 18.94 | 55.83% | 58.93% | 1 | 3 |
| 5 | `STC-aeon` | General TSML | 14/15 | 19.12 | 55.46% | 60.56% | 0 | 2 |
| 6 | `SincShallowNet-NB` | EEG Supervised DL | 14/15 | 20.19 | 54.75% | 53.15% | 0 | 2 |
| 7 | `ContraWR-NB` | EEG Supervised DL | 14/15 | 20.31 | 55.54% | 51.97% | 1 | 2 |
| 8 | `TSLR-MOABB` | EEG Classical | 12/15 | 20.50 | 54.47% | 57.67% | 1 | 1 |
| 9 | `ATCNet-NB` | EEG Supervised DL | 12/15 | 20.94 | 55.31% | 52.74% | 0 | 2 |
| 10 | `SleepStagerChambon2018-NB` | EEG Supervised DL | 14/15 | 21.06 | 54.03% | 56.03% | 0 | 0 |
| 11 | `TMSANet-NB` | EEG Supervised DL | 12/15 | 21.31 | 57.45% | 57.87% | 1 | 1 |
| 12 | `AttentionBaseNet-NB` | EEG Supervised DL | 12/15 | 21.50 | 53.01% | 49.43% | 0 | 0 |
| 13 | `ERPCov-MDM-MOABB` | EEG Classical | 14/15 | 23.38 | 53.62% | 53.59% | 0 | 0 |
| 14 | `TIDNet-NB` | EEG Supervised DL | 14/15 | 24.44 | 52.49% | 55.20% | 0 | 0 |
| 15 | `CSP-SVM-MOABB` | EEG Classical | 15/15 | 24.56 | 52.22% | 57.72% | 0 | 1 |

### Cognitive (8 problems; 6 common; 62 classifiers &ge;7/8)

| # | Classifier | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `DrCIF-500` | General TSML | 7/8 | 13.83 | 61.20% | 63.97% | 0 | 1 |
| 2 | `MRHydra` | General TSML | 8/8 | 16.00 | 60.24% | 62.08% | 1 | 1 |
| 3 | `Arsenal` | General TSML | 8/8 | 16.50 | 60.67% | 63.54% | 0 | 1 |
| 4 | `EEGNeX-NB` | EEG Supervised DL | 8/8 | 17.33 | 58.11% | 57.75% | 1 | 3 |
| 5 | `DE-LR` | EEG Classical | 8/8 | 21.00 | 61.19% | 63.04% | 0 | 2 |
| 6 | `TIDNet-NB` | EEG Supervised DL | 8/8 | 21.08 | 57.63% | 55.41% | 0 | 0 |
| 7 | `RDST` | General TSML | 8/8 | 21.33 | 58.78% | 62.02% | 0 | 2 |
| 8 | `FBCSP-SVM-MOABB` | EEG Classical | 8/8 | 21.58 | 59.21% | 62.50% | 0 | 1 |
| 9 | `XdawnCov-MDM-MOABB` | EEG Classical | 8/8 | 21.67 | 60.65% | 61.08% | 0 | 2 |
| 10 | `STC-aeon` | General TSML | 8/8 | 22.17 | 59.15% | 62.53% | 0 | 2 |
| 11 | `ShallowFBCSPNet-NB` | EEG Supervised DL | 8/8 | 22.75 | 57.13% | 56.65% | 0 | 0 |
| 12 | `MDM-MOABB` | EEG Classical | 8/8 | 22.92 | 60.00% | 61.98% | 0 | 0 |
| 13 | `TSLR-NB` | EEG Classical | 8/8 | 22.92 | 55.90% | 57.58% | 0 | 0 |
| 14 | `RotationForest` | Tabular | 7/8 | 23.75 | 55.74% | 60.01% | 0 | 0 |
| 15 | `TSSVM-MOABB` | EEG Classical | 8/8 | 25.08 | 61.51% | 60.48% | 1 | 1 |
<!-- LEADERBOARD_BY_TYPE:END -->
