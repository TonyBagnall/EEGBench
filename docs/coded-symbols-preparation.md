# CodedSymbols: Thielen2021 offline visual targets

**CodedSymbols** predicts which of 20 coded visual targets a participant attends
to. It uses the offline calculator-grid experiment from Thielen2021: 30 people,
one session per person, five blocks and 20 trials per block. Each target appears
once in each block. All 20 original target IDs are retained, giving 3,000 cases.

The source is the Radboud collection
[*From full calibration to zero training for a code-modulated visual evoked potentials brain computer interface*](https://doi.org/10.34973/9txv-z787),
**version 3**, public directory `DSC_2018.00122_448_v3`. Its original
[LICENSE.txt](https://public.data.ru.nl/dcc/DSC_2018.00122_448_v3/LICENSE.txt)
contains **CC0 1.0**, explicitly permitting copying, modification and distribution.
This is the data licence, independently verified from the original deposit.
The requested Radboud acknowledgement and source citations accompany the export.

Reference: Thielen, Marsman, Farquhar and Desain (2021),
[*From full calibration to zero training for a code-modulated visual evoked potentials for brain–computer interface*](https://doi.org/10.1088/1741-2552/abecef),
Journal of Neural Engineering 18(5), 056007. The source README's citation still
says version 1; the exported source is pinned to the version-3 directory and its
publisher SHA256 manifest.

## Local results

The export is complete in `D:/Data/EEG/CodedSymbols/`. See the
[machine-readable results](coded-symbols-local-results.json) for validation details.
Size includes `.ts` and metadata files, in decimal GB.

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---|---|---|---|---|---|---|---|---|
| CodedSymbols | 2200 | 800 | 30 | 8 | 16128 | 20 | 512 | 5.575 | CC0-1.0 |

All 3,000 cases passed exact float32 numeric readback, label/count/order checks,
metadata alignment, sensor-order checks, complete finite windows and duplicate
checks. No subject or duplicate case crosses train/test. There are 110 cases per
class in training and 40 per class in testing. All 150 recordings confirm one
session per participant and a separate 180 Hz processed-buffer header.

The initial two-person, one-block pilot passed before the full run. The full
representative aeon check loads 40 training and 40 test cases covering all 20
classes, then fits and predicts with `SummaryClassifier`. Full numeric checking
independently covers every exported case. **66 automated tests pass.**

There are **two trials with accumulated cycle-marker drift over 100 ms**, with
a maximum of 104.2 samples (approximately **204 ms**). Their original marker
times, unchanged nominal windows and per-case warning flags are preserved.
The affected training cases are `Thielen2021/offline/05/5/12` and
`Thielen2021/offline/06/2/01` (zero-based trial indices).
The first-electrode Fpz/Fp1/Fz discrepancy also remains explicitly unresolved.
These source limits are included in the quality status rather than concealed.

The complete dataset occupies approximately **3.097 GB** as float64 numeric
arrays, excluding loader/label overhead. Conversion and validation process the
data in bounded memory. Original source metadata and checksums remain available
alongside the final arrays; large temporary input recordings and pilot exports
are removed after validation.

## Cases and split

Each case contains **eight EEG channels × 16,128 timepoints**, a nominal
31.5-second trial at the original **512 Hz**. The participant attends one target
while the targets display distinct 126-bit modulation codes at 60 Hz. A nominal
code cycle lasts 2.1 seconds, with 15 cycles per trial. The one-second cue is
outside the archived window.

The labels are the original **1–20** entries of each block's `trainlabels.mat`.
They identify the attended target/code column. They are unchanged in the archive;
the associated descriptions `symbol_01`–`symbol_20` are index descriptions, not
invented character names. The actual glyph-to-index mapping has not been verified.
The original code matrix and subset resources are preserved.

The fixed EEGBench split is **participants `01`–`22` train, `23`–`30` test**:
2,200 training and 800 test cases, with respectively 110 and 40 cases per class.
There is no official source train/test assignment and no archived validation set.
Order is numeric participant, numeric block, then chronological trial order.
Read participant, session and run IDs as strings.

The session identifier is the date in the original filename, paired with the
participant; the GDF does not supply an acquisition timestamp or participant string.
The configuration's `main.subject` corroborates the `sub-XX` participant path.
Its numeric `main.subjectid` is **not** a participant identifier: it is 1 even for
participant 23. That field is retained without using it for grouping. Original
trial identity is traced through the label-vector index, STATUS-event index,
recording path and complete list of cycle-marker samples.

## Raw data versus processed buffers

The exported data come from each original `*_main_eeg.gdf`, which has a STATUS
channel followed by eight EEG channels. **STATUS is axis 0 and is excluded**;
native axes 1–8 are retained in order. MNE applies the GDF calibration and physical
unit conversion to volts; no further scaling is added. Values are cast to float32
and written with nine significant digits for exact float32 `.ts` roundtrip.

The deposit also contains `traintrials.mat` buffers at **180 Hz**, with 5,670
samples per trial in the pilot. The associated `hdr.mat` describes these buffers.
Configuration settings refer to additional filtering/downsampling in the original
system. Those buffers and transformations are **not used** in this raw 512 Hz
preparation. Original configuration and header files are preserved and decoded
separately from the actual GDF header. No added filtering, resampling, baseline
correction or reference change is applied.

Trial starts are recovered using the pinned MOABB algorithm: consecutive STATUS
markers normally occur approximately 2.1 seconds apart, and a gap outside
1.8–2.4 seconds starts a new trial. Each block must have exactly 20 groups and
15 or 16 cycle markers per group. A sixteenth marker sometimes occurs at the
trial boundary and sometimes is absent; blindly taking every sixteenth event
would give incorrect starts. Label order is checked against the configuration.

The crop is `[first marker, first marker + 16128)` in zero-based original samples,
with the end exclusive. Nominal full-trial windows must not overlap and must be
complete and finite. Original marker jitter is retained without moving or
resampling samples. Cycle timing deviations are recorded per case; accumulated
deviations over 100 ms from the nominal cycle schedule are explicitly flagged.
The source includes such delayed trials with intact trial grouping and label
alignment. Their nominal windows are retained without time warping. Trial count,
label alignment, complete windows and non-overlap remain mandatory checks.

MOABB's binary code-bit prediction and this 20-target problem use the **same
recordings**. They are different label/epoch views, not independent recording
collections. Only the 20-target problem is added. The separate online experiment
with a different target set is outside this preparation.

## Sensor identity and positions

The literal order in the supplied `resources/nt_cap8.loc`, also used by the
pinned loader's mapping, is:

```text
Fpz, T7, O1, POz, Oz, Iz, O2, T8
```

The GDF's EEG names `AF3, F3, FC5, P7, P8, FC6, F4, AF4` are default cap labels
and are explicitly identified as incorrect for this custom acquisition by the
loader. The mapping changes names without changing array order. Every recording
must have the expected native names, types and ordering before selecting EEG.

**The first electrode's physical identity is unresolved.** The `.loc` file and
loader mapping say **Fpz**; `nt_cap8.txt` and the processed buffer header say
**Fp1**; the publication/overview description says **Fz**. We use the literal
`.loc` name Fpz in the ordered channel list and explicitly flag its conflicting
aliases. It must not be treated as an independently confirmed anatomical location.
This is an actual source discrepancy, not a guessed replacement sensor name.

The `.loc` polar coordinates, alternate `.txt` template, processed header and
native GDF location fields are preserved. These are not individual digitizations;
the default GDF cap positions must not be interpreted as the actual custom cap.
The source study describes a Biosemi ActiveTwo acquisition with CMS/DRL. Reference
information from the publication/loader is distinguished from native header data.

## Reproduction and artifacts

Install `tools/requirements-moabb.txt` in a separate preparation environment.
The tested runtime uses MNE 1.13.2 and aeon 1.5.0. Run:

```powershell
python -m tools.prepare_thielen --cache D:/Data/EEGSources/Thielen2021 --output D:/Data/EEG
```

The converter refuses an existing destination before downloading. `--subjects`,
`--train-subjects`, `--runs`, `--output` and `--offline` allow small pilot runs or
reuse of a verified source cache. For example, the initial pilot used subjects
`1,23`, train subject `1` and run `1`, with a separate output directory.

Source pins:

- Version-3 publisher manifest SHA256:
  `8fb809122ade5446fc137b3d5ad8e36e357bf252f01d7f1e9404a65dcae4633b`.
- Original CC0 licence SHA256:
  `240cd1c345932866b833dd34c637d7b4832cd02218792feee0501349f312353b`.
- MOABB loader commit `bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`,
  `moabb/datasets/thielen2021.py`.

Original files are downloaded directly from Radboud and checked against its
published SHA256 values. The NEMAR alias `nm000214` identifies the source study;
its BIDS/bit-event derivatives are not inputs to this preparation. The source
cache keeps the original binary GDF and MATLAB files; conversion processes one
recording at a time with float32 trial windows, and numeric validation streams
the `.ts` rows. There is no additional large intermediate array copy.

`D:/Data/EEG/CodedSymbols/` contains:

- `CodedSymbols_TRAIN.ts`, `CodedSymbols_TEST.ts`.
- Exactly aligned `cases_train.tsv` and `cases_test.tsv`; `CodedSymbols_rows.tsv`
  combines them in TRAIN-then-TEST order.
- `CodedSymbols_metadata.json`, `CodedSymbols_manifest.json`, the validation
  report, `channels.txt`, `channels.tsv`, `recordings.json` and completeness report.
- `source_metadata/`: original licence/README/manifest, montage/code resources,
  per-recording cfg/header/labels, decoded native metadata and STATUS events,
  plus the pinned loader. Template and raw sensor evidence remain distinct.
- Attribution, a short README and conversion code with dependency pins.

Validation covers all shapes/counts, original labels, metadata-row alignment,
EEG selection/order, finite complete windows, source order, within-partition
duplicates, train/test signal duplicates and subject separation. Full numeric
readback checks every case; representative aeon loading and classifier fit/predict
checks cover all 20 classes. No benchmark scores are produced.

| Metadata | Availability / evidence |
|---|---|
| Participants | `sub-XX` paths and matching cfg string; numeric cfg subjectid not used |
| Sessions/runs | Filename date and block path, retained as strings |
| Trial/epoch identity | Original label-vector row, STATUS-event index and cycle markers |
| Sample/time bounds | Original GDF samples, zero-based, end exclusive |
| Labels | Original 1–20 target IDs unchanged; code matrix retained; glyph mapping unverified |
| Sampling | Raw GDF 512 Hz; separate 180 Hz processed-buffer header explicitly distinguished |
| Channels/types/order | Eight EEG axes verified in every GDF; STATUS excluded; all native aliases retained |
| Positions/reference | Templates and native fields retained; first site conflicts; individual positions unavailable |
| Demographics | Publication aggregate only; no individual age/sex invented from invalid GDF fields |
| Licence/provenance | Original CC0, publisher SHA256 per file, version-3 URL and pinned loader |

No downloaded recordings or generated arrays are committed to Git or uploaded.
