# ArmCoordination / Kueper2024

Prepared and validated, 6 November 2026. Classify executed right-arm-only versus synchronous both-arm reaching. This follows the pinned MOABB condition mapping, not imagined movement and not the original paper's movement-versus-rest transfer classifier.

Original source: [Zenodo10229480](https://zenodo.org/records/10229480), [dataset DOI](https://doi.org/10.5281/zenodo.10229480), CC BY4.0 verified in original record metadata. The pinned3.101GB zip expands to3.347GB, with8 participants and49 physical recordings. [Source lock](arm-coordination-source-lock.json). Paper: Kueper, Kim and Kirchner(2024), Scientific Reports14:16690, [DOI10.1038/s41598-024-65910-8](https://doi.org/10.1038/s41598-024-65910-8).

Native layout is67 channels:64 EEG in embedded uppercase order, plus x_dir/y_dir/z_dir accelerometers in mg. Preserve all EEG names/order without case normalisation. Explicit header EEG resolution is0.0406901 microvolts/count in the inspected file; cast binary float32 counts to float64 before multiplying by native per-channel resolution. Exclude accelerometers. No new filtering, reference, baseline or resampling. Source README supplies FCz reference and AFz ground; individual sensor coordinates are unavailable.

Use native motion-tracking onset S100 for unilateral/right arm and S101 for bilateral/left arm, as in the pinned loader. Epoch from -2 to+1sec, end exclusive:1500 samples at500Hz, final sample+0.998sec. Native marker positions are one-based; original keys repeat, so preserve marker key AND unique line ordinal. Compare selected native sample positions independently with MNE annotations.

The nominal3x40 trials/condition differs from distributed data:2003 native selected onsets, all inside S8/S9 active-phase markers. Retain all onsets, including extra/error-flagged episodes, and preserve native S3(error), S27(excluded-event), S128(correct-trial end), plus undocumented S26/S28. Per-case flags refer to markers between consecutive selected onsets; this association is explicitly not a recovered original trial ID. No guessed valid-trial repair. Discontinuity or incomplete-window exclusions will be reported.

XP01 unilateral set4 continues interrupted set3; source text says the two together complete a logical40-movement set. It is not an additional40-trial session. Keep both physical files, never crop across their boundary. Whole-participant split: alphabetic native IDs AV82/JD68/JV43/QS70/RA12/UP28 TRAIN, XP01/ZS27 TEST. Native expected counts before window checks:1498train/505test. No archived validation.

Subject age, gender, handedness, experiment date, cap-size token and run notes are recovered from original participant text files. Session grouping uses the date token in native filenames, qualified as an assigned grouping because original visit IDs are absent. AV82 participant metadata's listed filenames contain20211210, while its experiment-date field and actual filenames agree20211220; retain the discrepancy. Original marker datetimes have no established timezone.

Filter evidence is preserved from both native tables: amplifier DC/131Hz; software time constant1.59155s(approximately0.1Hz)/249Hz, notchOff. MNE's parsed lowpass249Hz explicitly ignores the hardware131Hz field. The publication describes effective0.1-131Hz. Retain the original header and distinguish these sources; do not pretend MNE's single value fully describes acquisition filtering.

A pilot with AV82 train/ZS27 test passed before full conversion. Full .ts numeric readback, label/case alignment, source-order sensor checks, exact duplicate tests, subject separation and flat-channel policy passed. An aeon classifier smoke test passed on three cases per class per split. Source files/intermediates remain separately on D, no data arrays in Git and no uploads.


## Measured preparation

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ArmCoordination | 1498 | 505 | 8 | 64 | 1500 | 2 | 500 Hz | 3.65 | CC BY 4.0 |

TRAIN:738 unilateral /760 bilateral. TEST:245 unilateral /260 bilateral. All2003 native selected onsets produced complete epochs, with no discontinuity-window exclusions. No flat/tiny sensors or duplicate cases were found, and no participant/recording crosses the split. All49 native sensor tables and binary/marker filename pairings agree. Source VMRK keys repeat; unique source line ordinals were preserved rather than losing markers in a dictionary.

Output: `D:/Data/EEG/ArmCoordination/`, with TRAIN/TEST .ts, ordered case tables, channel table, metadata, attribution, validation and manifest. Original zip, extracted recordings and compressed numeric NPZ intermediates remain separately in `D:/Data/EEGSources/Kueper2024/`. Source cache extraction checks ZIP CRC before reusing a same-sized file. [Measured result](arm-coordination-conversion-result.json), [metadata completeness](arm-coordination-metadata-completeness.json).

```powershell
python -m tools.download_kueper --root D:/Data/EEGSources/Kueper2024
python -m tools.prepare_kueper --cache-root D:/Data/EEGSources --output D:/Data/EEG
```

Use dependencies in `tools/requirements-moabb.txt`; `--pilot` selects AV82/ZS27. Existing final outputs are not overwritten. No upload has been made.
