# SymbolAttention

Prepared 6 November 2026 from **Chailloux2020 / OpenNeuro ds003190 v1.0.1**. Classify attended target versus non-target symbols in a single-option P300 interface, with recordings varying stimulus count and stimulation type.

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SymbolAttention | 521259 | 175180 | 19 | 8 | 256 | 2 | 256 Hz | 27.83 | CC0-1.0 |

Outputs: `D:/Data/EEG/SymbolAttention/`, standard TRAIN/TEST `.ts`, ordered case TSVs, channel tables, dataset metadata, attribution, validation and hash manifest. Compressed float64 NPZ intermediates and original sources are separately under `D:/Data/EEGSources/Chailloux2020/`. Dense float64 arrays require about 11.41 GB before loader/model overhead. No upload has been made.

## Provenance and licence

Original [release](https://openneuro.org/datasets/ds003190/versions/1.0.1), data DOI [10.18112/openneuro.ds003190.v1.0.1](https://doi.org/10.18112/openneuro.ds003190.v1.0.1), Git revision `153d0a1633adbf7d079eeabc866a2ad727bcff46`. The original dataset description and dataset-named LICENSE both establish CC0, independently from MOABB's software licence. [Licence evidence](symbol-attention-licence-evidence.json); [file/version/checksum lock](symbol-attention-source-lock.json).

Other names: Chailloux2020; Single-Option P300-BCI; original title *Assesment of the visual stimuli properties in P300 paradigm*. The pinned MOABB loader declares raw mirror `on003190`; NEMAR `nm000262` is a derivative of the same OpenNeuro collection, not another independent study.

Reference: Chailloux Peguero, Mendoza-Montoya and Antelis (2020), *Single-Option P300-BCI Performance Is Affected by Visual Stimulation Conditions*, Sensors 20(24):7198, [paper DOI 10.3390/s20247198](https://doi.org/10.3390/s20247198). Independent loader revision: `bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`.

## Participants, splits and labels

Nineteen participants, **56 available sessions**. Participant `019` has sessions `01`/`03`; session `02` is absent. Native IDs `01`-`09` and `010`-`019` remain strings. Whole numeric IDs 1-14 form TRAIN; 15-19 form TEST. All available cnos/ctos conditions are pooled as one classification problem. Order: participants numerically, native session token and filename, then native flash-marker order. No shuffle or archived validation; no subject or recording crosses splits. Source has no fixed train/test protocol.

Encoded `1=NonTarget`, `2=Target`. TRAIN: 438,917 non-target / 82,342 target; TEST: 147,485 / 27,695. Native block marker10X identifies attended symbol X; compare each native flash1-9 to X. Reset target at every block boundary. Original symbol, target, marker ordinal, block, sample position and encoded label are preserved separately. Native F/H condition codes are retained; their SF/CF correspondence is not invented.

The source contains 384 BrainVision files, including two no-flash placeholders. Fifteen nominal protocol files are absent. A copied recording is excluded, leaving **381 included recordings**. [Complete source inspection](symbol-attention-source-inspection.json).

## Source issues and explicit exclusions

- Subject `01`, session `03`, cnos/run7 has 179 flashes without an attended-target marker in the current block. Exclude these rather than carry a stale target from another block.
- Subject `019`, sessions `01`/`03`, ctos/run5H have no flashes and ten unnamed placeholder channels. Exclude them without assigning scalp names.
- Subject `011`, session `03`, ctos/run5H is an exact copied binary of session `02`/ctos/run5H, with identical native marker stream and BIDS event table. Retain the earlier copy; exclude the later 1,392-flash copy with source path/hash evidence. Original labelled total 697,831 becomes **696,439 unique retained cases**. The initial unfinished export was stopped and its verified staging directory removed before publication; conversion restarted with source-case hash preflight.
- Subject `016`, session `02`, cnos/run6 contains symbols1-7 despite filename-derived grid6. Preserve both fields; category encoding uses native target/flash equality, not the filename's grid number.

## Sensors, units and timing

All included VHDR and BIDS tables agree on native order **FZ, Cz, P3, PZ, P4, PO7, PO8, Oz, Timestamp**. Retain the first eight documented EEG sensors, excluding Timestamp. Preserve original spelling/order; no flat or effectively flat EEG channels were found. BIDS labels all inputs unknown and EEGChannelCount0, contradicting the original sensor description; role evidence and that discrepancy are explicit. Native EEG JSON and README give **M2/right-mastoid reference**, README AFz ground. Individual coordinates are unavailable; no synthetic montage is assigned.

One-second windows contain 256 samples starting at native VMRK position minus one. BIDS sample fields equal one-based VMRK positions, whereas onset seconds use zero-based positions; conversion explicitly reconciles them. Epochs overlap within recordings but not across subject partitions. Original data are continuous, so newly formed epoch ordinals are distinguished from recovered marker IDs.

Native float32 values are cast directly to float64 unchanged. Physical unit is omitted in VHDR and unknown in BIDS: **microvolt interpretation is inferred** from BrainVision/MNE convention and amplitudes, factor1, not directly recovered. No filtering, baseline, reference change or resampling is added. Pre-distribution acquisition filtering remains unknown.

Native Timestamp endpoints are retained per case and recording. Large absolute timestamps were already quantised upstream as float32 (pilot step131,072); their units/timebase are unspecified. They cannot recover precise event times. Use native sample indices; float64 cannot restore upstream precision.

## Validation and completeness

Two-subject pilot passed before full download. Full exact float64 `.ts` readback, case/hash/row/label alignment, sensor ordering, finite values, class counts, subject separation and duplicate tests passed. No exact duplicate cases within/across splits or remaining flat/tiny sensors. An aeon loader/classifier smoke test passed on three cases/class/partition; the complete archive was stream-validated, not fitted as one giant model.

Direct fields: participant/session/run/file, native marker/block/symbol/sample information, timestamp values, fs, names/order. Documented: EEG roles, reference, ground and stimulus protocol. Assigned/inferred: case encoding, whole-subject split, new window ordinal and presumed microvolt units. Missing: individual demographics/coordinates, explicit physical units, precise original timestamps and acquisition filters. [Machine completeness](symbol-attention-metadata-completeness.json); [measured results](symbol-attention-conversion-result.json).

## Reproduce

Use dependencies in `tools/requirements-moabb.txt`:

```powershell
python -m tools.download_chailloux --root D:/Data/EEGSources/Chailloux2020
python -m tools.prepare_chailloux --cache-root D:/Data/EEGSources --output D:/Data/EEG
```

`--pilot` selects subjects01/019. Git-annex content hashes pin mutable S3 downloads to the immutable release. Cached NPZ data must match freshly decoded cases exactly; source-case duplicates are checked before export. Final folders are not overwritten.
