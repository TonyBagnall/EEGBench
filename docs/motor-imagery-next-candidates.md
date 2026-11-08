# Small motor imagery candidates, 8 November 2026

Metadata and pinned-loader survey only: no new EEG files were downloaded in
this survey. Compare accession/recordings with our existing provenance before
admission. Existing archive arrays and results are unchanged.

## Recommended queue

Prioritise compact motor imagery recordings with original-host-confirmed open
data licences. All four below have original-host **CC BY 4.0** evidence. Sizes
are decimal MB/GB for the selected original compressed files, not final `.ts`
sizes. Counts and dimensions remain planning values until native-file checks.

| Priority | Source | Imagined task | Participants | EEG / Hz | Selected source download | Main admission checks |
|---:|---|---|---:|---|---:|---|
| 1 | [MIMED2024](https://data.mendeley.com/datasets/zs25xxjkm9/3) | Left-hand raising/lowering, right-hand raising/lowering, standing/sitting: three folder-level classes | 30 | 14 / 128 | **19.526 MB** | Recover actual array channel order from primary evidence; distinguish source blocks, days and timing assigned from protocol. Do not invent six directional labels. |
| 2 | [MOVING2024](https://zenodo.org/records/12804784) | Right-hand opening/closing, wrist rotation, finger tapping, plus rest | 11 | 32 / 500 | **98.204 MB** EEG-only `edf.rar` | Native EDF channel names and annotations; verify units, trigger windows and MI versus executed intervals. Fixed movement order is a protocol confound. |
| 3 | [Zhang2017](https://doi.org/10.6084/m9.figshare.5579461.v1) | Nine elbow-centred imagined actions plus rest, including lifting, opening a door and combing | 12 | 17 / 1000 | **1.755 GB** `KI.rar` | Check native sensors, variable cue durations and trial counts; no guessed fixed 5-second windows across shorter trials. |
| 4 | [Kodera2023](https://zenodo.org/records/7893846) | Left versus right hand | 29 reported | Cohort-dependent | **1.774 GB** `data.zip` | Existing inspection found two sensor/rate cohorts and unresolved participant correspondence. Do not silently pool cohorts or assume all files have the nine-channel/500-Hz headline structure. |

MIMED is the strongest next pilot. The original imagery-only archive is exactly
19,526,072 bytes, verified by HTTP HEAD; the full Mendeley record also contains
execution and feature products which are unnecessary for this task. The pinned
loader exposes 12 windows per participant (360 nominal cases), each
14 x 512 samples: approximately **0.0206 GB float64** before export. This is a
loader-derived planning interpretation, not a measured native case count. Source
folders support three activity families; they do not establish separate up/down
labels for every repetition. Source channel order, timing and reported day
groupings must be independently checked rather than inherited unquestioningly
from loader constants. Native offsets can be large; do not confuse them with
flat signals or apply blanket voltage rescaling.

MOVING needs only `edf.rar`, not the accompanying 2.349-GB virtual-glove archive.
The nominal MI subset has 48 cases per participant (528 total), 32 x 3000 at
500 Hz: approximately **0.406 GB float64**. Anatomical EEG names are expected in
the EDF headers; accelerometer channels remain auxiliary. Its imagined and
executed task views share the rest intervals, so they must not be counted as two
wholly independent recording collections. The original pinned Zenodo v1 record
advertises a newer version: inspect that version's changes before choosing the
release for conversion.

## Small sources with outstanding issues

- [NeuroTUMBCI2025](https://zenodo.org/records/18087806): **306.528 MB** including
  calibration, 24 EEG at 250 Hz, two participants with five/three sessions.
  Original-host CC BY 4.0 confirmed. Participant 1 uses rest/right hand/feet;
  participant 2 uses rest/left hand/right hand. The four-label union is not a
  common four-class task. A subject-disjoint split would leave labels unseen in
  training or test. Consider an explicitly documented session split or an
  explicitly chosen common-label task, rather than silently dropping classes.
- [Shin2022](https://doi.org/10.6084/m9.figshare.20383716): **353.216 MB**, ten
  participants, 16 channels at 250 Hz, left/right cursor-control imagery.
  Original-host CC BY 4.0 confirmed. The recording archive contains real LIVE EEG
  and SIMULATED cursor telemetry; only LIVE is appropriate. The pinned loader
  reports no anatomical sensor labels in BCI2000 headers and generates EEG1-16.
  These are not recovered electrode identities. Recover the original mapping
  before accepting it. Check the nominal 11 runs against the paper's ten-run
  description for duplicate recordings, and respect variable feedback durations.
- [MILimbEEG](https://data.mendeley.com/datasets/x8psbz3f6x/2): low-rate 16-channel
  data at 125 Hz, 60 participants, eight labels including baseline/rest and
  hand/foot tasks; original release CC BY 4.0. Exact imagery-only file total has
  not yet been verified, so it is not ranked by a guessed download size. The
  release mixes execution/imagery, repeated runs and heterogeneous clinical
  backgrounds. Native IDs and sensor order need inspection.

## Larger reserves

Original-host API totals: Batista2022 **2.863 GB**, PoloHortiguela2025
**2.936 GB**, Perdikis2018 **4.681 GB**, Alawieh2025 **18.288 GB** including
non-EEG material. All four original records declare CC BY 4.0. They are lower
priority by download size; these are full-record totals and may include
unnecessary auxiliary products. Clinical/repeated-session coverage makes them
useful later. Cho2017, OpenBMI and Dreyer2023 remain larger-cohort reserves.

BCI Competition III IVa is compact but its original redistribution grant remains
unresolved. BNCI2014_002 still has the sensor-name provenance issue already
documented. Neither becomes admission-ready merely because its loader runs.
Already prepared MI sources, including ImaginedGripForce, ImaginedHandTraining,
ImaginedHandsStroke and the completed ImaginedHandsRobot conversion, are excluded
from this new queue. ImaginedGrasps belongs to the existing batch, not a new
candidate.

## Reproducibility

Original record API evidence and pinned MOABB loader snapshots are in
`source-evidence/motor-imagery-survey/`. File sizes, publisher checksums, loader
hashes, MIMED archive headers and priorities are recorded in
[motor-imagery-candidate-inspection.json](motor-imagery-candidate-inspection.json).
Loader commit: `bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`.
MOABB declarations were checked against original Zenodo/Figshare/Mendeley records;
the software licence was not used as a data grant.

Follow [the conversion handover](../DATASET_CONVERSION_HANDOVER.md): verify native
metadata and hashes, run one participant through the full `.ts`/sidecar pipeline,
then expand after pilot validation. Final text storage can greatly exceed the
compressed download; check D-drive space before bulk retrieval.


## Subsequent preparation audit (8 November)

The user authorised all first three. Original archives are downloaded and verified.
MOVING is converted as ImaginedHandGestures (382/143cases,17EEG). Zhang is fully converted as ImaginedArmTasks (3240/1080cases) after a720case pilot; native anatomical
channel names remain unresolved and explicitly flagged. **MIMED has now failed
full source duplicate admission**:85cross-ID duplicate pairs, including one
conflicting class. Its earlier priority was a metadata-only recommendation;
it is not currently an admission-ready30participant problem. See the
[preparation report](compact-imagery-preparation.md) and
[source audit](mimed-native-quality-audit.json).


## Remaining queue after MOVING/Zhang

Additional verified-licence source candidates remain: Batista2022 (20 reported
participants, left/right imagination under VR/haptic conditions, original
record2.863GB) and PoloHortiguela2025 (six participants, ankle imagination/rest
with static/moving exoskeleton conditions, original record2.936GB). Both original
records are CC BY4.0. Perdikis2018 is4.681GB and has generic native sensor labels;
recover its exact sensor mapping before admission. MILimbEEG is low-rate16channel
MI/execution data from60 participants, CC BY4.0 at the original host; imagery-only
file size is still unverified.

Smaller but qualified: NeuroTUM306.528MB has different three-class vocabularies
for its two participants; Shin2022353.216MB has unresolved original anatomical
sensor mapping; Kodera1.774GB mixes two sensor/rate setups and unclear cross-date
participant identity. Those issues remain admission checks, not reasons to guess
sensor names, pool identities or silently discard labels.

Pan2023 (14people,two days) and Pan2025 (10people) are further low-rate28channel
left/right MI candidates. Original Harvard Dataverse metadata API requests
returned HTTP403 in this follow-up, so precise source sizes/licence applicability
were not independently reconfirmed. That API response does not establish that
users need approval to access the data. No EEG downloaded in this follow-up.


## Completed under C:/Temp while D: is offline

NeuroTUM is prepared as two single-participant session-transfer problems:
ImaginedRightHandFeetRest150/40cases and ImaginedLeftRightHandRest480/240cases,
24x750 at250Hz,3classes each. One study, two distinct individuals; exact native
sensor names/positions recovered. MILimb individual-file access was resolved:
ImaginedHandFootActions2727/930cases,60people,11x500at125Hz,8classes. All62copied
rest epochs across S1/S2 excluded symmetrically and5flat sensors globally removed;
source cases unchanged and complete evidence retained. These are prepared, no
longer new-source candidates. Current71registered/67selected. See
[temp-C batch details](temp-c-mi-preparations.md). D: was not accessed.
Batista/Polo remain queued because their full footprints exceed the C budget.
