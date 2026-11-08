# Motor imagery batch: restored to D drive

Originally prepared8November2026 under C:/Temp while D: was offline. The user
has now resumed D: access. Final `.ts`/sidecars are in **D:/Data/EEG/**; sources
and compressed intermediates in **D:/Data/EEGSources/**. Pilots are under each
source cache's `pilot-output/`. Every copied file passed byte-count/SHA256 checks
before the named C: copies were removed. Numeric arrays are unchanged.
[Machine-readable transfer verification](c-temp-to-d-transfer.json).

| Dataset | Train | Test | Subjects | Channels | Points | Classes | Hz | Approximate final GB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ImaginedRightHandFeetRest | 150 | 40 | 1 | 24 | 750 | 3 | 250 | 0.060 |
| ImaginedLeftRightHandRest | 480 | 240 | 1 | 24 | 750 | 3 | 250 | 0.222 |
| ImaginedHandFootActions | 2727 | 930 | 60 | 11 | 500 | 8 | 125 | 0.387 |

All original data grants are CC BY4.0. Exact refreshed sizes, source paths and
validation are in the result JSONs; totals may change slightly with prose.

The NeuroTUM problems are two participants from one study with different native
three-class maps, deliberately separate problems. They use session transfer:
same person shared intentionally, final native session test, earlier sessions
train. Native XDF names/order/coordinates and markers recovered, original numbers
cast float64 unchanged. Physical microvolt interpretation is inferred; coordinate
units/frame and original reference are unknown. No replacement standard montage,
clock fitting, dejittering, filtering, resampling or rereferencing.
[NeuroTUM source identity, exact splits and completeness](neurotum-preparation.md).

MILimb uses original imagery files only, including its baseline/rest classes;
execution files are not downloaded. Whole subjects split45/15. It is an explicit
source-quality subset:31copied rest pairs across S1/S2 are all excluded (62cases),
with no guessed true owner. The rest of their trials are retained. One S22
left-hand trial is absent in the source. Five globally flat/effectively flat
sensors removed: F4,FC1,Cz,CP1,T8. Original CSV values/labels are unchanged apart
from the documented case/sensor selections; publisher hashes and excluded epoch
list retained. Native numeric columns map through the author's numbered sensor
graphic. Original continuous offsets and session visits remain unknown.
[Full MILimb audit, source mapping and exclusions](milimb-preparation.md).

These add **three problems from two studies**, bringing the registry to71 and
eeg.txt to67. Original30problem/results subset unchanged. No uploads. Source
snapshots, exact file revisions/checksums and executable conversion code accompany
each dataset. Every retained case passed full float64 `.ts` readback, row/hash/
label alignment, channel/order checks and duplicate/flat checks, plus aeon
load/fit/predict smoke on three cases/class/partition. No cross-person identical
case was found between the two NeuroTUM problems.

Use each supplied split; there is no separate archived validation set. For these
new files, point local loading at D:/Data/EEG. Normal D-drive defaults are restored
in the standalone adapters. The temporary C: copies have been removed after verification.

The next larger Batista/Polo sources were not started during C: staging because
their full footprints exceeded its budget. They remain queued; this relocation
downloaded no additional EEG. A4GB free-space reserve was checked before each job. See
[live completion/storage checkpoint](temp-c-mi-progress.json) and
[agent conversion handover](../DATASET_CONVERSION_HANDOVER.md).
