# WalkingTargets

Prepared 6 November 2026 from BCIComp2020WalkingERP, the 2020 International BCI Competition Track 5 / Data Set-E. Classify attended target **OOO** versus non-target **XXX** visual stimuli during treadmill walking at 1.6 m/s. This is a different recording task from ImaginedCommands (Track 3), although they share an OSF project and review paper.

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| WalkingTargets | 3600 | 900 | 15 | 42 | 100 | 2 | 100 Hz | 0.36 | CC BY 4.0 |

Files are in `D:/Data/EEG/WalkingTargets/`: TRAIN/TEST `.ts`, ordered case TSVs, dataset metadata, channels, validation, attribution and hash manifest. Sources and compressed float64 NPZ intermediates remain under `D:/Data/EEGSources/WalkingERP/`; no large data are stored in Git.

## Source and redistribution

The [original OSF project](https://osf.io/pq7vb/) explicitly links CC BY 4.0 for its data, separately from MOABB's software licence. See [original licence evidence](walking-targets-licence-evidence.json) and [the source lock](walking-targets-source-lock.json): 48 files pinned by OSF ID, version and SHA256, totalling 0.301 GB. No original dataset DOI was independently established. The reference paper is Jeong et al. (2022), *2020 International brain-computer interface competition: A review*, Frontiers in Human Neuroscience 16:898300, Data Set-E, [DOI 10.3389/fnhum.2022.898300](https://doi.org/10.3389/fnhum.2022.898300). Independent MOABB loader revision: `bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`.

## Participants, labels and partitions

Fifteen participants contribute 300 walking trials each. The organiser documents ages 19-32, 11 male and 4 female; individual demographics were not recovered. The 45 distributed MAT epoch files represent three partitions per participant, from 15 documented walking sequences. Original continuous filenames and visit/session/run IDs are unavailable; unknown IDs remain unknown. Subject IDs `01`-`15` remain strings.

The official first 180 trials/person are training, next 60 validation and final 60 test. Archive TRAIN concatenates all training files then all validation files, sorting subjects within each phase and preserving native epoch order. TEST is unchanged. **All 15 subjects intentionally occur in both partitions**: this measures later trials from known participants. No validation split is archived.

Encoded labels: `1=NonTarget_XXX`, `2=Target_OOO`. TRAIN has 2,897 non-target and 703 target cases; TEST has 699 non-target and 201 target cases. Native training/validation class names and one-hot labels agree with `event.desc` (1/2). Test labels come from the test-folder **True Label** workbook (0/1), independently matched against the pinned loader. The root prediction-probability submission template is not ground truth. Subject 11 has 64 targets in 300 trials despite the nominal 20% ratio; published labels are preserved.

## Sensors, numeric values and preprocessing

All 45 MAT files agree on 56 inputs in embedded `clab` order: 32 scalp EEG, four EOG, 14 ear EEG and six IMU. Select EEG without reordering. Four ear sensors are then removed globally under the archive flat-channel policy: **L1, L2, R1, R4**, native zero-based indices **36, 37, 44, 46**. They have respectively 297, 286, 404 and 300 constant case/channel pairs: **1,287 pairs across 704 cases**. No cases are removed. `channel-removal-audit.tsv` traces affected cases to source epochs and verified exported waveform hashes. Final arrays contain **32 scalp and 10 ear EEG**.

Native float64 values and 100 samples at 100 Hz are preserved; native epoch time runs from -190 to +800 ms inclusive, with stimulus zero at local sample 19. No additional filtering, padding, re-epoching, baseline, referencing or rescaling. Microvolt units are **inferred** from MATLAB/EEG-loader convention and amplitudes; no explicit physical-unit field was recovered. Original acquisition rate and pre-distribution filtering are unknown.

Native `mnt` scalp x/y and 3D coordinates are retained without assigning unknown units/frame or individual measured geometry; ear positions are absent. The original PDF diagram shows scalp REF between FC1/FC2 and GND between Fp1/Fp2. Nominal FCz/Fpz names are positional inferences; ear reference remains unknown. No reference channel or standard montage is invented.

## Completeness and validation

Direct: subject/file/partition, local epoch index, native labels and test-label cells, array axes, sensor names/order, source frequency, epoch-relative times and montage values. Documented: sensor roles, protocol, aggregate demographics and split. Inferred: global trial ordinals, walking grouping, presumed microvolt units and nominal scalp reference names. Missing: continuous sample offsets, acquisition filename, session/run IDs, ear geometry/reference and acquisition frequency. Continuous cross-split overlap is consequently **unknown**, not reported as zero. Sample indices are explicitly epoch-local.

Each participant's identical 60-second standing calibration is repeated in all three files; its role and hashes are preserved, but it is not included as cases or another independent problem.

A one-subject pilot preceded full conversion. Full numeric `.ts` readback, case hashes/order, shapes, labels and native sensor identity passed. No duplicate cases within/across splits or remaining flat sensors were found. An aeon load/fit/predict smoke check passed. Intentional subject overlap is explicitly reported.

## Reproduce

Use `tools/requirements-moabb.txt` dependencies:

```powershell
python -m tools.download_walking_erp --root D:/Data/EEGSources/WalkingERP
python -m tools.prepare_walking_erp --cache-root D:/Data/EEGSources --output D:/Data/EEG
```

Use `--pilot` for subject 01. Downloads verify hashes; conversion refuses to overwrite an existing final dataset. Metadata distinguishes recovered facts from inferences. No upload has been made.
