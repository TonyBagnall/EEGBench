# NBackAudioCondition: provenance and preparation

Data attributed to **Christoph Tremmel**. **More information to follow.**

The archive preparation is `D:/Data/EEG/NBackAudioCondition/`, the 41st registered
problem. It uses the source `ClassificationData.txt` below, not the reduced labels
in the old NBack `.ts` files. The source is pinned by SHA-256 in its manifest,
and the converter is retained in its `conversion_code/` folder.

## Joint classification task

The twelve labels combine three N-back levels (0, 1, 2) and four audio conditions
(0, 1, 2, 3). The original code is retained: `10 * audio_condition + nback_level`,
giving `0,1,2,10,11,12,20,21,22,30,31,32`. Audio descriptions are pending. These
are recorded experimental conditions, not noise added during conversion.

The source has 18,000 cases, 1,500 per joint class. Excluding participants 10 and
16 leaves 16,560 cases, 1,380 per class. The preserved split uses one-based
participant block IDs:

- Training: `1,3,4,5,6,7,8,11,12,13,17,20,21,22,23,24`; 11,520 cases, 960 per class.
- Test: `2,9,14,15,18,19,25`; 5,040 cases, 420 per class.
- Excluded: `10,16`; scientific reason to follow.

Each case has 16 channels and 600 timepoints at **200 Hz**, a **3-second** window.
The archive owner confirmed the recording sampling frequency on 9 November 2026;
it is not embedded in the supplied signal text. No resampling was required.
Signal decimal tokens and channel
order are preserved. No filtering, resampling, scaling or numeric rounding is
added. Stray NUL bytes are removed from the representation and the three-field
label segment is replaced by its unchanged combined code. Source order within
each partition is retained. There is no archived validation partition.

## Metadata and validation

`cases_train.tsv` and `cases_test.tsv` align with their respective `.ts` files;
`NBackAudioCondition_rows.tsv` concatenates TRAIN then TEST. Read identifiers as
strings. `row` is zero-based within split. Source-row and within-subject trial
indices are zero-based local indices, not recovered acquisition trial IDs. The
original N-back, audio and combined labels are retained.

The archive owner confirmed contiguous 720-row participant blocks and exclusions
on 4 November 2026. Dimensions, values and label distributions are directly
recovered from the supplied file. Attribution to Christoph Tremmel is supplied by
the archive owner. Recording sampling frequency is owner-confirmed as 200 Hz.
Sessions, recording/run IDs, original trial
IDs and recording sample/time bounds are unknown. Sensor names, units,
montage/reference and original preprocessing are also unknown. `channels.tsv`
lists array positions with blank names; EEG type comes from the earlier formatter,
not independent acquisition metadata. Anatomical channel-order consistency and
recording-interval overlap cannot be established.

Publication, DOI, public source URL, data licence and audio-condition descriptions
are pending. This local preparation does not establish redistribution permission.

Conversion checks cover every case's dimensions, per-person class counts, exact
float64 signal hashes on full `.ts` readback, case/label alignment, string IDs,
subject separation and exact signal duplicates across TRAIN/TEST. An aeon
load/fit/predict check uses representatives of all twelve classes. These are
compatibility checks, not benchmark scores. See local validation JSON and manifest.

```powershell
python -m tools.prepare_nback --source C:/Data/ChristophEEG/ClassificationData/ClassificationData.txt --output D:/Data/EEG
```

The converter refuses to overwrite existing output and publishes a staged folder
only when validation passes. Existing source files and benchmark results remain.

## Earlier preparations

The existing subject-disjoint preparation is at `C:/Data/ChristophEEG/NBack/`,
with `NBack_TRAIN.ts` and `NBack_TEST.ts`. It was outside the inspected
`D:/Data/EEG/` archive, so it was absent from the earlier 40-problem registry.

Its local formatter, `C:/Data/ChristophEEG/format_nback.py`, describes a
three-class N-Back working-memory task (levels 0, 1, 2), 16 channels and 600
points per case. It reads `ClassificationData/ClassificationData.txt`, assumes
25 contiguous participant blocks of 720 trials, excludes participants 10 and 16,
and assigns 16 remaining people to training and seven to test: 11,520 / 5,040 cases.
The archive owner has now confirmed the participant blocks and exclusions. Original
acquisition identifiers are unavailable; block numbers are retained transparently.

`NBackR` contains a random trial split of the same eligible source cases, allowing
participants on both sides. `NBack_Noise0`–`NBack_Noise3` filter the four noise
conditions. The corresponding `NBackR_Noise*` folders apply random trial splits
to those subsets. They are preparations of one source collection, not ten
independent recording collections. `format_nback_random.py` documents that split.

The older `C:/Code/aeon-neuro/aeon_neuro/datasets/classification_datasets.py`
also lists `N_Back` among 31 candidates. Its record key 49 is explicitly a
placeholder, not a confirmed Zenodo release. The original study, source licence,
and sensor identities were not established by that historical location check;
the archive owner subsequently confirmed 200 Hz on 9 November 2026. The original
files remain in place; the joint task is now prepared
separately in the archive as described above.
