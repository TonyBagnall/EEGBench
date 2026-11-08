# Additional EEG datasets

These local preparations use the same layout as the other datasets in
`D:/Data/EEG/`. They are separate from the original 30-problem paper archive and
its unchanged results. They have not been uploaded to Zenodo or registered for
aeon's automatic downloads.

The [BCI IV 2a, ISRUC-Sleep and FACED preparations](openeegbench-local-preparations.md)
are also documented separately, including fixed splits, source labels, ISRUC
channel derivations, FACED's absent Neutral class and local-use limitations.

| Dataset | Domain | Channels | Length | Classes | Subjects | Train | Test | Hz | Status |
|---|---|---|---|---|---|---|---|---|---|
| MentalArithmetic | BCI | 19 | 1000 | 2 | 36 | 1515 | 192 | 200 | Validated |
| ImaginedCommands | BCI | 64 | 600 | 5 | 15 | 5250 | 750 | 200 | Validated; within-subject run split |
| ChildhoodSeizures | Med | 17 | 2000 | 2 | 22 | 34045 | 2140 | 200 | Validated; bipolar EEG |

The subject count uses normalized participant IDs where known; ChildhoodSeizures has 23 case IDs for
22 people. BCI and Med
have the same meanings as in the [original dataset overview](datasets.md).
Signals have shape `(cases, channels, timepoints)`. Original validation is appended
to training, with ordering within each partition unchanged; original test is
preserved. There is no separate validation split or prescribed validation fold.

## Files and loading

Validated folders are `D:/Data/EEG/MentalArithmetic/`, `ImaginedCommands/`, and `ChildhoodSeizures/`.
Each folder contains:

- `Name_TRAIN.ts`, `Name_TEST.ts`: standard multivariate aeon files, with the
  original encoded numeric labels.
- `Name_rows.tsv`: case metadata ordered TRAIN then TEST. `split` and zero-based
  `row` identify the corresponding case; read IDs as strings. All recovered source
  fields and the original train/validation/test partition are retained.
- `Name_metadata.json` and `channels.txt`: exact channel order, sensor kinds,
  dimensions, label mapping, preprocessing, provenance and limitations.
- `Name_validation.json`, `Name_manifest.json`: round-trip results, preparation
  status and file hashes; the final manifest marks a completed export.
- `cases_train.parquet`, `cases_test.parquet`, `source_metadata/`,
  `source-manifest.json`, `source-validation.json`, `source-chunks.json`,
  `conversion_code/`, and `ATTRIBUTION.txt`: compact metadata and source evidence.

Every `.ts` case is re-read from disk and checked for exact float32 equality and
label agreement with its HDF5 source. Case-table order and string IDs are checked.
Representative exported cases are loaded with aeon and used to fit/predict with
SummaryClassifier. This checks compatibility; no classification results are added.
Large files are validated as streams rather than loaded completely into RAM.

```python
from pathlib import Path
import pandas as pd
from aeon.datasets import load_from_ts_file

name = "MentalArithmetic"
folder = Path("D:/Data/EEG") / name
X_train, y_train = load_from_ts_file(folder / f"{name}_TRAIN.ts")
X_test, y_test = load_from_ts_file(folder / f"{name}_TEST.ts")
rows = pd.read_csv(folder / f"{name}_rows.tsv", sep="\t", dtype=str)
assert len(rows[rows["split"] == "TRAIN"]) == len(X_train)
```

## MentalArithmetic

- **Original source / other names:** *EEG During Mental Arithmetic Tasks*,
  [PhysioNet EEGmat v1.0.0](https://physionet.org/content/eegmat/1.0.0/),
  [DOI 10.13026/C2JQ1P](https://doi.org/10.13026/C2JQ1P);
  OpenEEGBench `arithmetic_zyma2019`.
- **Processed source:** [braindecode/arithmetic_zyma2019](https://huggingface.co/datasets/braindecode/arithmetic_zyma2019/tree/8359206e7e1b3d1f068033348e291d6677be1920),
  pinned revision `8359206e7e1b3d1f068033348e291d6677be1920`.
- **Task / dimensions:** serial-subtraction arithmetic versus eyes-closed rest;
  36 participants, 72 recordings; train `(1515, 19, 1000)`, test `(192, 19, 1000)`.
  Labels `0 = mentalArithmetic`, `1 = rest`; class counts 384/1131 in training,
  48/144 in test.
- **Derivation:** five-second, non-overlapping windows at 200 Hz from 500 Hz
  recordings. Distributed processing selects 19 channels in order, resamples to
  200 Hz, multiplies by 1e6 and applies a 0.1 Hz high-pass filter. Export adds no
  signal processing. Earlier owner/acquisition processing is retained.
- **Split:** train subjects `00`-`27`, then validation `28`-`31`; test `32`-`35`.
  No participant or exact signal case crosses the resulting split.
- **Sensors in array order:** Fp1, Fp2, F3, F4, F7, F8, T3, T4, C3, C4, T5, T6,
  P3, P4, O1, O2, Fz, Cz, Pz. All distributed channel kinds are EEG; XYZ positions
  are unknown.
- **Relationship to former EEGMAT export:** it used the same original PhysioNet
  recordings with 500 Hz/two-second windows and a different split/selection.
  That duplicate local export was removed; `MentalArithmetic` is the retained
  copy and follows OpenEEGBench's 200 Hz/five-second preparation.
- **Licence / paper:** [ODC Attribution 1.0 data terms](https://physionet.org/content/eegmat/view-license/1.0.0/).
  Zyma et al. (2019), *Electroencephalograms during Mental Arithmetic Task
  Performance*, Data 4(1), 14. [DOI](https://doi.org/10.3390/data4010014).

## ImaginedCommands

- **Original source / other names:** *2020 International BCI Competition, Track
  3*, [OSF project](https://osf.io/pq7vb/); NEMAR `nm000113`, OpenEEGBench
  `bcic2020-3`.
- **Processed source:** [braindecode/bcic2020-3](https://huggingface.co/datasets/braindecode/bcic2020-3/tree/8e2addefed44280be79b0c29bb09cc4c723cf18d),
  revision `8e2addefed44280be79b0c29bb09cc4c723cf18d`.
- **Task / dimensions:** imagined speech of five commands; 15 participants and
  45 recordings; train `(5250, 64, 600)`, test `(750, 64, 600)`. Labels `0 = Hello`,
  `1 = Help me`, `2 = Stop`, `3 = Thank you`, `4 = Yes`. Every class has 1050
  training and 150 test cases.
- **Derivation:** three-second trials at 200 Hz, source 256 Hz; distributed
  resampling, multiplication by 1e6 and 0.1 Hz high-pass filtering. Earlier BIDS
  conversion concatenated original MATLAB trials, so processed sample coordinates
  do not represent original acquisition timestamps.
- **Split:** run `00` (4500 cases) followed by run `01` (750 cases) forms training;
  run `02` (750 cases) is test. All 15 people intentionally appear in both sets.
  This is a within-subject run protocol, not subject-independent evaluation. No
  exact signal case crosses train/test.
- **Sensors in array order:** Fp1, Fp2, F7, F3, Fz, F4, F8, FC5, FC1, FC2, FC6,
  T7, C3, Cz, C4, T8, TP9, CP5, CP1, CP2, CP6, TP10, P7, P3, Pz, P4, P8, PO9,
  O1, Oz, O2, PO10, AF7, AF3, AF4, AF8, F5, F1, F2, F6, FT9, FT7, FC3, FC4,
  FT8, FT10, C5, C1, C2, C6, TP7, CP3, CPz, CP4, TP8, P5, P1, P2, P6, PO7,
  PO3, POz, PO4, PO8. All are distributed as EEG; positions unknown.
- **Licence / paper:** the [OSF metadata](https://api.osf.io/v2/nodes/pq7vb/) links
  its [CC BY 4.0 licence](https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e96a/).
  Jeong et al. (2022), *2020 International brain-computer interface competition:
  A review*, Frontiers in Human Neuroscience 16, 898300, Data Set-C.
  [DOI](https://doi.org/10.3389/fnhum.2022.898300).

## ChildhoodSeizures

- **Original source / other names:** [CHB-MIT Scalp EEG Database v1.0.0](https://physionet.org/content/chbmit/1.0.0/),
  Children's Hospital Boston/MIT; [DOI 10.13026/C2K01R](https://doi.org/10.13026/C2K01R);
  OpenEEGBench `chbmit`.
- **Processed source:** [braindecode/chbmit](https://huggingface.co/datasets/braindecode/chbmit/tree/3c7fc5537fb22686b2aafa8eb1a30d292c4464ab),
  revision `3c7fc5537fb22686b2aafa8eb1a30d292c4464ab`.
- **Task / dimensions:** seizure versus background; 22 people represented by 23
  case IDs and 661 recordings; train `(34045, 17, 2000)`, test `(2140, 17, 2000)`.
  Labels `0 = seizure`, `1 = background`; counts 852/33193 in training, 22/2118 in test.
- **Derivation:** ten-second windows at 200 Hz, source-reported 256 Hz; distributed
  selection/renaming of 17 bipolar derivations, resampling, multiplication by 1e6,
  and 0.1 Hz high-pass filtering. Nominal strides are ten seconds for seizure and
  100 seconds for background. End-window handling retains 125 adjacent overlapping
  window pairs within recordings; these remain as supplied.
- **Split:** train `chb01`-`chb19`, then validation `chb20`/`chb21`; test `chb22`/
  `chb23`. `chb21` is the same person as `chb01`; both are in merged training.
  Rows preserve case IDs and provide normalized participant IDs. `chb24` and its
  861 windows are excluded by OpenEEGBench's masks. No known person or exact
  signal case crosses train/test.
- **Sensors:** array order and original derivations are below. Names are upstream
  renamings, including the unexpected `F7-T7` to `T8` mapping; they must not be
  interpreted as monopolar electrodes at the named sites. No positions are invented.

| Array index | Distributed name | Original bipolar derivation |
|---|---|---|
| 0 | AF7 | Fp1-F7 |
| 1 | T8 | F7-T7 |
| 2 | TP7 | T7-P7 |
| 3 | PO7 | P7-O1 |
| 4 | AF3 | Fp1-F3 |
| 5 | C4 | F3-C3 |
| 6 | CP3 | C3-P3 |
| 7 | PO3 | P3-O1 |
| 8 | C2 | Fz-Cz |
| 9 | CPz | Cz-Pz |
| 10 | AF4 | Fp2-F4 |
| 11 | FC4 | F4-C4 |
| 12 | CP4 | C4-P4 |
| 13 | PO4 | P4-O2 |
| 14 | AF8 | Fp2-F8 |
| 15 | FT8 | F8-T8 |
| 16 | PO8 | P8-O2 |

- **Licence / references:** [ODC Attribution 1.0 data terms](https://physionet.org/content/chbmit/view-license/1.0.0/).
  Guttag (2010), *CHB-MIT Scalp EEG Database*; Shoeb (2009), *Application of Machine
  Learning to Epileptic Seizure Onset Detection and Treatment*, MIT PhD thesis
  ([source](https://hdl.handle.net/1721.1/54669)).

## Excluded: Depression

Depression (`mdd_mumtaz2016`, formerly `MDDMumtaz2016`) was removed from the
local archive and download/export choices after finding exact source signals
across train/test: 121 distinct windows, affecting 726 training and 484 test
cases. Its prepared arrays and quarantined `.ts` files have been deleted.
Only small diagnostic reports and source metadata remain locally. See the
[upstream issue draft and reproduction](issues/mdd-duplicate-windows.md).

## Metadata limits and deferred candidate

None of these releases provides explicit session IDs or usable stored XYZ
positions. Distributed epoch indices and processed-recording sample bounds are
retained, but generally cannot be translated into original acquisition trial IDs
or exact original sample indices. Original frequencies recovered from separate
BIDS sidecars are distinguished from publication reports. No synthetic montage or channel order is invented.

FACED is now prepared locally as **VideoEmotions**, with eight observed classes
despite the source nine-class declaration (Neutral, label 4, is missing). Its
release-review limitations are retained in the sidecars. See the
[current preparation details](openeegbench-local-preparations.md).
SEED-V was not downloaded. The initial audit is retained in the
[completeness report](openeegbench-results.md) and
[reproducible import guide](openeegbench-import.md).
