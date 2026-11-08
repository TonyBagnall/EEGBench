# ImaginedGripForce

Prepared 5 November 2026 in `D:/Data/EEG/ImaginedGripForce/`. Original files are
cached separately in `D:/Data/EEGSources/MartinezPeon2024/`.

Predict **imagined right-hand squeezing at 10%, 40% or 70% of maximum voluntary
contraction**. Participants imagine the sensations of squeezing a ball, rather
than actually producing the labelled force. All three available force levels
are retained. A separately marked rest/basal class is not available.

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ImaginedGripForce | 240 | 60 | 10 | 14 | 640 | 3 | 128 | 0.02668 | CC BY 4.0 |

The size includes `.ts`, compressed intermediate arrays and sidecars. The two
`.ts` files total **21.30 MB**; source text files total **47.69 MB**. Each class
has 80 training and 20 test cases. Measured results and validation are in
[imagined-grip-force-local-results.json](imagined-grip-force-local-results.json).

## Provenance and permission

- Original name / MOABB loader: **EEG Kinesthetic motor imagery levels /
  MartinezPeon2024**.
- Author: **Dulce Martinez-Peon**.
- Original source: [Figshare article 25773342, version 1](https://doi.org/10.6084/m9.figshare.25773342.v1).
- Reference: Martinez-Peon, Garcia-Hernandez, Benavides-Bravo and Parra-Vega
  (2024), *Characterization and classification of kinesthetic motor imagery
  levels*, Journal of Neural Engineering 21, 046024,
  [DOI 10.1088/1741-2552/ad5f27](https://doi.org/10.1088/1741-2552/ad5f27).
- **Data licence:** CC BY 4.0, directly checked through the original
  [versioned Figshare metadata API](https://api.figshare.com/v2/articles/25773342/versions/1),
  applicable to the dataset release. Attribution and changes are recorded in
  `ATTRIBUTION.txt`; MOABB software licensing is not used as the data grant.
- [Pinned source lock](imagined-grip-force-source-lock.json) lists all 60 files,
  their IDs, URLs, sizes and publisher MD5 values. Local receipts add SHA256.
- Loader evidence is pinned to MOABB commit
  [`bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`](https://github.com/NeuroTechX/moabb/blob/bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5/moabb/datasets/martinezpeon2024.py).

## Subjects, recordings, channels and timing

Ten original participant IDs `001`-`010` are preserved as strings. The documented
protocol has one session per participant. Each has six source files: three force
levels, two attempts each. Five cues per file give 30 trials per participant,
300 overall and 60 recording files. Session `0` is archive assigned; run IDs
derive from the filename, and trial IDs are cue indices.

Each native text table has 23 numerical columns without column headers. Source
EEG columns **2-15 inclusive (zero-based)** are selected in their original order:

`AF3, F7, F3, FC5, T7, P7, O1, O2, P8, T8, FC6, F4, F8, AF4`.

These names and their EEG interpretation are **documented source/loader mapping**,
not labels embedded in the files. All 60 files passed numerical column/schema
checks; the absence of embedded sensor labels prevents an independent per-file
sensor identity check. Other columns contain time-like fields, a wrapping sample
counter, gyroscope values and unused values; they are excluded from EEG arrays.
No individual sensor positions are available and no template positions are invented.
P3/P4 reference locations are reported by the publication as quoted in the loader,
rather than directly recovered from a file header.

Cues at `2.9, 10.9, 18.9, 26.9, 34.9` seconds are **inferred from the fixed protocol**,
relative to source row zero, following the pinned loader's approach. They are not
recorded trigger timestamps. At 128 Hz, rounded starts are
`371, 1395, 2419, 3443, 4467`; each crop has 640 samples and an exclusive end.
The recorded time-column and sample-counter values at each crop's endpoints are
preserved separately, without treating them as absolute acquisition times or
silently aligning the inferred cues to them. Windows do not overlap.

## Conversion, splitting and checks

[Standalone converter](../tools/prepare_imagined_grip_force.py): select source
EEG columns, crop five protocol-derived windows and export **float64 microvolts**.
The source values already have microvolt scale, including large DC offsets;
no extra multiplication, filtering, resampling, demeaning or rereferencing is
applied. The paper's reported 60 Hz notch is not applied locally or asserted
to be present in the distributed numerical values.

No official partition is supplied. The fixed split is original participants
`001`-`008` TRAIN and `009`-`010` TEST. Cases follow participant, numeric force
level, attempt, then cue order. Original partition is `unsplit`; there is no
archived validation split. Filename force labels `10/40/70` encode as `1/2/3`.

Both `.ts` files passed complete readback against float64 signal hashes and
ordered case metadata. All 300 cases and all 4200 case/channel pairs are finite;
none are constant or have standard deviation at/below `1e-7` microvolts. No
channels were removed. No duplicate cases, shared participants or overlapping
recording intervals cross partitions; no within-partition duplicates were found.
Both full partitions loaded with aeon, passed its variance check and were used
in a SummaryClassifier fit/predict compatibility check. This is not a benchmark result.

Four adapter tests cover native EEG versus auxiliary selection, cue rounding,
leading-zero IDs, malformed source schemas and incomplete-epoch rejection.
Together with shared adapter and registry tests, **14 tests passed**.

Sidecars include ordered `cases_train.tsv` / `cases_test.tsv`, `channels.tsv`,
dataset metadata, metadata completeness, validation, source evidence, attribution
and a manifest with artifact hashes. `classification_arrays.npz` uses NumPy
ZIP compression and contains `X_train, y_train, X_test, y_test, channel_names`;
X has `(cases, channels, timepoints)` order. Load with
`numpy.load(path, allow_pickle=False)`. The NPZ also passed exact readback.

To reproduce from the repository root with the scientific dependencies installed:

```powershell
python -m tools.prepare_imagined_grip_force --cache D:/Data/EEGSources/MartinezPeon2024 --output D:/Data/EEG
```

Use `--download-only` to cache/verify source files, or `--offline` to convert a
verified cache. Existing final problem folders are never overwritten. Generated
arrays and recordings are outside Git; the original 30 problems and their results
are unchanged. The registry now has 55 preparations and `eeg.txt` has 51.
