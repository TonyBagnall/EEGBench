# tsml-eval EEG results, snapshot 2026-11-11 (provisional)

Test-set results for the train/test split of each problem (`testResample0`), taken from the
tsml-eval prediction files in `D:/Results/EEG`. Experiments are still running, so cells will fill in.

- `accuracy.csv`, `balacc.csv`, `logloss.csv`, `auroc.csv`: one row per dataset (76 eligible
  problems), one column per classifier (90). Blank means no result yet (not run, still running,
  or failed on time/memory).
- `auroc.csv`: binary problems use the positive-class probability; multiclass problems use
  one-vs-rest macro AUROC over the classes present in the test set.
- `logloss.csv`: natural-log loss of the true-class probability, clipped at 1e-15.
- `classifiers.csv`: classifier to family (the tsml-eval results folder). `-NB` = braindecode model
  via aeon-neuro; `-MOABB` = MOABB pipeline; `-BPxyz` = band-pass x to yz Hz; `CBraMod`/`LaBraM` are
  frozen probes, `-random` their random-weight controls.
- `datasets.csv`: dataset to family (Clinical, BCI, Cognitive) and BCI type (MI, ERP, VEP, Speech).
- `export_tsml_results.py`: the script that produced these files.

Excluded: MEG/ECoG problems, single-channel and legacy problems, and superseded result folders.
One cell (CNN on ImaginedArmMovements) has no probabilities, so its log loss and AUROC are blank.
