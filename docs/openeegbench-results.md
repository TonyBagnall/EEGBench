# OpenEEGBench candidate preparation results

Pinned inputs and commands are documented in `docs/openeegbench-import.md` in the repository.
The existing 30 datasets and results are unchanged. No data were uploaded.

Counts for an unconverted candidate are from inspected source metadata, not verified signal arrays.
Sizes are decimal GB for complete converted directories, excluding source cache and separate .ts exports.

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---|---|---|---|---|---|---|---|---|
| arithmetic_zyma2019 | 1515 | 192 | 36 | 19 | 1000 | 2 | 200.0 | 0.113 | ODC-By-1.0 |
| bcic2020-3 | 5250 | 750 | 15 | 64 | 600 | 5 | 200.0 | 0.751 | CC-BY-4.0 |
| chbmit | 34045 | 2140 | 22 | 17 | 2000 | 2 | 200.0 | 4.120 | ODC-By-1.0 |
| faced | 15629 | 3588 | 123 | 26 | 2000 | 8 | 200.0 | - | unverified (NEMAR: CC-BY-4.0) |

## Conversion status

- `arithmetic_zyma2019`: converted and validated.
- `bcic2020-3`: converted and validated.
- `chbmit`: converted and validated.
- `faced`: metadata only; original licence unresolved.

## Metadata completeness

Available case counts; a dash means absent. All inspected recordings have ordered channel names and FIFF channel kinds.

| Dataset | Subject | Session | Run | Recording/source file | Distributed epoch index | Original trial/video ID | Processed sample bounds | Original sample bounds | Original Hz from BIDS |
|---|---|---|---|---|---|---|---|---|---|
| arithmetic_zyma2019 | 1707 | - | - | 1707 | 1707 | - | 1707 | - | 1707 |
| bcic2020-3 | 6000 | - | 6000 | 6000 | 6000 | - | 6000 | - | 6000 |
| chbmit | 36185 | - | 36185 | 36185 | 36185 | - | 36185 | - | - |
| faced | 19217 | - | - | 19217 | 19217 | 19217 | 19217 | - | 19217 |

## Findings and exceptions

- faced: source metadata contains 8 classes [0, 1, 2, 3, 5, 6, 7, 8], while OpenEEGBench declares 9. No missing class was invented or relabelled.
- mdd_mumtaz2016: excluded and signal arrays/export removed. 121 distinct upstream windows crossed train/test (726 affected training cases, 484 test cases, 2904 matching pairs). Only diagnostic evidence remains; see docs/issues/mdd-duplicate-windows.md.
- BCI 2020-3 intentionally uses a within-subject run split. Its 15 subjects are shared across merged training and test.
- CHB-MIT's chb24 is excluded by the upstream fixed masks (861 metadata windows). chb01 and chb21 are one physical participant; 23 retained case IDs correspond to 22 known participants.
- CHB-MIT's 17 distributed channel names are renamed bipolar derivations. Their original pairs are retained; no monopolar positions are invented.
- No dataset provides explicit session IDs. Distributed window/epoch row indices and processed-recording sample intervals are available, but original acquisition trial IDs and sample indices are generally unavailable.
- All five inspected releases lack usable stored XYZ sensor positions, and the consulted original BIDS metadata contain no electrode-position sidecars. Channel names and FIFF types are known; positions remain unknown and no synthetic montage was added.
- FACED provides video identifiers. Original acquisition frequency is matched from separate BIDS sidecars for Arithmetic, BCI 2020-3 and FACED; 120 MDD cases have no exact original-sidecar match. CHB-MIT's original 256 Hz is source-reported, not recovered per example.
- FACED signals were not downloaded: original Synapse redistribution terms could not be verified, despite CC-BY-4.0 on the NEMAR derivative. The HF cards all declare licence unknown.
- Arithmetic .ts pilot: all converted examples reload with identical float32 values and labels; an aeon SummaryClassifier fit/predict check passed on reloaded arrays. Evidence: pilot-ts-roundtrip.json in the local data root.

Metadata values are directly recovered unless labelled as derived or inferred. Per-recording MNE Info and original source sidecars retain position/reference information where present; null positions remain unknown. See each dataset's JSON, case tables and validation report for full details. Depression/MDD is excluded from download/export choices; its signal arrays were removed and only diagnostic reports remain. See docs/additional-datasets.md for local names and descriptions.
