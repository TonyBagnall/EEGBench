# Leaderboards

`python -m neuroverse.experiments.tables` builds the three-page interactive dashboard in `results/neuroverse/` and updates the summary tables in `README.md` and this document.

## Interactive Dashboard Pages

| Page | Purpose | Scope |
|---|---|---|
| [`results/neuroverse/leaderboard.html`](../results/neuroverse/leaderboard.html) | Algorithm leaderboard with problem-type tabs, Standard Metrics vs Split-by-Problem-Type column views, paradigm filters, coverage-mode switches, and critical difference diagrams | 90 algorithms across 76 scalp EEG problems (and 7 domain/BCI subsets) |
| [`results/neuroverse/matrix.html`](../results/neuroverse/matrix.html) | Interactive problem-by-algorithm score heatmap grouped under paradigm banners, with metric selector and multi-metric hover tooltips | 76 problems &times; 90 algorithms |
| [`results/neuroverse/datasets.html`](../results/neuroverse/datasets.html) | Per-problem explorer comparing the `Default` floor, median, best score, winning paradigm, gain over floor, and spread | 76 scalp EEG problems |
| [`results/neuroverse_paper_2026/leaderboard.html`](../results/neuroverse_paper_2026/leaderboard.html) | Archived Rushbrooke et al. (2026) DMLR paper leaderboard | 20 estimators across 30 archive problems |

## Ranking Methodology & Coverage Rules

Because extended cluster experiments include computationally intensive hybrids (`HC2-500-pc`) as well as structurally restricted EEG methods (such as `TRCSP-LDA-MOABB` on binary tasks and `LaBraM` on datasets with standard 10–20 channel labels), requiring 100% completion across all 76 problems would exclude most classifiers.

The leaderboard therefore provides two explicit ranking modes in the UI and Python API:

1. **Common Block (`>=80%` coverage, primary default)**:
   - For a selected problem scope of $N$ problems, every classifier with results on at least $\lceil 0.8 N \rceil$ problems is admitted.
   - Admitted classifiers are then evaluated strictly on their **shared completed problem intersection** (`common_problems`), so mean ranks, mean balanced accuracy, mean accuracy, AUROC, log loss, wins (ties included), and Wilcoxon–Holm critical difference cliques are paired on the exact same problems.
   - Tighter common-block thresholds (`>=90%` and `100%`) can be selected directly in `leaderboard.html`.
2. **All Available (`All 90`, descriptive mode)**:
   - Admits every classifier with at least one result on the selected tab, normalising within-problem ranks to $[1, M]$ so restricted or partially completed pipelines can be inspected alongside full-archive methods.

## Programmatic Usage

Build a league table in Python for any problem type (`"All"`, `"BCI"`, `"MI"`, `"ERP"`, `"VEP"`, `"Speech"`, `"Clinical"`, `"Cognitive"`):

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
### All Scalp EEG (76 problems; 39 common; 80 algorithms &ge;61/76)

| # | Algorithm | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `HC2-500-pc` | General TSML | 63/76 | 15.86 | 53.60% | 55.69% | 3 | 13 |
| 2 | `HC2-noTDE-500-pc` | General TSML | 70/76 | 16.38 | 53.89% | 55.57% | 1 | 12 |
| 3 | `MRHydra` | General TSML | 69/76 | 22.45 | 51.04% | 52.70% | 4 | 5 |
| 4 | `Arsenal` | General TSML | 74/76 | 22.77 | 51.63% | 53.85% | 1 | 9 |
| 5 | `DrCIF` | General TSML | 69/76 | 23.01 | 50.85% | 53.70% | 0 | 4 |
| 6 | `DrCIF-500` | General TSML | 70/76 | 24.37 | 51.00% | 53.84% | 2 | 7 |
| 7 | `STC-aeon` | General TSML | 72/76 | 24.83 | 51.25% | 53.77% | 1 | 6 |
| 8 | `EEGNeX-NB` | EEG Supervised DL | 75/76 | 28.63 | 47.52% | 47.75% | 4 | 9 |
| 9 | `DE-LR` | EEG Classical | 71/76 | 29.58 | 48.73% | 49.98% | 1 | 4 |
| 10 | `TSLR-MOABB` | EEG Classical | 72/76 | 32.36 | 47.74% | 49.15% | 0 | 2 |
| 11 | `RDST` | General TSML | 66/76 | 33.06 | 48.23% | 50.47% | 1 | 4 |
| 12 | `TSEN-MOABB` | EEG Classical | 75/76 | 33.18 | 47.01% | 48.36% | 0 | 3 |
| 13 | `TSSVM-MOABB` | EEG Classical | 75/76 | 33.38 | 47.12% | 49.72% | 0 | 2 |
| 14 | `TIDNet-NB` | EEG Supervised DL | 75/76 | 33.79 | 47.25% | 47.21% | 0 | 3 |
| 15 | `FBMSNet-NB` | EEG Supervised DL | 75/76 | 34.28 | 46.29% | 45.88% | 1 | 1 |

### BCI (All) (53 problems; 29 common; 80 algorithms &ge;43/53)

| # | Algorithm | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `HC2-500-pc` | General TSML | 46/53 | 12.41 | 53.15% | 53.98% | 3 | 13 |
| 2 | `HC2-noTDE-500-pc` | General TSML | 50/53 | 15.24 | 52.63% | 53.29% | 1 | 11 |
| 3 | `DrCIF` | General TSML | 47/53 | 19.36 | 50.86% | 52.35% | 1 | 5 |
| 4 | `Arsenal` | General TSML | 52/53 | 20.55 | 50.58% | 51.22% | 1 | 7 |
| 5 | `MRHydra` | General TSML | 51/53 | 20.71 | 49.74% | 50.39% | 3 | 4 |
| 6 | `DrCIF-500` | General TSML | 50/53 | 21.19 | 51.16% | 52.67% | 2 | 8 |
| 7 | `STC-aeon` | General TSML | 50/53 | 22.78 | 50.53% | 51.81% | 1 | 5 |
| 8 | `RDST` | General TSML | 46/53 | 26.52 | 48.56% | 49.63% | 1 | 4 |
| 9 | `EEGNeX-NB` | EEG Supervised DL | 53/53 | 28.26 | 46.02% | 45.87% | 4 | 7 |
| 10 | `TDE` | General TSML | 48/53 | 31.47 | 46.56% | 47.66% | 0 | 3 |
| 11 | `SPARCNet-NB` | EEG Supervised DL | 53/53 | 31.72 | 44.15% | 44.45% | 0 | 2 |
| 12 | `FBMSNet-NB` | EEG Supervised DL | 53/53 | 31.74 | 44.98% | 44.05% | 0 | 0 |
| 13 | `TSEN-MOABB` | EEG Classical | 52/53 | 32.16 | 45.47% | 46.33% | 0 | 2 |
| 14 | `TIDNet-NB` | EEG Supervised DL | 53/53 | 32.36 | 46.28% | 45.93% | 0 | 3 |
| 15 | `TSSVM-MOABB` | EEG Classical | 52/53 | 33.12 | 44.76% | 46.29% | 0 | 1 |

### Motor Imagery (35 problems; 18 common; 82 algorithms &ge;28/35)

| # | Algorithm | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `HC2-500-pc` | General TSML | 31/35 | 15.78 | 62.28% | 63.54% | 2 | 8 |
| 2 | `HC2-noTDE-500-pc` | General TSML | 34/35 | 16.44 | 62.45% | 63.38% | 0 | 7 |
| 3 | `Arsenal` | General TSML | 35/35 | 22.50 | 60.57% | 61.50% | 0 | 5 |
| 4 | `DrCIF` | General TSML | 30/35 | 22.50 | 60.14% | 62.42% | 1 | 3 |
| 5 | `MRHydra` | General TSML | 34/35 | 23.56 | 58.47% | 59.48% | 2 | 2 |
| 6 | `DrCIF-500` | General TSML | 34/35 | 23.97 | 60.16% | 62.44% | 2 | 4 |
| 7 | `TIDNet-NB` | EEG Supervised DL | 35/35 | 24.75 | 56.97% | 56.49% | 0 | 1 |
| 8 | `EEGNeX-NB` | EEG Supervised DL | 35/35 | 26.69 | 55.57% | 55.52% | 3 | 6 |
| 9 | `STC-aeon` | General TSML | 34/35 | 26.83 | 58.99% | 60.89% | 0 | 2 |
| 10 | `RDST` | General TSML | 29/35 | 28.97 | 57.49% | 59.14% | 1 | 2 |
| 11 | `FBMSNet-NB` | EEG Supervised DL | 35/35 | 28.97 | 54.71% | 53.15% | 0 | 0 |
| 12 | `CSP+LDA-BP830` | EEG Classical | 34/35 | 29.19 | 56.87% | 57.99% | 0 | 1 |
| 13 | `DLCSP-shLDA-MOABB` | EEG Classical | 35/35 | 29.25 | 56.73% | 58.78% | 0 | 1 |
| 14 | `EEGConformer-NB` | EEG Supervised DL | 35/35 | 29.69 | 55.00% | 53.99% | 1 | 4 |
| 15 | `TSLR-MOABB` | EEG Classical | 35/35 | 30.67 | 56.21% | 57.45% | 0 | 1 |

### ERP / P300 (8 problems; 6 common; 78 algorithms &ge;7/8)

| # | Algorithm | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `Deep4Net-NB` | EEG Supervised DL | 8/8 | 10.92 | 68.30% | 62.56% | 0 | 1 |
| 2 | `SPARCNet-NB` | EEG Supervised DL | 8/8 | 13.00 | 66.03% | 60.96% | 0 | 1 |
| 3 | `EEGNeX-NB` | EEG Supervised DL | 8/8 | 13.25 | 68.64% | 61.41% | 0 | 3 |
| 4 | `MRHydra` | General TSML | 7/8 | 13.42 | 63.14% | 79.15% | 1 | 1 |
| 5 | `EEGInceptionMI-NB` | EEG Supervised DL | 8/8 | 14.58 | 69.31% | 71.13% | 1 | 1 |
| 6 | `CTNet-NB` | EEG Supervised DL | 8/8 | 17.42 | 65.19% | 59.06% | 0 | 1 |
| 7 | `EEGSimpleConv-NB` | EEG Supervised DL | 8/8 | 19.25 | 65.08% | 65.60% | 0 | 3 |
| 8 | `TMSANet-NB` | EEG Supervised DL | 8/8 | 19.50 | 61.52% | 50.06% | 0 | 0 |
| 9 | `HC2-noTDE-500-pc` | General TSML | 7/8 | 21.17 | 60.10% | 80.58% | 0 | 0 |
| 10 | `BrainModule-NB` | EEG Supervised DL | 8/8 | 22.17 | 64.60% | 64.04% | 0 | 3 |
| 11 | `TCFormer-NB` | EEG Supervised DL | 8/8 | 23.42 | 62.14% | 55.68% | 2 | 2 |
| 12 | `IFNet-NB` | EEG Supervised DL | 8/8 | 24.00 | 62.15% | 56.38% | 1 | 2 |
| 13 | `TSLR-NB` | EEG Classical | 7/8 | 24.58 | 55.05% | 56.50% | 0 | 0 |
| 14 | `TIDNet-NB` | EEG Supervised DL | 8/8 | 24.83 | 61.75% | 58.80% | 0 | 1 |
| 15 | `FBMSNet-NB` | EEG Supervised DL | 8/8 | 25.00 | 58.95% | 57.35% | 0 | 0 |

### VEP / SSVEP (6 problems; 3 common; 85 algorithms &ge;5/6)

| # | Algorithm | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `STC-aeon` | General TSML | 5/6 | 6.67 | 37.42% | 38.32% | 0 | 1 |
| 2 | `DrCIF-500` | General TSML | 5/6 | 10.67 | 30.50% | 31.59% | 0 | 0 |
| 3 | `XdawnCov-MDM-MOABB` | EEG Classical | 6/6 | 11.00 | 53.80% | 53.90% | 0 | 2 |
| 4 | `RDST` | General TSML | 6/6 | 11.00 | 31.01% | 31.64% | 0 | 0 |
| 5 | `HC2-noTDE-500-pc` | General TSML | 5/6 | 11.33 | 31.15% | 31.92% | 0 | 1 |
| 6 | `QUANT` | General TSML | 6/6 | 11.67 | 29.36% | 30.33% | 0 | 1 |
| 7 | `MRHydra` | General TSML | 6/6 | 12.17 | 30.27% | 30.83% | 0 | 0 |
| 8 | `AUG-TANG-SVM-MOABB` | EEG Classical | 5/6 | 12.33 | 43.12% | 43.89% | 1 | 1 |
| 9 | `xDAWN-LDA-MOABB` | EEG Classical | 5/6 | 12.67 | 47.63% | 47.87% | 0 | 0 |
| 10 | `HC2-500-pc` | General TSML | 5/6 | 13.00 | 29.43% | 30.00% | 0 | 0 |
| 11 | `DrCIF` | General TSML | 6/6 | 14.00 | 28.01% | 28.92% | 0 | 0 |
| 12 | `TemplateCCA-BP640` | EEG Classical | 5/6 | 15.50 | 50.29% | 50.29% | 0 | 1 |
| 13 | `Arsenal` | General TSML | 6/6 | 15.67 | 27.95% | 28.58% | 0 | 1 |
| 14 | `ERPCov-MDM-MOABB` | EEG Classical | 5/6 | 16.00 | 49.82% | 49.87% | 0 | 1 |
| 15 | `LaBraM-random` | EEG Foundation | 6/6 | 18.00 | 24.89% | 25.29% | 0 | 0 |

### Speech BCI (4 problems; 4 common; 83 algorithms &ge;4/4)

| # | Algorithm | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `TDE` | General TSML | 4/4 | 4.25 | 35.75% | 35.70% | 0 | 3 |
| 2 | `HC2-500-pc` | General TSML | 4/4 | 4.75 | 35.99% | 35.93% | 1 | 3 |
| 3 | `STC-aeon` | General TSML | 4/4 | 15.75 | 30.07% | 30.12% | 1 | 2 |
| 4 | `DrCIF` | General TSML | 4/4 | 16.25 | 31.91% | 31.79% | 0 | 1 |
| 5 | `RotationForest` | Tabular | 4/4 | 17.00 | 28.95% | 28.88% | 0 | 0 |
| 6 | `HC2-noTDE-500-pc` | General TSML | 4/4 | 19.50 | 31.03% | 31.04% | 0 | 1 |
| 7 | `RiemannianKNN-OAS-BP140` | EEG Classical | 4/4 | 20.25 | 30.17% | 30.19% | 0 | 0 |
| 8 | `TSSVM-MOABB` | EEG Classical | 4/4 | 26.75 | 28.22% | 28.27% | 0 | 0 |
| 9 | `DrCIF-500` | General TSML | 4/4 | 27.75 | 32.07% | 31.91% | 0 | 2 |
| 10 | `CBraMod` | EEG Foundation | 4/4 | 27.75 | 25.35% | 25.22% | 0 | 0 |
| 11 | `TSEN-MOABB` | EEG Classical | 4/4 | 28.25 | 25.48% | 25.36% | 0 | 0 |
| 12 | `CSP+SVM` | EEG Classical | 4/4 | 28.62 | 25.33% | 25.19% | 0 | 0 |
| 13 | `RiemannianKNN-OAS-BP830` | EEG Classical | 4/4 | 28.75 | 30.85% | 31.05% | 0 | 1 |
| 14 | `MRHydra` | General TSML | 4/4 | 28.75 | 27.59% | 27.41% | 0 | 0 |
| 15 | `CBraMod-random` | EEG Foundation | 4/4 | 31.50 | 25.47% | 25.48% | 0 | 1 |

### Clinical (15 problems; 8 common; 72 algorithms &ge;12/15)

| # | Algorithm | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `HC2-noTDE-500-pc` | General TSML | 13/15 | 15.12 | 58.72% | 63.14% | 0 | 1 |
| 2 | `DE-SVM` | EEG Classical | 12/15 | 20.50 | 56.42% | 60.40% | 0 | 2 |
| 3 | `Arsenal` | General TSML | 14/15 | 22.31 | 56.99% | 63.33% | 0 | 2 |
| 4 | `DE-LR` | EEG Classical | 12/15 | 23.50 | 55.83% | 58.93% | 1 | 1 |
| 5 | `EEGNeX-NB` | EEG Supervised DL | 14/15 | 24.06 | 55.46% | 57.43% | 1 | 2 |
| 6 | `CSP+SVM-BP140` | EEG Classical | 12/15 | 24.12 | 55.73% | 61.02% | 1 | 1 |
| 7 | `STC-aeon` | General TSML | 14/15 | 24.50 | 55.46% | 60.56% | 0 | 1 |
| 8 | `TSLR-MOABB` | EEG Classical | 12/15 | 25.00 | 54.47% | 57.67% | 0 | 1 |
| 9 | `TMSANet-NB` | EEG Supervised DL | 12/15 | 25.50 | 57.45% | 57.87% | 1 | 1 |
| 10 | `SincShallowNet-NB` | EEG Supervised DL | 14/15 | 25.69 | 54.75% | 53.15% | 0 | 1 |
| 11 | `ContraWR-NB` | EEG Supervised DL | 14/15 | 25.75 | 55.54% | 51.97% | 1 | 2 |
| 12 | `ATCNet-NB` | EEG Supervised DL | 12/15 | 26.12 | 55.31% | 52.74% | 0 | 2 |
| 13 | `SleepStagerChambon2018-NB` | EEG Supervised DL | 14/15 | 26.44 | 54.03% | 56.03% | 0 | 0 |
| 14 | `AttentionBaseNet-NB` | EEG Supervised DL | 12/15 | 26.94 | 53.01% | 49.43% | 0 | 0 |
| 15 | `ERPCov-MDM-MOABB` | EEG Classical | 14/15 | 28.56 | 53.62% | 53.59% | 0 | 0 |

### Cognitive (8 problems; 6 common; 79 algorithms &ge;7/8)

| # | Algorithm | Paradigm | Coverage | Mean Rank | Balanced Acc | Accuracy | Wins | Top-5 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `HC2-noTDE-500-pc` | General TSML | 7/8 | 16.83 | 63.74% | 65.56% | 2 | 2 |
| 2 | `DrCIF` | General TSML | 8/8 | 18.83 | 62.19% | 65.01% | 0 | 0 |
| 3 | `DrCIF-500` | General TSML | 7/8 | 19.25 | 61.20% | 63.97% | 0 | 1 |
| 4 | `MRHydra` | General TSML | 8/8 | 21.58 | 60.24% | 62.08% | 0 | 1 |
| 5 | `Arsenal` | General TSML | 8/8 | 22.75 | 60.67% | 63.54% | 0 | 1 |
| 6 | `EEGNeX-NB` | EEG Supervised DL | 8/8 | 23.17 | 58.11% | 57.75% | 1 | 3 |
| 7 | `DE-LR` | EEG Classical | 8/8 | 27.00 | 61.19% | 63.04% | 0 | 1 |
| 8 | `FBCSP-SVM-MOABB` | EEG Classical | 8/8 | 27.33 | 59.21% | 62.50% | 0 | 1 |
| 9 | `RDST` | General TSML | 8/8 | 27.67 | 58.78% | 62.02% | 0 | 1 |
| 10 | `TIDNet-NB` | EEG Supervised DL | 8/8 | 28.33 | 57.63% | 55.41% | 0 | 0 |
| 11 | `STC-aeon` | General TSML | 8/8 | 29.00 | 59.15% | 62.53% | 0 | 2 |
| 12 | `XdawnCov-MDM-MOABB` | EEG Classical | 8/8 | 29.42 | 60.65% | 61.08% | 0 | 1 |
| 13 | `TSLR-NB` | EEG Classical | 8/8 | 29.58 | 55.90% | 57.58% | 0 | 0 |
| 14 | `ShallowFBCSPNet-NB` | EEG Supervised DL | 8/8 | 30.00 | 57.13% | 56.65% | 0 | 0 |
| 15 | `MDM-MOABB` | EEG Classical | 8/8 | 30.83 | 60.00% | 61.98% | 0 | 0 |
<!-- LEADERBOARD_BY_TYPE:END -->
