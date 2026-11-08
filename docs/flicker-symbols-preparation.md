# FlickerSymbols: Wang2016 attended visual targets

FlickerSymbols predicts which of **40 frequency/phase-coded visual targets** a
participant is attending. It is a separate study from FlickerAttention and
CodedSymbols. The original Tsinghua SSVEP Benchmark has 35 participants, one
documented session each and six blocks of 40 trials: 8400 cases in total.

Source: Wang, Chen, Gao and Gao, *A Benchmark Dataset for SSVEP-Based
Brain–Computer Interfaces*, IEEE Transactions on Neural Systems and
Rehabilitation Engineering 25(10), 1746–1752 (online 2016; print 2017),
[DOI 10.1109/TNSRE.2016.2627556](https://doi.org/10.1109/TNSRE.2016.2627556).
The [original laboratory release](https://bci.med.tsinghua.edu.cn/download.html)
provides the channel locations, participant roster and frequency/phase map.
EEG MATLAB files come from the checksum-pinned
[Zenodo record 14865172](https://zenodo.org/records/14865172).

The Zenodo data record explicitly declares **CC BY 4.0**, corroborated by the
versioned NEMAR dataset description. The original laboratory README does not
contain an explicit licence grant. That distinction is preserved in the
sidecars: this is a local research preparation, with applicability of the
original grant to redistribution retained as a release-review item. This is
data-specific evidence, independent of MOABB's software licence. The NEMAR
derivative reports 34 participants; it is not the signal source for this export.

## Representation and fixed split

Each native epoch has **64 channels × 1500 points at 250 Hz**. Acquisition was
at 1000 Hz; the source extracted six-second epochs and downsampled to 250 Hz.
Epochs extend from 0.5 seconds before stimulation to 5.5 seconds after onset,
including five seconds of flicker. The original amplifier passband was
0.15–200 Hz with a 50 Hz acquisition notch. The reported reference is the vertex.

The numeric values are retained in **microvolt scale**. This interpretation
comes from the pinned MOABB loader's conversion to MNE volts, not an embedded
unit attribute in the MATLAB array. No additional filtering, mean subtraction,
reference change, scaling, cropping or resampling is performed. This differs
from the MOABB adapter, which demeans epochs, constructs synthetic continuous
data and normally selects a shorter stimulation interval.

Source float64 values are written using their shortest exact decimal
representation, preserving the original binary64 values on readback. All 40
original target indices, **1–40**, remain labels. The sidecar maps them to the
source frequency and phase. Actual keyboard character identities are not
invented from the target index.

There is no official fixed subject split. This preparation uses:

- **TRAIN:** participants `01`–`06` and `09`–`28`: 26 people, 6240 cases,
  156 cases per class. Six experienced and 20 novice participants.
- **TEST:** participants `07`, `08`, `29`–`35`: nine people, 2160 cases,
  54 cases per class. Two experienced and seven novice participants.

Subjects are disjoint. All six blocks remain with their participant. This
differs from the original within-subject block evaluation. There is no archived
validation partition. Cases follow ascending participant, original target
index, then original block index, matching the pinned loader's source indexing.
The original random presentation chronology within blocks is not recoverable
from the target-indexed MATLAB arrays.

## Sensors and metadata

The original `64-channels.loc` lists every sensor in array order. Its index
sequence is checked against all 64 array axes; names and order are preserved,
including uppercase source spelling. **CB1 and CB2 are retained under their
original names**; no unconfirmed P9/P10 aliases are introduced. The original
polar coordinates are preserved rather than replaced by invented individual
3D positions. A common external source montage describes all participant arrays;
the MATLAB signal files do not embed separate per-participant sensor names.

Each case table records a string participant ID, source filename, target and
block indices, exact MATLAB indexing expression, label, frequency, phase,
epoch-local boundaries, stimulus-relative times and a float64 signal hash.
Session `0` denotes the one documented acquisition session; its evidence is
explicitly recorded. Original dates/session IDs, continuous-recording sample
offsets and within-block trial chronology remain unknown. The original
participant roster, including age, gender, handedness and experience group,
is retained under `source_metadata/`.

## Implementation and checks

The standalone adapter is [prepare_wang.py](../tools/prepare_wang.py), with
[tests](../tools/test_prepare_wang.py). It pins MOABB commit
`bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`, the complete Zenodo file checksum
roster, the original frequency/phase map, channel file, README and versioned
NEMAR metadata. Downloads are bounded to four concurrent participant files;
verified temporary MATLAB cache files are removed after conversion unless
`--keep-source` is specified. Remote URLs, byte sizes, MD5 and SHA256 remain in
the manifest for redownload.

A two-person pilot was completed first: 480 cases, all 40 classes, exact
float64 readback, aligned metadata, no duplicates, no tiny/constant channels
and an aeon load/fit/predict check covering every class. The full preparation
performs the same checks across every case, plus subject separation and
cross-partition duplicates. Expected combined signal memory is 6.45 GB as
float64; decimal text is larger.

Run from the repository with the data-import dependencies installed:

```powershell
python -m tools.prepare_wang --output D:/Data/EEG --cache C:/Code/EEGBench/.openeegbench/wang2016
```

The active destination is `D:/Data/EEG/FlickerSymbols/`, with two `.ts` files,
aligned `cases_train.tsv` / `cases_test.tsv`, metadata, validation, ordered
sensor tables, source evidence, attribution, conversion code and a manifest.
Read all case identifiers as strings. Full preparation passed. Measured folder size is **15.292 GB**.
See [machine-readable results](flicker-symbols-local-results.json).
