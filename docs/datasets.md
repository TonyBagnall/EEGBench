# Datasets

The archive is the 30 EEG classification problems of Table 1 in
[Time Series Machine Learning for Classifying Electroencephalograms](https://data.mlr.press/assets/pdf/v03-8.pdf).
Six come from the UEA multivariate archive, the rest were collated for the paper. The
data are taken as their owners presented them, with no preprocessing added.

The archive is a sub-collection of the
[Multiverse](https://github.com/aeon-toolkit/multiverse) archive for multivariate time
series classification, and some of these datasets are also in its benchmark subset,
Multiverse-core.

<!-- DATASETS:START -->
| Dataset | Domain | Channels | Length | Classes | Subjects | Train | Test | Hz | Open |
|---|---|---|---|---|---|---|---|---|---|
| Alzheimers | Med | 19 | 30000 | 3 | 88 | 45 | 43 | 500 | yes |
| Blink | BCI | 4 | 510 | 2 | &mdash; | 500 | 450 | 255 | yes |
| ButtonPress | BCI | 32 | 1000 | 2 | 1 | 120 | 120 | 1000 | yes |
| EpilepticSeizures | Med | 1 | 178 | 2 | &mdash; | 80 | 11420 | 178 | yes |
| EyesOpenShut | BCI | 14 | 128 | 2 | &mdash; | 56 | 42 | 128 | yes |
| FaceDetection | Psy | 144 | 62 | 2 | &mdash; | 5890 | 3524 | 250 | yes |
| FeedbackButton | Psy | 61 | 450 | 2 | 57 | 1700 | 1150 | 500 | yes |
| FeetHands | BCI | 64 | 640 | 2 | 105 | 2835 | 1890 | 160 | yes |
| FibroLiverpool | Med | 64 | 15360 | 2 | 36 | 15 | 21 | 512 | no |
| FibroUEA | Med | 64 | 15000 | 2 | 41 | 17 | 23 | 500 | no |
| FingerMovements | BCI | 28 | 400 | 2 | &mdash; | 316 | 100 | 128 | yes |
| HandMovementDirection | BCI | 10 | 400 | 4 | &mdash; | 160 | 74 | 400 | yes |
| ImaginedFeetHands | BCI | 64 | 640 | 2 | 105 | 2835 | 1935 | 160 | yes |
| ImaginedOpenCloseFist | BCI | 64 | 640 | 2 | 105 | 2835 | 1890 | 160 | yes |
| InnerSpeech | BCI | 128 | 3584 | 4 | 9 | 250 | 200 | 1024 | yes |
| LongIntervalTask | Med | 63 | 4750 | 2 | 139 | 1660 | 1120 | 500 | yes |
| LowCost | BCI | 15 | 375 | 2 | 10 | 600 | 600 | 125 | yes |
| MatchingPennies | Psy | 10 | 10000 | 2 | 7 | 700 | 700 | 5000 | yes |
| MindReading | BCI | 204 | 200 | 5 | &mdash; | 727 | 653 | 200 | yes |
| MotorImagery | BCI | 64 | 3000 | 2 | &mdash; | 278 | 100 | 1000 | yes |
| OpenCloseFist | BCI | 64 | 640 | 2 | 105 | 2835 | 1890 | 160 | yes |
| PhotoStimulation | Med | 19 | 9000 | 3 | 73 | 37 | 36 | 500 | yes |
| PronouncedSpeech | BCI | 128 | 3584 | 4 | 9 | 250 | 200 | 1024 | yes |
| SelfRegulationSCP1 | BCI | 6 | 896 | 2 | &mdash; | 268 | 293 | 256 | yes |
| SelfRegulationSCP2 | BCI | 7 | 1152 | 2 | &mdash; | 200 | 180 | 256 | yes |
| ShortIntervalTask | Med | 63 | 2750 | 2 | 139 | 1660 | 1120 | 500 | yes |
| SitStand | BCI | 17 | 1250 | 4 | 32 | 3200 | 3200 | 250 | yes |
| Sleep | Psy | 1 | 178 | 5 | 82 | 2394 | 1205 | 100 | yes |
| SongFamiliarity | Psy | 32 | 3000 | 2 | 29 | 700 | 750 | 1000 | yes |
| VisualSpeech | BCI | 128 | 3584 | 4 | 9 | 250 | 200 | 1024 | yes |
<!-- DATASETS:END -->

Domain is medical (Med), brain-computer interface (BCI) or psychology (Psy). Subjects is
blank where the source does not record it. MindReading is MEG rather than EEG. The table
is written from `eegbench.datasets.metadata()` when the leaderboards are rebuilt.

## Lists

```python
from eegbench.datasets import eegbench, eegbench_open, by_domain, metadata

len(eegbench)        # 30, the whole archive
len(eegbench_open)   # 28, the ones anyone can download
by_domain("Med")     # the 7 medical problems
metadata()           # the table above as a DataFrame
```

`eegbench_open` is the same list as `aeon.datasets.tsc_datasets.eeg2026`. The two left
out, FibroLiverpool and FibroUEA, are not fully open access; contact Tony Bagnall for
access for research. Results for them are still on the leaderboard.

## Downloading and loading

The open datasets are on Zenodo in the
[tsml community](https://zenodo.org/communities/tsml/) and are fetched and cached by
aeon:

```python
from aeon.datasets import load_classification

X_train, y_train = load_classification("Blink", split="train")
X_test, y_test = load_classification("Blink", split="test")
```

`X` has shape `(n_cases, n_channels, n_timepoints)`. Some of these are large:
Alzheimers is 19 channels of 30,000 points a case.

## The train and test split

Every dataset has a default split, and the leaderboard uses only that.

- Where there are several subjects, no subject has cases on both sides. A classifier
  that learns to recognise a subject or a recording session, rather than the class, gets
  no credit for it.
- Where there is a single subject, the split is by recording session.
- Where there are several subjects, an ancillary file gives the subject index of each
  case.

This is why results here are not resampled. A random or class-stratified resample puts
the same subject in train and test, and scores on it are not comparable to the ones
here. Resampling that keeps subjects together needs the subject index, and is not yet
part of this repository.
