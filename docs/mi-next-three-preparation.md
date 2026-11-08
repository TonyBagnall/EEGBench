# Three further motor imagery datasets

Completed 8 November 2026. The original Batista, Polo-Hortiguela and Leeuwis
collections have been prepared as ImaginedHandsHaptics, ImaginedAnkleRest and
ImaginedHandsFeedback. Each small pilot passed the complete conversion and aeon
checks before its remaining source files were downloaded. Final outputs are in
`D:/Data/EEG/<Name>/`; original files, pilots and per-recording compressed NPZ
intermediates remain separately under `D:/Data/EEGSources/`. No uploads.

<!-- SUMMARY:START -->
| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ImaginedHandsHaptics | 3083 | 1034 | 20 | 32 | 2495 | 2 | 500 | 4.605 | CC-BY-4.0 |
| ImaginedAnkleRest | 264 | 132 | 6 | 28 | 1000 | 2 | 250 | 0.212 | CC-BY-4.0 |
| ImaginedHandsFeedback | 6560 | 2240 | 55 | 16 | 1250 | 2 | 250 | 3.100 | CC-BY-4.0 |
<!-- SUMMARY:END -->

Sizes describe the complete local output directories, in decimal GB. The three
additions bring the collection to 77 registered / 73 selected problems, including
25 motor imagery problems (24 scalp EEG plus the original ECoG entry). The
original 30 paper problems and experiment results are unchanged.

Every numeric case passed exact float64 `.ts` readback and ordered metadata,
label and signal-hash checks. All original channel orders were checked against
the actual selected arrays. No exact duplicate cases within or across partitions,
no shared participant IDs across train/test, and no EEG sensor removals were
found. Aeon loaded each final and fit/predict passed on three cases per class
per split; this is a compatibility smoke check, not full-cohort classifier fitting.
Final manifest byte counts and SHA256 values were verified after sidecar refresh.

## ImaginedHandsHaptics — Batista2022

Original [Zenodo 7664069 v1](https://doi.org/10.5281/zenodo.7664069),
*Physiological Signals During Motor Imagery Brain-Computer Interface Training
Using Virtual Reality and Haptics*, Batista, Caetano, Fleury, Figueiredo and
Vourvopoulos (2022). Original data CC BY 4.0, verified from the version-specific
record independently of MOABB software. Twenty participant ZIPs total 2.863 GB.
The pinned MOABB loader declares NEMAR nm000318 as another source view; no NEMAR
arrays were downloaded or counted separately. A separate primary paper DOI for
these exact recordings was not established; original NeuRow references remain
in the publisher metadata.

Classify imagined left versus right hand during five feedback conditions:
MI, MIMO, MIMOHP, MIMOVR and MIMOVRHP. These compare abstract feedback, motor
observation, VR and haptics; they are pooled into one classification problem.
Executed-movement ME recordings are excluded. The source has 20 people and
99 imagery recordings, rather than an assumed 100: sub-13 lacks MIMOVRHP.
Native class cues total 4,127; ten trials with lost-sample discontinuities or
missing/ambiguous end markers are excluded, leaving 4,117 cases. Actual cue counts
of 42 or approximately 40 are retained rather than forced to a nominal count.

Native S7/S8 cues identify left/right and S10 identifies the imagery end. The
common safe crop is 2,495 samples, 4.99 seconds at 500 Hz, determined from the
shortest complete, discontinuity-free imagery interval. No interpolation or
invented nominal timing. Original trial ordinals, marker keys/lines, sample
bounds, end markers, timestamps and exclusions accompany the cases. Sample times
are stored-file indices divided by 500, not reconstructed wall-clock elapsed time
across dropped samples. Native session IDs and all recording dates are preserved.

Exact 32-channel EEG order and explicit microvolt resolutions are read from
every original BrainVision header. Float32 digital samples are cast to float64
before per-channel physical calibration, independently checked with MNE. No
archive filter, baseline, resampling or rereference. The other six inputs are
excluded: their native names vary between generic Aux1/Aux2/Aux3 and explicitly
named PPG/ECG/Resp, followed by three accelerometers. Generic per-input physiology
is not guessed from MOABB renaming. EEG order does not change. Original
coordinate templates and hardware/software filter tables are retained where
present; 24 headers omit coordinates. No missing geometry or filter history is
filled from a generated standard montage. Electrode reference/ground and
individual demographic mappings remain unknown. Cohort age and sex percentages
are retained as reported, without inventing integer demographic counts.

Native participant folders 01–09, 12–19 and p01–p03 are primary identifiers.
Pilot p01–p03 filenames contain sub-01–03 tokens; both tokens are preserved,
never merged. MOABB's secondary IDs 20/21/22 map to p01/p02/p03 explicitly.
TRAIN contains main 01–09,12–15 and pilots p01/p02; TEST main 16–19 and p03:
15/5 people, with pilots represented on both sides. Within each partition,
participant folders, original recording timestamps and native cue order define
the deterministic case order. No source benchmark train/test partition exists.

All 99 native calibrated EEG-only recording hashes and 4,117 retained
cue-locked two-second EEG fingerprints were compared with the 26 original
ImaginedHandsEmbodiment recordings and their source cue prefixes: no exact
matches. Native acquisition dates are also disjoint (Batista 2021–2022,
Embodiment 2023). This supports separate recording collections; it does not prove
that anonymised participants differ between studies. See
[full identity evidence](batista-vagaja-full-identity.json),
[native cue/exclusion audit](batista-full-native-marker-audit.json),
[auxiliary variants](batista-native-sensor-variations.json) and
[coordinate availability](batista-native-coordinate-availability.json).

## ImaginedAnkleRest — PoloHortiguela2025

Original [Zenodo 14672334 v1](https://doi.org/10.5281/zenodo.14672334),
*EEG Signal Dataset During Dorsiflexion and Plantar Flexion Movements*,
Polo-Hortiguela, Ortiz, Ianez and Azorin (2025), original data CC BY 4.0.
Twelve original ZIPs total 2.936 GB. MOABB declares NEMAR nm000302 as another
view, not another recording collection.

Six people imagine dominant-ankle dorsal/plantar flexion or relax, wearing an
exoskeleton in STATIC and MOTION conditions. Original S1 is a single visit per
person; the two conditions are not separate visits or problems. Each condition
has 11 native repetition files: 132 files overall. Native task codes 211/221
identify relaxation and 311/321 imagery. Keep the first four seconds of each
labelled phase, matching the pinned MOABB interval: two relaxation phases and
one imagery phase per repetition, 396 cases. Initial settling, audio preparation
and return phases are excluded. Full phase bounds, native task index/order,
recording date, repetition ID and trigger-quality hashes/ranges are retained.
Trigger semantics are not guessed for undocumented rejection. No overlap is
introduced by the selected windows.

Use only original `session.data_EEG`, not supplied processed/filter/normalised
blocks. Native arrays have 35 channels: 28 EEG, four EOG and three inertial.
Configured names and EEG indices are checked in every file. Exact uppercase Z
spelling and array order are preserved; there is no standard-name substitution.
Original configured 2D positions and preprocessing-step tables are retained,
without asserting coordinate units/frame or individual measurement. The 250 Hz
sampling rate is a native configuration field. Raw float64 numbers are unchanged;
microvolt interpretation is inferred because an explicit original physical-unit
field was not recovered. Reference/ground and individual demographics are unknown.
Some MATLAB string objects are opaque to SciPy; original MAT files are retained
rather than assigning guessed descriptions. No archive DSP.

Release folders B01–B05 match their native IDs; release B06 files identify B07
internally. Both IDs are retained and a consistent one-to-one mapping is required
across all repetitions/conditions. Do not silently replace either identity.
TRAIN release B01–B04, TEST B05–B06: four/two people, 264/132 cases.
Case order is release participant, STATIC then MOTION, repetition filename and
native phase order. Source file/date mappings are in the
[complete inventory](polo-release-native-file-audit.json).

## ImaginedHandsFeedback — Leeuwis2021

Original [DataverseNL 10.34894/Z7ZVOD v1.0](https://doi.org/10.34894/Z7ZVOD),
version ID 3733, *Psychological and Cognitive Factors in Motor Imagery Brain
Computer Interfaces*, Leeuwis, Paas and Alimardani (2021). Original version terms
explicitly grant CC BY 4.0. All 224 files total 5.135 GB: 220 EEG CSVs plus the
questionnaire, online-error summary, readme and original data report. The report
was extracted and both pages visually inspected. Related paper:
[*Vividness of Visual Imagery and Personality Impact Motor-Imagery Brain Computer
Interfaces*](https://doi.org/10.3389/fnhum.2021.634748); the report also cites
Leeuwis and Alimardani (2020), *High Aptitude Motor-Imagery BCI Users Have Better
Visuospatial Memory*. MOABB declares NEMAR nm000327 as a secondary view.

Fifty-five native, non-contiguous participant IDs 7–67; never renumbered 1–55.
One visit per person, calibration then three feedback runs, 40 trials per run,
20 left and 20 right: 8,800 cases. Actual 16-channel CSV order is authoritative
and differs from the prose electrode list. Parse numeric CSVs with round-trip
float64 decimals. Each stored trial has 2,000 points and starts at t=-2.996,
not exactly -3 seconds. Locate actual t=0 at index 749 and keep 1,250 samples,
0 through 4.996 seconds. Preserve original trial IDs, -1/+1 classes, file/datafile
IDs, epoch-local bounds and stored CSV row bounds. Original continuous offsets,
calendar/visit IDs and individual electrode positions are not distributed; no
synthetic timeline or montage is constructed.

Native numbers are unchanged. Microvolt interpretation is inferred; neither the
CSV header nor original data report explicitly supplies physical units. The
paper describes acquisition/online processing with 0.5–30 Hz bandpass and
48–52 Hz notch, but the exact distributed CSV filtering history is not separately
labelled. Right-earlobe reference and AFz ground are documented in the original
report/paper. No added archive filtering, baseline, referencing or resampling.

Questionnaire ppnr IDs map directly to EEG IDs, providing individual age,
gender, handedness, cognitive/personality scores and notes. Preserve original
strings and fields; raw BCI_Novice coding is not interpreted without its question
wording. Actual distributed rows cover 55 people, 36 Female/19 Male. The report's
36 female +21 male totals describe 57 and are retained as a source inconsistency.
Basic demographic fields accompany each case; full participant records and the
unaltered supplementary CSVs accompany the dataset. Online error summaries are
metadata, never EEG classification features.

Archive TRAIN contains the first 41 numeric native IDs, TEST the remaining 14:
6,560/2,240 cases. Calibration and feedback phases are pooled but preserved in
case metadata; original per-person adaptive classifiers are not reproduced.
No fixed published benchmark test partition is supplied. Subject 40's irregular
feedback filenames are retained and linked through pinned file IDs. Native
filename subject IDs are independently checked. File chronology is not invented
where timestamps are unavailable. Original continuous interval overlap remains
unknown; stored row spans and exact duplicate cases are checked.

## Metadata completeness and reproduction

| Field | HandsHaptics | AnkleRest | HandsFeedback |
|---|---|---|---|
| Subject IDs | Native main/pilot strings plus filename aliases | Release/native strings and bijection | Native IDs and original ppnr mapping |
| Session/run | Native lab/pilot session, condition, dates | Native S1, condition, date, repetition | Documented single visit, calibration/feedback file mapping; dates absent |
| Trial/case identity | Native cue/marker ordinals and lines | Native repetition and labelled phase | Original trial 1–40 and source CSV row bounds |
| Original timing | Native recording indices/end/segment markers | Native recording/phase indices | Epoch-local TimeStamp, continuous offsets unknown |
| Labels | Native S7/S8, encoded 1/2 | Native 211/221/311/321, encoded 1/2 | Native -1/+1, encoded 1/2 |
| EEG names/order | Direct from every native header | Direct native configured labels/indexes | Direct every CSV column header |
| Units | Explicit native microvolt calibration | Inferred microvolts; original numbers unchanged | Inferred microvolts; original numbers unchanged |
| Positions | Native templates where supplied, 24 missing tables | Native configured 2D, units/frame unknown | No individual positions recovered |
| Reference | Unknown | Unknown | Right earlobe / AFz ground documented |
| Demographics | Cohort summary only | Not recovered | Individual questionnaire records |
| Original partition | Unsplit; assigned whole-subject split | Unsplit; assigned whole-subject split | Calibration/feedback phases preserved; whole-subject archive split assigned |

Original data grants are independent of the software licence. Exact source pins
and publisher checksums are in `batista-mi-source-lock.json`,
`polo-mi-source-lock.json` and `leeuwis-mi-source-lock.json`. Each dataset has a
`*-mi-conversion-result.json` and `*-mi-metadata-completeness.json`; the combined
machine-readable summary is [mi-next-three-summary.json](mi-next-three-summary.json).
Original source evidence, code snapshots, class counts, memberships, ordered
case TSVs, channels TSV/text, metadata JSON, full validation and manifest accompany
each final. Read identifiers as strings.

Reusable commands, in an environment matching `tools/requirements-moabb.txt`:

```powershell
python -m tools.download_mi_next batista --pilot
python -m tools.prepare_mi_next batista --pilot
python -m tools.download_mi_next batista
python -m tools.prepare_mi_next batista
```

Use keys `polo` and `leeuwis` identically. Both scripts accept `--cache-root`;
conversion accepts `--output`. Pilots use a separate source-cache `pilot-output`
folder and separate ordinal NPZ cache. Batista's mandatory cross-source audit
uses the existing Vagaja source cache under the same cache root; its metadata
path is configurable with `--identity-reference-metadata`. Converters refuse
existing finals. Finalise only after source checks, full numeric/metadata/channel
and duplicate validation plus aeon smoke pass. No validation split is archived.
