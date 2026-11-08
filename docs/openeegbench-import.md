# Importing candidates from OpenEEGBench

The [collection reassessment](openeegbench-review.md) reviews all twelve upstream
entries, including pinned BCI IV 2a and ISRUC metadata, FACED's missing Neutral
class, and new data-specific FACED licence evidence. Its findings supplement
the original five-candidate import audit below.

The standalone tools in [`tools/openeegbench`](../tools/openeegbench/prepare.py)
prepare candidate datasets for review. They do not add datasets to the 30-problem
archive, change results, or upload anything. See also the
[existing dataset provenance](dataset-provenance.md).

## Reproducible sources and licence review

The registry follows OpenEEGBench commit
[`3e4d034ae3e009deeda9c987d05a37e18fd87e15`](https://github.com/braindecode/OpenEEGBench/blob/3e4d034ae3e009deeda9c987d05a37e18fd87e15/open_eeg_bench/default_configs/datasets.py).
It pins the following Hugging Face commits, not `main`. The processed releases
are Zarr v3 `WindowsDataset` stores, not Hugging Face Arrow datasets; use the
importer rather than `datasets.load_dataset()`.

| Candidate / HF ID (prefix `braindecode/`) | Exact HF revision | Split unit; original train / validation / test | Data licence evidence |
|---|---|---|---|
| `arithmetic_zyma2019` | `8359206e7e1b3d1f068033348e291d6677be1920` | Subjects `00`-`27` / `28`-`31` / `32`-`35` | [PhysioNet EEGmat](https://physionet.org/content/eegmat/view-license/1.0.0/): ODC-By-1.0 |
| `bcic2020-3` | `8e2addefed44280be79b0c29bb09cc4c723cf18d` | Runs `00` / `01` / `02`, within subject | [Original OSF project](https://api.osf.io/v2/nodes/pq7vb/) links its [CC BY 4.0 licence](https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e96a/) |
| `chbmit` | `3c7fc5537fb22686b2aafa8eb1a30d292c4464ab` | Cases `chb01`-`chb19` / `chb20`,`chb21` / `chb22`,`chb23` | [PhysioNet CHB-MIT](https://physionet.org/content/chbmit/view-license/1.0.0/): ODC-By-1.0 |
| `faced` | `18c73355fc71c055e92828384da85bb49bc6e3c0` | Subjects `000`-`079` / `080`-`099` / `100`-`122` | [NEMAR derivative](https://github.com/nemarDatasets/nm000112/blob/2577b0bbc089b49e828cd98d80445133634b6d34/dataset_description.json) declares CC-BY-4.0; original Synapse terms remain unverified |
| `mdd_mumtaz2016` (excluded; audit only) | `53cd9de1af5f09209d8a0f4fe20aa325c6a5fedb` | Explicit subject lists in the registry | [Original Figshare v2 record](https://api.figshare.com/v2/articles/4244171/versions/2): CC BY 4.0 |

Reviewed 3 November 2026. The HF cards say `license: unknown`; OpenEEGBench's BSD
software licence is not used as data permission. ODC Attribution permits database
reuse and modification with its licence and attribution notices retained; its scope
is database rights and it does not grant unrelated rights in individual contents.
CC BY 4.0 permits sharing and adaptation subject to attribution, licence notices
and identification of modifications. The generated attribution file identifies
sources, citations, upstream processing and our format/split changes. Original
notices and metadata must accompany a future release.

The initial audit kept FACED **metadata-only** because the original Synapse
project/wiki/annotations did not establish redistribution terms. The later review
found a data-specific CC BY 4.0 statement in a paper coauthored by original FACED
researchers. The reviewed registry now permits the explicitly authorized local
research preparation, with release limitations retained in its sidecars. Video
stimuli are outside this import. SEED-V is not in the registry and cannot be selected.

The paragraph above records the original five-candidate audit. Following the
collection reassessment and explicit user authorization, BCI IV 2a, ISRUC-Sleep
and FACED now have reviewed **local research preparation** entries. These carry
source terms and redistribution limitations into their outputs; local preparation
does not approve publication. See [local preparation details and commands](openeegbench-local-preparations.md).
FACED's declared nine-class mapping is retained alongside its eight observed
labels, and its local export lists only the observed codes.

## Installation and commands

Run commands from the repository root, using a local virtual environment:

```powershell
python -m venv .openeegbench/venv
.openeegbench/venv/Scripts/python.exe -m pip install -e ".[data-import,test]"
.openeegbench/venv/Scripts/python.exe -m pytest tools/openeegbench eegbench -q
```

Use the appropriate environment activation or Python path on other platforms.
The run in this workspace used Python 3.12, aeon 1.4.0, NumPy 2.3.5, pandas
2.3.3, h5py 3.14.0 and PyArrow 24.0.0. The manifest records installed versions.

```powershell
# Inspect all distributed metadata and original-source sidecars, without EEG.
python -m tools.openeegbench.prepare inspect --dataset all

# First complete and validate the smallest dataset.
python -m tools.openeegbench.prepare convert --dataset arithmetic_zyma2019

# Then convert the other candidates with verified original-source terms.
python -m tools.openeegbench.prepare convert --dataset bcic2020-3
python -m tools.openeegbench.prepare convert --dataset chbmit

# Recheck output and run a bounded aeon classifier smoke test.
python -m tools.openeegbench.prepare validate --dataset arithmetic_zyma2019
python -m tools.openeegbench.prepare summary
python -m tools.openeegbench.report

# Export standard .ts arrays with accompanying metadata when required.
python -m tools.openeegbench.prepare export-ts --dataset arithmetic_zyma2019 --ts-output .openeegbench/ts

# Use the existing D:/Data/EEG/Name/Name_TRAIN.ts layout and named sidecars.
python -m tools.openeegbench.export_local --destination D:/Data/EEG
```

Set `--cache PATH` and `--output PATH` on any import command to use another local
directory or drive. Defaults are `.openeegbench/source` and
`.openeegbench/archive`. `.openeegbench/` is ignored by Git; custom output
locations should be outside the repository or explicitly ignored. Never commit
downloaded recordings or generated classification arrays.

Metadata downloads are cached and checksum verified. Signal chunks are downloaded
one at a time to temporary storage, verified against their HF SHA-256/git blob
hashes, decoded, written to the archive and removed. This avoids keeping a second
full signal copy. The source adapter accepts only the inspected float32,
little-endian, gzip Zarr schema and fails on missing chunks or unsupported codecs;
it does not silently fill missing chunks with zeros. No remote Python is executed.

Completed conversions are never overwritten. Downloads respect server retry
headers and back off on rate limits. Each completed recording has a checkpoint;
use the same command with `--resume` after an interruption. Resume requires the
same HF and converter revision. Cached metadata can be reused; choose a new
`--output` root if the converter has changed or an incomplete output predates
checkpoint support. A
`manifest.json` is written last as the successful completion marker. Do not use
`convert --dataset all` as an unattended batch: the local research candidates are
large and include separate redistribution review requirements. Individual commands
make preparation scope explicit.

## Stored format and ordering

Each successfully prepared dataset directory contains:

| File | Contents |
|---|---|
| `arrays.h5` | `X_train`, `y_train`, `X_test`, `y_test`; signals are losslessly gzip-compressed float32, labels int64 |
| `cases_train.parquet`, `cases_test.parquet` | One row per case, ordered exactly like the arrays; Zstandard compression; nullable string identifiers |
| `dataset.json` | Dimensions, frequencies, counts, ordered sensors, channel derivations, label definitions, preprocessing and provenance |
| `metadata-completeness.json` | Available/total counts for required case metadata fields |
| `validation.json` | Shapes, per-split class counts, subject overlap, cross-split duplicates and validation status |
| `aeon-smoke.json` | Compatibility test using a small class-balanced subset of actual converted signals |
| `source-chunks.json` | SHA-256 and byte count of each downloaded signal chunk |
| `checkpoint.json`, `progress/` | Recording completion checkpoints and per-recording case tables for interrupted downloads |
| `conversion_code/` | Exact converter and registry bytes used by this run |
| `source_metadata/` | Unmodified distributed sidecars, all recording-level serialized MNE Info and window tables, pinned original BIDS sidecars, licence evidence and upstream config/loader |
| `ATTRIBUTION.txt` | Source, citation, licence link and modification notice |
| `manifest.json` | HF/source pins, split definition, converter hashes, environment, artifact hashes and validation result |

Signal array shape is `(cases, channels, timepoints)`, directly usable by aeon.
`X_train` contains original **training followed by validation**; each retains the
order used by Braindecode: numeric `recording_N` order, then metadata row order.
`X_test` retains the original test order. `original_partition` records the original
assignment even after merging. There is no archived validation array. The
importer applies no normalization, resampling, filtering or channel changes.

```python
from tools.openeegbench.prepare import load_prepared
import pandas as pd

X_train, y_train, X_test, y_test = load_prepared(
    ".openeegbench/archive/arithmetic_zyma2019"
)
cases = pd.read_parquet(
    ".openeegbench/archive/arithmetic_zyma2019/cases_train.parquet"
)
assert len(cases) == len(X_train)
```

`load_prepared` materializes arrays. For larger problems, open `arrays.h5` with
h5py and access cases or batches. HDF5 chunks contain one case. File size in the
summary is the complete candidate directory in decimal GB, including metadata,
excluding cache and separately exported `.ts` files. `.ts` is deliberately a
separate export: text can be several times larger. It uses nine significant
digits, enough to round-trip float32 values, and does not include timestamps.
Channel names remain in JSON; case order remains in the accompanying Parquet
files. The export produces its own file hash manifest; `source-manifest.json`
preserves the HDF5 conversion manifest separately from the exported files.

## Metadata evidence and limitations

Serialized MNE Info is read directly from each Zarr recording group, without
constructing MNE/Braindecode objects or applying OpenEEGBench's synthetic standard
montage. It retains `chs`, FIFF sensor kinds, calibration, units, `loc`, coordinate
frames, `dig`, reference flags, projectors, bad channels and recording metadata.
Names, types, unit tags, sampling frequency and array channel count/order must
agree across every recording or conversion stops. Recording-specific positions
may differ and are retained separately. Unknown positions remain null.

CHB-MIT needs special interpretation: its distributed preprocessing selected 17
bipolar derivations, then renamed them with electrode-like names. For example,
`F7-T7` was renamed `T8`. The importer preserves that exact name and array order
and saves the inverse mapping as `source_derivation`; this is not an assertion
that the signal is a monopolar recording at T8. No standard positions are added.

The preprocessing log in the files records resampling to 200 Hz, multiplication
by 1e6 and high-pass filtering at 0.1 Hz, plus dataset-specific selection/renaming
and window definitions. Original MNE highpass/lowpass fields may also describe
earlier acquisition filters. Original unit tags can still say volts after
scaling; retain both the numeric scaling and unit tags. The converter does not
change the values to reconcile these descriptions.

For each case the output retains the complete distributed window row, its source
index, global index, recording group, source pathname, subject/session/run IDs,
task, original target, encoded target, any distributed label name, partition and
signal hash. CHB-MIT's `participant_id` normalizes chb21 to chb01 based on the
original PhysioNet description; `subject_id` preserves the original case label.
The two cases both fall in merged training. BCI 2020-3 intentionally shares
subjects across train/test and preserves the published run split.

The pinned CHB-MIT release also includes chb24 (861 windows), but OpenEEGBench's
fixed masks do not assign it to any partition. It is explicitly excluded from
conversion, with its source metadata and exclusion recorded. The inspected FACED
metadata has **eight** observed classes, with no Neutral (label 4) examples,
despite the configuration declaring nine. This is an additional source issue to
resolve before admission, independently of its licence status.

`i_window_in_trial` is a **window ordinal**, not an original trial ID. It is
preserved without inventing trial identifiers. FACED supplies `video_index` and
other video/rating metadata; where present this is retained as the trial/video
identifier. `source_epoch_index` identifies the distributed epoch row, not a
guaranteed original acquisition trial. `start_sample_processed` and
`stop_sample_processed` are sample coordinates in the processed recording with
an exclusive stop. Seconds are derived using its stored processed frequency.
Original acquisition sample indices remain null because resampling, cropping
and BIDS trial concatenation prevent exact recovery from these fields alone.

Original frequency/reference information from matching pinned BIDS sidecars is
kept as independent source-file evidence, separate from publication-reported
frequencies in the registry. NEMAR revisions identify the metadata consulted,
not proof of the exact unpublished BIDS revision used to build the HF arrays.
Absent session/run IDs remain null; a zero explicit-session count means unknown,
not evidence that there were no sessions. For fixed-window datasets without a
saved label mapping, JSON records observed target/task associations; it does not
invent original textual labels. MDD diagnosis names are an explicitly marked
inference from HS/MDDS source naming and the original dataset description;
numeric targets remain unchanged.

## Validation and adding candidates

Conversion checks every case for finiteness, expected window shape and label
range. It re-reads every stored case, recomputes its canonical float32 SHA-256,
compares the metadata hash and verifies source-index order and labels. Exact
cross-split duplicates fail validation, including equal signals with different
labels. Hashing normalizes signed zero. This does not detect approximate
duplicates or all possible shared recording segments; sample intervals and
subject/source identifiers remain necessary for those audits. Unexpected subject
overlap fails; only the published BCI run split is an explicit exception.

The aeon smoke test fits SummaryClassifier on up to eight cases per class and
predicts up to two test cases per class. It verifies compatibility, not benchmark
accuracy. The pilot `.ts` files should additionally be reloaded with
`aeon.datasets.load_from_ts_file` and compared with the HDF5 arrays.

Tests use synthetic, checksum-verified on-disk releases with explicit EEG and ECG
sensor identities. They cover deterministic split concatenation, leading zeros,
labels and row correspondence, channel-order rejection, missing metadata/chunks,
output corruption, duplicate rejection, licence gating, `.ts` round trips and an
aeon classifier fit. Existing archive tests run separately; no existing metadata
or results need regeneration.

To add a candidate, inspect its original terms and processed schema first, then
add its exact HF revision, upstream source evidence and explicit partitions to
`registry.py`. Do not guess missing channel names or relax the channel checks.
Extend the adapter with tests if the storage schema differs. A reviewable report
must distinguish successful conversion, metadata-only inspection and failed
validation; an available HF repository alone is not release approval.

The preparation run and its source-data findings are recorded in
[the candidate results report](openeegbench-results.md). Depression/MDD was
removed after validation found exact source-signal duplicates across subjects
and train/test. Prepared arrays and the quarantined `.ts` export were deleted;
only diagnostic reports and source metadata remain. Its pinned registry entry is
retained for auditing, but CLI download/export choices exclude it and conversion
rejects it. See the [upstream issue draft](issues/mdd-duplicate-windows.md).
FACED remains deferred because of unresolved original terms and its missing
Neutral class.
