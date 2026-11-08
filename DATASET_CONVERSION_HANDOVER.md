# EEG dataset conversion: agent handover

Entry point for an agent continuing archive assimilation. Read this before downloading or converting. The user authorises continuing through eligible batches without repeatedly asking permission. Read live state before relying on the snapshot below.

## Active three-dataset batch:8November2026

User authorised Batista2022, PoloHortiguela2025 and Leeuwis2021. Proposed final names ImaginedHandsHaptics, ImaginedAnkleRest, ImaginedHandsFeedback. Current registry remains74/selected70/MI22 until full validation. All three native-source pilots passed exact .ts/metadata/sensor/duplicate/aeon checks. Public reusable tools/download_mi_next.py and tools/prepare_mi_next.py; tests88passed (nine new safeguards). Sources/finals on D, about102GB free before batch. Full source transfers running; gated sequential full conversions start automatically via ignored .openeegbench/mi_next_watch_convert.py. Inspect .openeegbench/mi-next/cohort-orchestrator.json/log and per-key download-full/full JSON/log files before launching any duplicate jobs. Worker .openeegbench/run_mi_next.py takes key and action. No subagents, no uploads.

Source locks docs/batista-mi-source-lock.json,polo-mi-source-lock.json,leeuwis-mi-source-lock.json (pilot receipts replaced by full source locks when transfers complete). Pilot results docs/<key>-mi-pilot-result.json retained. Preparation docs/mi-next-three-preparation.md, progress docs/mi-next-three-progress.json. Full core results may temporarily include new pilot entries, never register those.

Batista pilot209/196cases32x2497at500Hz; native42vs40cue counts retained, lost-sample trials excluded. Compare full original calibrated EEG-only recording hashes plus2s cue fingerprints against all26Vagaja recordings before admission; pilot10recordings already passed with disjoint dates. Full common crop derived from valid native S10 spacings, may differ from pilot. Keep p01-p03 participant folders distinct from sub-01..03 filename tokens.15/5whole-subject split balances pilot/main cohort, excludes ME execution. Native units explicit, reference unknown. Require final metadata/code/doc refresh and all artifact hash checks.

Polo pilot33/33cases28x1000at250Hz, no EEG removed. Fixed B01-B04/B05-B06 split now works for pilot B01/B06; original default first4of2 caused empty test and was fixed/tested. Full132repetitions, three phases each expected396cases before quality checks. Source uppercaseZnames from native config retained. Release B06 internally B07: preserve both aliases; code requires bijection across all files/conditions. OriginalS1 with STATIC/MOTION conditions, not two visits. First4seconds each15srest/28sMI phase match pinned MOABB interval; exclude settling/audio states. Raw data_EEG only; units inferred unchanged, missing reference and2Dcoordinate units flagged. Some MATLAB string objects opaque; preserve source, no guesses.

Leeuwis pilot160/160cases16x1250at250Hz, no EEG removed. Native non-contiguous IDs7..67,55people/220CSVruns. Find actual t=0atindex749 (start-2.996), not nominal750. Round-trip float64 CSV parse; no synthetic continuous timeline. Whole-subject first41numeric native IDs/remaining14, pooling calibration+feedback with source phase metadata. Questionnaire ppnr maps actual individual demographics/scores:55rows36Female/19Male, report57total is inconsistent. Native BCI_Novice raw coding not interpreted. Paper documents filter/reference/ground; exact CSV filter history/units not explicit. Source file-ID mapping includes irregular Subject40 names; native filename participant checked during full conversion.

After all full jobs: register only validated finals, update registry/README/eeg.txt/tables/counts and source descriptions/provenance, add summary/completeness reports, merge latest full worker results so pilots cannot overwrite them, refresh final sidecar docs/code/hashes and run relevant tests/diff check. Expected totals77registered/73selected/25MI only if all3pass. Roadmap remaining Pan2023/Pan2025/Rozado/Cho/Daly still have original grant/access/identity gates; don't start them until this requested batch resolved.

## Latest completion:8November2026

ImaginedHandsRobot, ImaginedGrasps and Vagaja2023/ImaginedHandsEmbodiment are fully converted, validated, registered and documented on D.74registered/70selected,22MI including21scalp EEG and one ECoG. No active workers remain for this batch; do not rerun existing finals. [Summary, dimensions, metadata completeness and caveats](docs/mi-completion-batch.md); machine-readable summary docs/mi-completion-batch.json. Original30results unchanged. No uploads.

Robot2880/2880cases32x1000at250Hz; native training/online phases intentionally share people/sessions. Grasps4500/2250cases60x1000at250Hz; official training+validation merged, test day unchanged, shared people intentional. Native float64 Grasp units remain inferred microvolts; no guessed rescaling. Continuous offsets unavailable. All numeric readbacks, labels/metadata/order, duplicates and aeon compatibility checks passed. Every final manifest artifact hash was checked after refreshed sidecars.

Embodiment798/240cases32x4997at500Hz; source1040cues, exclude two left-hand imagery trials crossing lost-sample markers, common safe4997sample window. Native header calibration/coordinates/filter tables recovered; source SUB31 explicitly uses deposited same-stem EEG/VMRK because header references are stale. Whole-subject20/6 split,10/3perpriming group. No flat EEG removals in any of the three. Original source caches D:/Data/EEGSources/Farabbi2020,BCIComp2020UpperLimb,Vagaja2023. Pilot/full ordinal caches separate for Grasps/Vagaja. Preserve old pilot caches; never silently infer sensors/reference or original continuous offsets.

Next candidate is Batista2022, original Zenodo7664069 CC BY4.0 (2.863GB originals); no EEG downloaded in this batch. Before independently counting it, compare native file IDs/dates/waveforms with Embodiment due common laboratory/hardware. Roadmap docs/motor-imagery-road-to-30.md/json has eight further candidates needed for30 under existing counting rule. Do not resume deferred MIMED/depression/VisualCategories without resolving documented source quality issues.

## Objective and boundaries

Prepare EEG classification problems as standard aeon/tsml `.ts` TRAIN/TEST files with comprehensive metadata sidecars in **D:/Data/EEG/**. Original downloads and numeric intermediates belong separately in **D:/Data/EEGSources/**. Maintain source identity, licence evidence, descriptions and source-issue reports in this repository.

- Prioritise verified fully open data, then smaller source/converted sizes. Public availability and software licensing do not establish data redistribution rights.
- No Zenodo or other uploads. No messages/issues to authors without explicit instructions; local issue drafts are fine.
- Do not download SEED-V or reinstate depression without resolving its known source duplicates.
- Preserve the original 30-problem paper subset and existing experiment results. Additions are local preparations until separately released.
- Do not overwrite existing final problems casually. Converters refuse existing final directories. Previously authorised corrections are documented separately.
- Do not commit large EEG/source/array/runtime files. `.openeegbench/` and `tmp/pdfs/` are ignored; large artifacts belong on D.
- Preserve unrelated uncommitted changes in this shared workspace. Read applicable AGENTS.md/current permissions. No subagents unless explicitly authorised by applicable instructions.

## 1. Recover current state

Read, in order:

1. `docs/assimilation-progress.json`: completed/in-progress/deferred work and current counts.
2. `docs/datasets.md`, `docs/dataset-provenance.md`, `eegbench/datasets.py`, `eeg.txt`.
3. `MOABB.md`, `OpenEEGBench.md`, `EEG-Bench.md`, `AdaBrain-Bench.md`, and their machine-readable inventories/mappings.
4. `docs/open-moabb-conversion-results.json` and relevant source-specific preparation/result/lock/completeness files.
5. Relevant converters, downloaders and tests. Inspect running sessions/logs before starting another worker for the same source.

Snapshot on 6 November 2026: **66 registered / 62 selected**. Four excluded from `eeg.txt` remain in the registry/on disk: Blink(4 channels), ButtonPress(32), Sleep(1), EpilepticSeizures(1). Only the last two are single-channel. Counts will change; use live state.

Latest completed sources, already prepared and registered:

| Archive name | Source | Train/test | Subjects | EEG x samples | Hz |
|---|---|---:|---:|---:|---:|
| ParkinsonsPedalling | Singh2020 / PRED+CT d011 | 2123/842 | 39 | 63x2000 | 500 |
| ParkinsonsRest | Cavanagh2018b / PRED+CT d002 | 1216/420 | 55 | 63x2000 | 500 |
| ObsessiveCompulsiveSymptoms | Gruendler2009 / PRED+CT d008 | 7754/2660 | 35 | 52x2000 | 500 |
| WalkingTargets | BCIComp2020WalkingERP / Track5 | 3600/900 | 15 | 42x100 | 100 |
| SymbolAttention | Chailloux2020 / ds003190 v1.0.1 | 521259/175180 | 19 | 8x256 | 256 |
| ArmCoordination | Kueper2024 / Zenodo10229480 | 1498/505 | 8 | 64x1500 | 500 |

Do not reconvert them as new studies.

## 2. Windows runtime and safe execution

Repo: `C:/Code/EEGBench`, PowerShell. **Always read/write repository text with explicit UTF-8.** Elevated Python can default to cp1252 and corrupt prose or fail on smart quotes. Do not embed a PowerShell here-string terminator inside an outer here-string; use apply_patch or an actual runner file for complex content.

Existing scientific environment bootstrap:

```python
import sys
from pathlib import Path
for folder in ['nback-aeon-1.5.0', 'kalunga-runtime', 'ofner-runtime']:
    sys.path.insert(0, str(Path('C:/Code/EEGBench/.openeegbench') / folder))
```

Dependencies are pinned in `tools/requirements-moabb.txt`. Existing overlays provide aeon1.5.0/MNE1.13.2 and scientific dependencies; avoid installing another large environment on C. A Python script can bootstrap those paths then import/call a source converter. For long jobs, use an ignored real runner `.py`, capture stdout/stderr to an ignored log and checkpoint process/session IDs. Use `Start-Process -WindowStyle Hidden` for background helpers. Keep user progress updates concise and frequent; no blocking waits over60 seconds.

D access and some installed runtimes need `require_escalated` under the current sandbox. Dataset work is already authorised; use the tool escalation with a concrete explanation instead of asking again. Check space via `shutil.disk_usage('D:/')`. The sandbox C overlay has sometimes reported ENOSPC while elevated writes worked; large data still belong on D.

Pytest shared temp can be inaccessible. Use an owned basetemp:

```python
import pytest, uuid
pytest.main(['-q', '-p', 'no:cacheprovider',
    '--basetemp=C:/Code/EEGBench/.openeegbench/test-' + uuid.uuid4().hex,
    'tools/test_prepare_open_moabb.py'])
```

The previous midnight-to07:00 pause was a one-off local process guard, not an agent scheduler. The user resumed chat explicitly. Do not promise automatic agent awakening without an actual scheduler. Check a new pause request against current dates/timezone.

## 3. Inspect before download/conversion

- Compare accession, cohort, source file IDs and recording/task membership against our provenance. Relabelled/resampled/filtered views are not new recordings. A shared DOI also does not prove identical recordings: competition tracks and ERP CORE tasks can be separate experiments.
- Inspect pinned loader code, original documentation and host metadata. Current MOABB source snapshot: `bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`; pin/document any replacement.
- Verify the **original data licence** and applicability to actual files, separately from software and paper licences. Save original host evidence, exact version and obligations. Treat NC/ND/research access separately.
- Create `docs/<name>-source-lock.json` with release/revision, original file IDs/URLs, publisher checksums and byte counts. Record paper and data DOI separately; a paper DOI is not an established data DOI.
- Estimate source bytes, float64 arrays `cases*channels*timepoints*8`, text expansion, staging and cache requirements. Source size can mislead: SymbolAttention is about1.36GB source but27.83GB `.ts`/sidecars.
- Inspect actual headers/variables, names/order/types, calibration, labels and native split semantics. Download real organiser test-label sheets, not prediction submission templates.
- Run a small participant pilot through the **entire pipeline** before bulk conversion. A single ZIP may require full download before pilot extraction.

## 4. Reusable implementation and adapter contract

`tools/prepare_open_moabb.py` is the common exporter: native recordings -> compressed float64 NPZ -> staged `.ts` and sidecars. Register a source `SPEC` and reader in `core.SPECS`/`core.READERS`, then call `core.prepare(key, cache_root, output)`.

Reader yields `(X, case_rows, channel_names, recording_info)` per recording:

- X: finite float64 `(cases, channels, timepoints)`, with explicit physical numeric interpretation.
- case_rows: one dictionary per case in exact X order. Start with `core.base_row(...)`, then qualify assigned/unknown IDs and add native source fields.
- channel_names: exact sensor names in X axis order, consistent across all included recordings or safely harmonised by documented names.
- recording_info: native shape/fs/calibration/units, types/positions/reference, source hashes, original markers/headers, participant/run information, source flags and missing metadata.

Examples:

| File | Pattern |
|---|---|
| `prepare_kueper.py` | Explicit BrainVision microvolt resolution, float64 before calibration, repeated Mk keys, demographics/flags |
| `prepare_chailloux.py` | BIDS/native cross-check, missing target markers, copied recording, unknown units, numeric sorting of string IDs |
| `prepare_walking_erp.py` | Native epoched MAT, true XLSX labels, official train+validation merge, shared participants, local epoch times |
| `prepare_predct.py` | Clinical joins, source readability exclusions, continuous windows, flat-case audit |
| `prepare_liu2024.py` | Original trigger/source-product audit and qualified cohort exclusions |
| `prepare_small_moabb.py` | Verified atomic fetch, `.ts` header, exact readback, overlap/duplicate tests, aeon smoke |
| `prepare_wang.py` | Exact float64 case hashes and round-trip decimal formatting |
| `download_openneuro_release.py` | Immutable Git snapshot and git-annex hashes before accepting mutable S3 files |

Keep downloading/conversion separate from experiments/leaderboards. Source-specific `finish_sidecars` enriches metadata and refreshes changed artifact hashes/result size. Do not copy another finisher blindly: assumptions differ.

## 5. Splits, order and original case identity

- Follow official partitions. Archive TRAIN is original training followed by validation; preserve original TEST. No archived validation. Tuning is the fitted classifier's responsibility.
- For unsplit sources, define a deterministic whole-subject split and exact membership. Usually about75% training, but document actual rule rather than calling it an original split.
- Keep IDs as strings. `01`...`09`,`010`...`019` need numeric sorting when appropriate while preserving original tokens.
- Preserve native example/marker order; document file/session order and never shuffle.
- `case_splitter`, `allow_subject_overlap=True` and mandatory `subject_overlap_reason` support official temporal/session protocols. Do not use them to excuse accidental leakage.
- Continuous source: record zero-based start/end-exclusive samples and original event positions; retain one-based source positions separately.
- Epoched source: retain native file/epoch index and local times; unknown continuous offsets stay unknown. The overlap validator recognises the exact string `Native epoch-local samples; original continuous offsets unavailable`. Never present a synthetic concatenated Raw timeline as original time.
- Original session/run/trial IDs that are absent stay unknown. Assigned date groups/ordinals must be labelled assigned/inferred. Repeated Mk keys require literal key plus unique line ordinal/sample position.

## 6. Scale, sensors and authorised flat policy

- Recover true names/order from files or a primary document explicitly identifying rows. Never invent E1...En or montage names from array length. Loader-generated labels need independent evidence.
- Preserve native spelling, e.g. FZ/PZ. Select EEG by recovered roles, not by assuming all inputs are EEG. Preserve source mappings for excluded EOG/ECG/EMG/timestamp/accelerometer inputs.
- Verify every included recording's order. Document any safe named intersection/reordering and excluded sensors; otherwise flag/defer.
- MNE EEG normally arrives in volts; verified volts -> microvolts uses `*1e6` after float64 casting. MAT/EEGLAB numbers may already be microvolts; BrainVision binary may be counts requiring per-channel resolution. Never blanket-rescale all sources.
- User authorises **global sensor removal if any retained case is constant/effectively flat**. Current criterion: `std <= 1e-7` in microvolt numeric scale. Record exact-constant/tiny counts separately. Index6 means the seventh channel.
- Cast to float64 before multiplying/calibrating. Exact round-trip decimal formatting preserves the resulting binary64 values.
- No added demeaning, normalisation, filtering, referencing, resampling or unrelated rejection by default. Large DC offsets are not constant channels.
- Record pre-removal names/indices, removed names/indices, affected cases, scale/calibration and final exported native indices. Final sensor/case tables must reflect removal.
- `prepare_predct.removal_pair_audit` assumes event_index equals NPZ row index; adapt before using it with excluded source ordinals.
- Preserve original positions/montage/reference. Missing geometry/timezone stays unknown. Keep any template distinct from measured individual coordinates.

## 7. Source duplicates and cache integrity

The exporter performs **source-case hash preflight before writing large files**, then full post-selection duplicate checks. Final checks remain necessary: channel removal can make formerly different cases identical.

Exclude an exact copied recording only with verified matching participant, waveform bytes, header/calibration/sensors and native event/label stream. Retain the earlier copy, document paths/hashes/excluded cases. Never repair contradictory labels by guesswork. Identical label schedules do not imply identical EEG.

Cached ZIP extraction checks CRC, not only size. Cached NPZ must exactly match freshly decoded X. Preserve source checksums and native extracted-file hashes. A same-sized file is not proof of validity.

Document bad files and precise exclusions. A validated subset may be possible, but do not hide cohort/protocol changes. Defer unusable labels and move to another eligible source. A loader incompatibility is not proof the original biological signals are corrupt.

## 8. Required output

```text
D:/Data/EEG/ProblemName/
  ProblemName_TRAIN.ts
  ProblemName_TEST.ts
  cases_train.tsv
  cases_test.tsv
  ProblemName_metadata.json
  ProblemName_manifest.json
  ProblemName_validation.json
  channels.tsv
  channels.txt
  metadata-completeness.json
  ATTRIBUTION.txt
  README_ProblemName.md
  source_metadata/
  conversion_code/
```

Intermediate: per-recording `numpy.savez_compressed` float64 X, `allow_pickle=False`, in the source cache. `.ts` embeds y; separate four-NPY files are unnecessary for this archive.

Metadata: subject/session/run/file/recording, native epoch/event/marker index, source time/sample bounds, original/encoded labels, original partition; dataset source/data DOI/paper DOI/licence, participant/session/recording counts, rates/window/overlap, preprocessing, names/types/order/reference/geometry and class counts. Distinguish directly recovered, documented, assigned/inferred and missing information.

## 9. Validate before registering

1. Source pins/checksums, shapes, labels/class counts and finite values.
2. Complete `.ts` numeric readback reproduces every float64 case hash/label and metadata row order.
3. Subject/recording separation or explicit original-protocol overlap. Unknown continuous overlap is not zero.
4. Every array's channel identity/order matches final metadata.
5. Exact duplicates within/across splits and remaining flat/tiny sensors.
6. Explicit missing/inconsistent metadata and source issue evidence.
7. Aeon load/fit/predict smoke. Current smoke uses3 cases/class/split; do not claim full-cohort fitting. Complete arrays are stream-validated separately.
8. Pilot passes before full conversion.
9. Unique staging directory renamed only after validation. Never register Pilot outputs.
10. Refresh hashes/bytes/size after metadata/code/doc enrichment. Untouched already-validated `.ts` need not be reread repeatedly because prose changed.

Stop only an identified owned worker. Before deleting its failed staging directory on Windows, resolve/check the absolute path lies inside the intended D:/Data/EEG staging root and verify the problem header. Never delete broad computed paths or original datasets. Avoid concurrent writers to one cache/output. Shared root results JSON is not a concurrent database: check/merge keys if jobs finish together.

## 10. Register and document

- Add canonical tuple to `_TABLE` before its sort in `eegbench/datasets.py`. Keep `eegbench_paper` derived from the original30 rows before additions.
- Repository uses **all prepared problems**, not only30. New rows are `local_only`; automatic aeon/Zenodo downloads remain the original published open subset until release.
- Add alphabetically to `eeg.txt`, excluding the four user-removed problems.
- Update targeted counts in tests/README/docs; do not globally replace numbers that might be channel counts or results.
- Add measured metadata assertions and meaningful adapter tests for label/timing/identity edge cases.
- Regenerate the table between DATASETS:START/END markers using `metadata_markdown()`. Add task/source/dimensions/split/licence descriptions and original aliases/source identity to provenance.
- Fractional fs such as62.5Hz is supported; never round/resample to fit the registry.
- Save measured result/completeness/summary, update `docs/assimilation-progress.json`, and current comparison-page counts. Preserve explicitly historical surveys and original results.
- Refresh final sidecar copies of source descriptions/code and artifact hashes.
- Run relevant tests plus `git diff --check`. Last completed suite:47 passing tests; expect more with new adapters.

## 11. Known source traps

- **VisualCategories/Kaneshiro2015:** data CC BY3.0; README explicitly maps electrodes1-124. S1 has5188 epochs and4 exact duplicate pairs, all with different exemplar IDs;3262/3263 also conflict in category1/6. X_2D/X_3D agree upstream. S10 is clean,5184 epochs. Only S1/S10 downloaded; other8 unknown. Deferred, not registered. See preparation/audits/local issue draft. Do not blindly choose a label or assume every other subject is affected.
- **BNCI2003_004:** actually Competition III IVa(2005), right hand/right foot,5 subjects118EEG. Original-host CC BY4.0 grant not established; defer fully-open classification.
- **WalkingTargets:** official shared participants, epoch-local offsets only; real True Label sheet differs from submission template. L1/L2/R1/R4 removed, leaving32scalp+10ear. Source fs100Hz, units inferred.
- **SymbolAttention:** copied session recording, missing target block, no-flash placeholders, one-based BIDS sample fields and coarse timestamps; see completed report.27.83GB export versus1.36GB source.
- **ArmCoordination:** repeated Mk keys; explicit EEG calibration differs from accelerometers. Hardware131/software249Hz tables; MNE reports software only. XP01 set4 continues set3. All2003 native onsets retained with flags rather than forcing1920 nominal valid trials. Executed movements, not imagination.
- **ParkinsonsRest:** isolated S3 marker in control896 before real sequence; use validated marker groups. Exclude author-bad803 OFF. Rest import reads *_ODDBALL.vhdr, so rest/oddball may share acquisitions despite distinct MATs. Large DC offsets/author-bad sensors are not automatically flat.
- **ParkinsonsPedalling:** Aa/Bb/Cc are native EEG names; no invented anatomy. Clinical CSV uses literal backslash-t. Workbook/script support first63 EEG; XYZ accelerometers excluded.
- **ObsessiveCompulsiveSymptoms:** high/low student OCI scores, not diagnosed OCD. Use SELECT columnB, not duplicateJ.35 nominal raw CNTs retained;11 processed deferred.12 global flat sensors removed. Reader incompatibility does not prove corrupt source signals.
- **Depression/SEED-V:** remain excluded. MDD identical recordings were non-flat; distinct-subject copies invalidate naive use. Source licences always separate from software.

## 12. Next batch and checkpoint

Read current progress/next-batch inspections; do not select an already-prepared source from an old shortlist. Original-host-confirmed fully open first, then actual download/converted size. Candidates now under inspection include BCIComp2020UpperLimb/Track4 and compact unprepared MOABB sources.

Track4 shares OSF pq7vb with WalkingTargets/ImaginedCommands but has different recordings: three imagined grasps over three recording days. The pinned loader warns native10-second test epochs have the cue section masked; use the actual4-second MI segment consistently. Verify original MAT/PDF and organiser answer sheet; never blindly copy synthetic Raw reconstruction or treat hard-coded loader labels as the sole authority.

Checkpoint each material discovery/completion: exact running IDs/logs/stage path, pins, exclusions, completed files, current blocker and next command. Update live progress and next-batch notes. Another agent should resume from that checkpoint without repeating hours of downloads/export.


Next-batch live checkpoint: [docs/next-batch-progress.json](docs/next-batch-progress.json). Selected candidates are **ImaginedHandsRobot / Farabbi2020** then **ImaginedGrasps / BCIComp2020UpperLimb**. Kodera2023 remains a reserve because its two native channel/rate cohorts require a separate harmonisation/identity decision. Source inspection must precede conversion.


Current new adapters: `tools/prepare_farabbi.py` preserves source training/online file phases (shared people/sessions, explicitly pooled across days); `tools/prepare_grasps.py` preserves official days1+2/day3 and verified source MI slice1500:2500. Both pilots passed. `tools/update_dataset_sidecars.py` safely refreshes sensor/case mappings and manifest hashes; its test checks case labels/hashes/leading-zero IDs remain unchanged. Full conversion runner/log/state lives under `.openeegbench/next-batch/` via `.openeegbench/run_next_conversion.py`. Check worker JSON/logs before starting another conversion.


## Compact imagery batch, 8 November 2026

Read `docs/compact-imagery-progress.json` and `docs/compact-imagery-preparation.md`
for the current task; do not restart an active worker. Original source downloads
MIMED19.526MB, MOVING98.204MB and Zhang1.755GB are publisher-MD5/size verified.
`tools/download_compact_imagery.py` and `tools/prepare_compact_imagery.py` implement
this batch; `tools/read_bci2000_native.py` is a strict direct native reader.

- MOVING/ImaginedHandGestures full conversion passed382TRAIN/143TEST,11people,
  17EEG x3000 at500Hz; missing3 source markers and15 globally flat sensors
  documented. Final folder exists on D; registry integration pending in this
  snapshot. Use live progress to determine whether that has since completed.
- Zhang/ImaginedArmTasks720-case pilot passed; full worker
  `.openeegbench/run_compact_imagery.py zhang`, state/log under
  `.openeegbench/compact-imagery/`. Native3.96second cues determine3960points;
  one40sample initial state fragment excluded. Expected4320cases. Anatomical
  sensor names absent in all180nativeheaders: preserve17source column ordinals,
  explicitly flag unknown anatomy/order correspondence, do not infer EGI1-16/E28.
- MIMED full export stopped on85cross-ID duplicate pairs, one conflicting label.
  `tools/audit_mimed.py` reproduces cropped/full-block hashes; detailed audit and
  unposted issue draft saved. None are flatlines. Complete30person data cannot
  pass admission. User asked defer versus explicitly reduced14person subset;
  no subset conversion without their answer. Pilot is not an admitted dataset.
- Pilot caches use separate `pilot-classification-intermediate` (Zhang suffix
  `-3960`) to avoid conflicting with full recording ordinal caches. Existing
  common exporter supports an optional `intermediate_directory` spec field.
- Relevant63tests passed before final registry edits. Refresh code/doc sidecar
  copies and artifact hashes after final descriptions. Original30/results unchanged.


**Compact batch completion update:** MOVING/ImaginedHandGestures and
Zhang/ImaginedArmTasks are now fully validated, registered and in eeg.txt.
Current68registered/64selected. Zhang3240/1080cases,17columns x3960points at1000Hz,
explicit unresolved anatomical sensor flag; MOVING382/143cases,17EEG x3000 at500Hz.
All sidecar/code/doc hashes refreshed;65relevant tests passed and diffcheck passed.
MIMED full30person problem remains unregistered due to85cross-ID duplicate pairs,
one conflicting class. Optional14person cohort requires the user's choice.
No live compact-batch worker remains. Latest checkpoint:
`docs/compact-imagery-progress.json`; D free approximately17.65GB at finish.
Previous Farabbi conversion is complete on D but previous-batch repository
registration/Grasps continuation is separate pending work; do not redownload.


## Active C:/Temp-only batch (8 November)

User paused D: access while moving the drive, then authorised further candidates
under C:/Temp if C has enough space. **Do not access D: at all until resumed.**
Initial C free8.6GB; enforce4GB reserve before jobs. Native sources go to
C:/Temp/EEGSources; final `.ts`/sidecars C:/Temp/EEG; pilot C:/Temp/EEGPilot.

NeuroTUM2025 is fully converted as two original-participant problems:
ImaginedRightHandFeetRest(P1)150/40cases,5sessions; ImaginedLeftRightHandRest(P2)
480/240cases,3sessions. Both24x750,250Hz,three original classes, one person each.
Last native session test, earlier sessions train; intentional participant sharing.
Native XDF sensor names/XYZ recovered; units presumedmicrovolts unchanged;
reference/coordinatephysicalunits unknown. Use pyxdf1.18.0 with sync/dejitterfalse.
Coincident empty markersP1S3 preserved, no EEG timestamp changes. Both passed full
validation; registry integration pending in this snapshot. Worker state/log
`.openeegbench/neurotum/`, tools prepare_neurotum.py/download_neurotum.py,
requirements-neurotum.txt. Existing overlays plus `.openeegbench/xdf-runtime`.

MILimb source access resolved via original public webpage per-file endpoints:
`/public-api/datasets/x8psbz3f6x/files?folder_id=<id>&version=2&$start=0&$limit=1000`
and `/folders/2`. Full ZIP403 does not require manual retrieval: use per-file
publisherSHA256 URLs. Original v2CCBY4.0,3719imagery CSVs561,848,100bytes,60people,
allR1. Root indexed sensor/encoding figures explicitly map16EEG channels; originals
visually inspected. Every CSV500rows16channels+sampleindex. S22I2trial5absent.
Candidate ImaginedHandFootActions,8classes includingbaseline/rest. PilotS1/S60
passed62/62cases,16x500,125Hz. Full download currently session25644; wait until
receipt `pilot=false` and3719imagery files verified before full conversion.
Scripts download_milimb.py/prepare_milimb.py and focused tests exist. No execution
M files downloaded. Sources/metadata1study; no invented continuous offsets/visits.
Progress `docs/temp-c-mi-progress.json`; main source locks/reports in docs.
Batista/Polo are not started because expanded total footprints exceed C capacity.


**C:/Temp batch completion update:** all three new problems are validated and
registered,71total/67selected. Finalarrays C:/Temp/EEG, sources C:/Temp/EEGSources.
D access remains paused: no read/write until the user resumes it. No live worker.
NeuroP1/P2full150/40and480/240,24x750at250Hz; one person each with intentionally
shared participant/disjoint sessions. MILimb full2727/930cases,60people,11x500at
125Hz,8classes. Raw source3719,62ambiguous copied class8rest files acrossS1/S2
excluded symmetrically without choosing a correct owner.5globalflat sensors
removed:F4,FC1,Cz,CP1,T8. Old raw source/pilots untouched; full input3719=3657retained
+62excluded. Header empty/NaN variants affect only sample-index column.
Read `docs/temp-c-mi-preparations.md`, source audit, exclusions and
`docs/temp-c-mi-progress.json`; do not redownload/reconvert these.74relevant tests
passed and diffcheck passed. New sources are2studies,3classification problems.
Batista/Polo still not started due limited C space; preserve4GB reserve. Exact
remaining C bytes and refreshed sizes in the completion report. No uploads.


## Latest update: D drive restored

The user explicitly resumed D access. All three temporary C: preparations are now
in D:/Data/EEG, their two source caches in D:/Data/EEGSources, and pilots beneath
each source cache's pilot-output directory. Every source/destination file was
byte-count/SHA256 verified before removing only the9explicitly named C:/Temp
copies. Source and numeric .ts/NPZ bytes are unchanged; paths/docs/code defaults
and sidecar hashes refreshed. New adapters now default to D:/Data again.
Current71registered/67selected, no new problems added by relocation. Source
grants/splits/exclusions remain unchanged. Read docs/c-temp-to-d-transfer.json,
docs/temp-c-mi-locations.json and live assimilation progress. Old C-only/D-paused
instructions above are historical and superseded by this user-authorised update.
No live transfer/conversion worker remains; no additional EEG downloaded/uploaded.
