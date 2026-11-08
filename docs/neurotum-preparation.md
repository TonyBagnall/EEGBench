# NeuroTUM: two single-participant motor imagery problems

**Current location:** D:/Data/EEG, sources D:/Data/EEGSources, restored by verified transfer. C:/Temp references below describe the original staging history; temporary copies are now removed.
Started8November2026. User moved D: elsewhere: **no D-drive access**. Sources and
outputs temporarily live under C:/Temp/EEGSources and C:/Temp/EEG. Initial C free
space approximately8.6GB; retain at least4GB before each conversion.

Original [Zenodo18087806 v1.0.0](https://zenodo.org/records/18087806), data DOI
10.5281/zenodo.18087806, neuroTUM e.V., original CC BY4.0 data grant. Reference
Tscherniak et al.,10.48550/arXiv.2511.23384. These are two people from **one study**,
not two independent studies. Original files have publisher MD5s and pinned byte
counts, local SHA256s and original metadata in the source lock/receipt. ASR
calibration recordings are separate unlabelled material and excluded.

P1 forms **ImaginedRightHandFeetRest**, three classes: rest, imagined right hand,
imagined legs/feet. Native sessionsS1-S4 train,S5test. P1 is documented as the
tetraplegic pilot. P2 forms **ImaginedLeftRightHandRest**, rest/imagined left hand/
imagined right hand, S1-S2train,S3test; P2 is documented as able-bodied. These
are archive-defined session-transfer splits. Each intentionally shares its one
participant across disjoint source session files; neither estimates transfer to
unseen participants. No validation archive and no dropped classes.

Native XDF descriptors supply exact24channel labels, EEG stream type and XYZ
positions. Preserve native uppercase/mixed spelling instead of loader spellings.
The source geometry's physical units/frame and individual measurement status are
unknown; no standard montage is substituted. Reference/ground not recovered.
Native physical unit fields are absent; Smarting numeric values are presumed
microvolts following source interpretation and amplitudes, cast float64 with
multiplier1. Any authorised global flat removals are recorded in the sidecars.

Epochs use the original YAML mapping **BLACKSCREEN** markers, nearest actual EEG
sample on native shared-host LSL timestamps,750samples at nominal250Hz (3seconds).
Check monotonicity, no within-window gap, sufficient samples and next marker
outside the crop. Preserve source marker index/time, source samples, alignment
error, native stream descriptors/footer and clock offsets. pyxdf1.18.0 runs with
clock synchronisation and timestamp dejittering **disabled**; no signal filtering,
resampling, rereferencing or demeaning. LSL monotonic times are not UTC/dates.

Both two-session pilots and full conversions passed. Final P1:
TRAIN `(150,24,750)`, TEST `(40,24,750)`, five native sessions. P2:
TRAIN `(480,24,750)`, TEST `(240,24,750)`, three native sessions. Both250Hz,
three classes, no flat channels removed, original values preserved asfloat64.
No within/across-split duplicate cases or overlapping source windows; all case
rows/labels/hashes match complete numeric readback. Aeon load/fit/predict smoke
passed using three cases per class per partition. Shared participant is the
intended task; sessions/source files are disjoint.

Native P1S3 marker entries62/63 are coincident empty strings. They are preserved
with original ordinals in the marker metadata and do not define class cases;
no sorting/dropping or signal changes are needed. EEG timestamps are strictly
increasing in all8session files. See `neurotum-native-timing-audit.json`.
The two problems have distinct individual recordings but one common study/source
accession. Temporary output locations: C:/Temp/EEG/ImaginedRightHandFeetRest and
C:/Temp/EEG/ImaginedLeftRightHandRest. No D-drive access.


The original paper v4 explicitly maps P1 to the patient and P2 to the healthy
participant in its data-availability section. Its analysis pipeline (4-36Hz
filter, ASR, common-average reference, baseline correction/windowing) is distinct
from this raw-XDF archive and is not reapplied. Native raw reference remains
unknown. [Original article](https://arxiv.org/html/2511.23384v4).

Final batch verification:74relevant tests passed; source/array/sidecar details
are linked from `temp-c-mi-preparations.md`. No uploads or D-drive access.
