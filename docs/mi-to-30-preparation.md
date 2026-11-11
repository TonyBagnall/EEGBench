# Motor imagery additions towards thirty

Work is local on `dataset-assimilation`; no upload or push is authorised.

The primary queue is Pan2023, Pan2025, Rozado2015, Cho2017 and Daly2020.
MIBMPI2024 is a small reserve with explicit noncommercial restrictions.
Admission requires a native-file pilot, complete-cohort audit and source identity
comparison. Different accessions alone do not establish independent recordings.

Original Harvard metadata endpoints returned 403, but public numeric datafile
downloads work. Original publisher-registered DataCite grants establish CC0 for
both Pan deposits and Rozado. Immutable file IDs, sizes, publisher MD5 where
available and locally computed SHA256 are in the source locks. Cho's original
GigaDB grant is CC0, despite MOABB's different licence annotation. Source EEG
remains outside Git under `D:/Data/EEGSources`.

Native epochs are cropped without synthetic concatenation, added filtering,
demeaning, resampling or rereferencing. Conversion uses float64 and exact decimal
round trips. Each case retains its source epoch and crop indices. Epoch-local
indices must never be interpreted as continuous acquisition offsets.

Pan2023 contains no sensor names. Opaque column identifiers therefore preserve
array identity, with the pinned MOABB anatomical mapping separately labelled as
secondary evidence, not recovered native names. Pan2025 embeds its ordered
uppercase channel names and task sample indices. Its second-session first thirty
trials are training; later trials are the original online test phase. Session
one and the second-session training phase are pooled for archive training.

MIBMPI2024 embeds ordered EEGLAB sensor labels/types, reference and coordinates;
coordinate units/frame must remain unknown unless established. Keep the original
one-second baseline outside the 2.5-second task window. Original labels distinguish
imagined screen tap and thumb swipe down. The original Zenodo description grants
CC BY-NC 4.0; its structured licence field is empty. No redistribution release is
being made.

Every adapter uses the existing complete source hash, sensor order, finite/flat,
duplicate, subject split, row alignment, exact numeric readback and aeon smoke
checks. A pilot is not a registered archive problem. Final outputs and counts
are recorded only after the full validation passes.

## Resuming the queue

`python -m tools.run_mi_to_30` continues pilots, downloads, conversions and local registration, stopping on any failed gate. Install the scientific runtime and pyxdf first. Read `docs/mi-to-30-progress.json` and the handover before launching, to avoid competing with existing workers. No uploads or Git pushes are performed.

Native source/pilot states and logs are under `.openeegbench/mi-to-30`. The current background queue was started with the configured scientific overlays. Cho originals support ordinary HTTP ranges; resumable chunks are checked for exact byte ranges, assembled in order and verified against the original MD5 before SHA256 receipt creation. Temporary range files are removed individually only after successful digest verification.

Regression validation at this checkpoint: **100 passed**, covering the preceding adapters, native MI crops, online partition boundary, XDF timestamp lookup, Cho event/sequence ordering, precision and ranged download assembly. Full per-dataset validation and artifact checks remain mandatory.

Disk policy: retain native source files, pilot outputs and validated final arrays. The unattended runner clears only this batch's full `classification-intermediate-full/recording-*.npz` files after complete numeric validation and final artifact verification, and records this in dataset metadata. These files can be rebuilt deterministically. This avoids accumulating both full float64 caches and large text exports on D.

## Completed full preparations

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---|---|---|---|---|---|---|---|---|
| ImaginedHandsOnline | 2123 | 1519 | 10 | 28 | 1000 | 2 | 250 | 1.893 | CC0-1.0 |
| ImaginedHandsCrossSession | 2400 | 960 | 14 | 28 | 1000 | 2 | 250 | 1.780 | CC0-1.0 |
| ImaginedHandPupils | 1150 | 400 | 30 | 32 | 3072 | 2 | 512 | 2.538 | CC0-1.0 |
| ImaginedHandsPhysiology | 7880 | 2640 | 52 | 64 | 1536 | 2 | 512 | 10.694 | CC0-1.0 |
| ImaginedHandMusicTempo | 1698 | 643 | 18 | 19 | 20000 | 2 | 1000 | 16.816 | CC-BY-4.0 |

All five are complete and registered locally:82registered,78selected,30MI including29scalp EEG and1ECoG. Daly retained1698TRAIN/643TEST after removing both ambiguous09/15run10 recordings; no retained duplicate cases or shared subjects. User confirmed reporting to OpenNeuro on9November2026. All arrays passed exact float64 readback; aeon fit/predict is a compatibility smoke test on3cases/class/split.
