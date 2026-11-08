# BCI IV 2a, ISRUC-Sleep and FACED local preparations

These candidates have been prepared and validated separately from the published 30-problem benchmark,
using the pinned OpenEEGBench releases in [the collection review](openeegbench-review.md).
The requested destination layout is:

| Source | Local folder / problem name | Train cases | Test cases | Channels | Length | Classes |
|---|---|---:|---:|---:|---:|---:|
| BCI Competition IV 2a | `D:/Data/EEG/ImaginedHandFeetTongue/` | 3456 | 1728 | 22 | 800 | 4 |
| ISRUC-Sleep | `D:/Data/EEG/ClinicalSleepStages/` | 64889 | 8803 | 6 | 6000 | 5 |
| FACED | `D:/Data/EEG/VideoEmotions/` | 15629 | 3588 | 25 | 2000 | 8 observed |

The original three preparations passed full float32 `.ts` readback, source case
alignment, subject separation, cross-split duplicate checks and bounded aeon
load/fit/predict checks. The final source comparison also verified all class
counts, participant IDs, row indices, sensor sidecars and sparse FACED labels.
The standalone importer/exporter test suite passed 23 tests.

The following size table describes the original preparation, before the local F8 removal.

| Dataset | Train cases | Test cases | Subjects | Channels | Timepoints | Classes | Frequency | Size GB | Licence / release status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ImaginedHandFeetTongue | 3456 | 1728 | 9 | 22 | 800 | 4 | 200 | 1.055 | CC BY-ND 4.0; local research preparation |
| ClinicalSleepStages | 64889 | 8803 | 82 | 6 | 6000 | 5 | 200 | 30.487 | Research access; redistribution unverified |
| VideoEmotions | 15629 | 3588 | 123 | 26 | 2000 | 8 | 200 | 11.511 | CC BY 4.0 corroborated; local release review retained |

Sizes are complete exported folders in decimal GB, including sidecars and source
evidence; they exclude the intermediate HDF5 copies. See also the
[machine-readable results](openeegbench-local-results.json).

The current VideoEmotions export has 25 channels after removal of F8 (original index 6), with no gain. Current shapes, sizes, hashes and validation are recorded in its local manifest and [signal correction results](signal-cleanup-results.json). See [local corrections](local-data-corrections.md).

All are at 200 Hz. Original training is followed by original validation, in
source recording/case order. The original test partition is retained. Classifier
validation is left to the fitted estimator.

Each completed folder contains `<Name>_TRAIN.ts`, `<Name>_TEST.ts`,
`<Name>_rows.tsv`, `<Name>_metadata.json`, `channels.txt`, Parquet case tables,
source metadata, attribution, conversion code, validation and a manifest. Read
case identifiers as strings. Case row order is TRAIN followed by TEST, with
zero-based row indices within each split. Numeric values retain upstream
microvolt scaling; serialized MNE unit tags can still say V and are preserved as
source evidence.

ISRUC's complete signal arrays occupy 10.61 GB (9.88 GiB) as float32: 9.34 GB
training and 1.27 GB test. Typical aeon `.ts` loading produces float64 arrays,
requiring about 21.22 GB for the signals, plus loading overhead and estimator
working memory. The intermediate HDF5 preparation supports reading subsets.

## Metadata completeness

Available case counts are shown below. All cases retain class codes, recovered
class names, original train/validation/test membership and ordered sensor types.

| Dataset | Subject | Session | Run | Recording ID | Source path/file | Source epoch index | Original video/trial ID | Processed sample bounds | Acquisition sample bounds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ImaginedHandFeetTongue | 5184 | 5184 | 5184 | 5184 | 0 | 5184 | 0 | 5184 | 0 |
| ClinicalSleepStages | 73692 | 0 | 0 | 73692 | 73692 | 73692 | 0 | 73692 | 0 |
| FACED | 19217 | 0 | 0 | 19217 | 19217 | 19217 | 19217 | 19217 | 0 |

Zero means unavailable in the distributed case metadata, rather than proof that
no session/run existed. FACED's original sampling frequencies are matched to BIDS
sidecars for all cases. BCI IV 2a's 250 Hz and ISRUC's 200 Hz acquisition rates are
source-reported. All 108 BCI source groups contain serialized sensor coordinates;
these are retained as stored MNE Info, without claiming they are independently
verified digitized acquisition positions. ISRUC and FACED have no usable stored
XYZ coordinates. No montage or synthetic positions were added by this converter.

## Task definitions and interpretation

ImaginedHandFeetTongue classifies four imagined movements: feet=0, left hand=1, right hand=2,
tongue=3. Four-second epochs contain 22 EEG channels. Subjects 1–6 are training,
subjects 7–9 test; original session and run identifiers remain in the case table.
The original source has 22 EEG and three EOG channels; EOG was excluded upstream.

ClinicalSleepStages classifies 30-second epochs as W=0, N1=1, N2=2, N3=3, REM=4. The fixed
protocol retains 82 cohort-I participants: 72 training, 10 test. The exported
channel names restore the true derivations in unchanged array order:
`C3-M2, C4-M1, F3-M2, F4-M1, O1-M2, O2-M1`. Upstream names
`O1, O2, AF8, P8, PO10, PO9` remain in `distributed_channel_names` and each
sensor's `distributed_name`. These are label corrections, not signal changes or
channel reordering. Second-scorer labels are preserved where distributed.

FACED classifies video-elicited emotions. This exact pinned preparation contains
Anger=0, Disgust=1, Fear=2, Sadness=3, Amusement=5, Inspiration=6, Joy=7,
Tenderness=8. Neutral=4 is absent upstream. The `.ts` header lists the eight
observed labels, preserving their original codes; no neutral examples are
invented and labels are not collapsed to 0–7. Original declared class count,
observed values and the full source label mapping are recorded separately.
Each case has 26 EEG channels and a ten-second window. Source video IDs remain
in the case table.

## Local use and release status

The user authorized these local research preparations. `LOCAL_RESEARCH_ONLY.txt`
and the source notices accompany each folder. Preparation does not grant public
redistribution permission. BCI IV 2a is CC BY-ND 4.0 and the redistributed upstream
filtering/resampling/cropping needs review. ISRUC's original site provides research
access but no verified redistribution grant. FACED has CC BY 4.0 corroboration in
a paper coauthored by original dataset researchers, while its original Synapse
terms remain a release-review item. No Zenodo upload is part of this work.

## Reproduction

Use the standalone tools from the repository root with the data-import environment:

```powershell
python -m tools.openeegbench.prepare convert --dataset bcic2a --cache .openeegbench/review-source --output D:/Data/EEG/.openeegbench-final-preparation
python -m tools.openeegbench.prepare convert --dataset isruc-sleep --cache .openeegbench/review-source --output D:/Data/EEG/.openeegbench-final-preparation
python -m tools.openeegbench.prepare convert --dataset faced --output D:/Data/EEG/.openeegbench-final-preparation
python -m tools.openeegbench.export_local --source D:/Data/EEG/.openeegbench-final-preparation --dataset bcic2a --destination D:/Data/EEG
python -m tools.openeegbench.export_local --source D:/Data/EEG/.openeegbench-final-preparation --dataset isruc-sleep --destination D:/Data/EEG
python -m tools.openeegbench.export_local --source D:/Data/EEG/.openeegbench-final-preparation --dataset faced --destination D:/Data/EEG
```

Completed folders are not overwritten. Interrupted conversion can use `--resume`
with the same converter, registry and source revisions. Each exported case is
read back and compared to its float32 HDF5 source; source case hashes, split
membership, class counts, subject separation and cross-split duplicates are
checked. A bounded aeon load/fit/predict check confirms format compatibility.
