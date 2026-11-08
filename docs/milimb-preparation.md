# ImaginedHandFootActions / MILimbEEG

**Current location:** D:/Data/EEG, sources D:/Data/EEGSources, restored by verified transfer. C:/Temp references below describe the original staging history; temporary copies are now removed.
Started8November2026, C:/Temp only; D: access paused. Original Mendeley
[x8psbz3f6x v2](https://data.mendeley.com/datasets/x8psbz3f6x/2), original
CC BY4.0. Asanza et al.(2023),10.1016/j.dib.2023.109540.

The full-archive endpoint was unavailable, but the original public webpage's
individual-file API works. Inventory every original folder and select only
native imagery I1..I8 files plus small original figures/annotations. Publisher
SHA256 and byte counts verified individually; no execution M files downloaded.
Selected3719imagery/baseline/rest CSVs total561,848,100bytes. Native version2
listing has7440epoch files and60subjects, unlike larger headline counts. All
listed imagery runs are R1. S22R1I2_5.csv is absent, so left-hand count299 rather
than300; no replacement case/label is guessed.

Eight original classes: eyes-open baseline, imagined closing left/right hands,
left/right foot dorsiflexion, left/right foot plantarflexion and intervening
rest. Baseline/rest are source classes, not additional independent studies.
Mixed healthy/clinical cohort; native participant annotations retained as
strings, including uncorrected height formats and dates rather than guessed ages.

Every CSV supplies0..499sample-index rows and16numeric channel columns0..15.
Original numbered electrode figure supplies channel1..16 mapping:
FC5,F3,Fz,F4,FC6,FC1,FC2,Cz,T7,CP5,C3,CP1,CP2,C4,CP6,T8. Native CSV column order is
checked, anatomical mapping is figure-derived, not embedded named CSV headers.
No individually measured positions are invented. Original units are explicitly
microvolts;125Hz and reference to neutral electrode on both ear lobes are
documented source properties. Native numbers cast/parsed float64 unchanged.
Original publisher filtering claims and example processing are distinguished;
no added filtering/resampling/rereferencing/baseline/normalisation.

Retain full500sample epochs (4seconds). Unknown original continuous offsets and
visits remain unknown. R1 is native repetition, not an asserted visit date.
Archive split uses whole subjects S1-S45train,S46-S60test, deterministic numeric
file-token order with original API listing index preserved; actual acquisition
sequence is unavailable. No validation archive. Pilot first, then full audit,
global flat policy, exact numeric/metadata/hash readback and aeon smoke.

Pilot/full conversion results pending.


## Full-source quality audit and explicit exclusions

Full preflight found31byte-identical/nonflat rest file pairs across S1/S2,
all original class8, no conflicting labels. The initial pilot S1/S60 did not
cover S2, so could not expose these copies. **All62 ambiguous epochs are excluded
symmetrically**, without selecting a guessed true owner. Both participants retain
their31 unambiguous baseline/imagery cases but contribute no class8rest. All other
participant/trial labels are unchanged. Full raw input3719files; planned retained
3657 cases,2727TRAIN/930TEST. This is an explicitly documented source-quality
subset, not a claim of an untouched complete release.

No duplicate rest waveform is a flatline. Independent full audit also found
constant/effectively flat sensors F4,FC1,Cz,CP1,T8 in some original cases. Apply the
user-authorised global sensor removal, preserving native order of remaining11.
Source CSV header variants have empty or NaN **sample-index header cells** only;
all16signal column headers remain0..15 and numeric sample indices0..499. The NaN
header label is not a missing EEG sample and requires no numerical repair.

Machine-readable evidence: `milimb-native-quality-audit.json` and
`milimb-header-audit.json`. Every excluded name/participant/class, publisher hash,
waveform hash and reason is retained in the dataset metadata and per-participant
source accounting. Source CSVs are unchanged. A new clean pilot S3/S60 passed
62/62cases,16channels, all8classes and full exact readback/aeon checks. The full
conversion now reruns under this documented rule; old raw-pilot/partial caches
remain separate. No upload or external author contact.


## Completed preparation

Full validated output: **TRAIN `(2727,11,500)`, TEST `(930,11,500)`**,125Hz,
8classes,60participants. Original source3719epochs,62excluded,3657retained;
subject separation45/15. Remaining source order:
FC5,F3,Fz,FC6,FC2,T7,CP5,C3,CP2,C4,CP6. No exact duplicate cases within/across
splits remain after both case and channel selection, and no constant/tiny sensors
remain. Every numeric case passed exactfloat64 readback/row/label/hash alignment;
aeon load/fit/predict smoke passed on three cases/class/partition. Source CSVs are
unchanged. All source/exclusion counts reconcile in metadata. The original full
source quality audit describes the pre-selection data, not the admitted output.

Final files: C:/Temp/EEG/ImaginedHandFootActions. Original CSVs and intermediates
remain separately in C:/Temp/EEGSources/MILimbEEG. No D-drive access or uploads.

Local upstream issue draft: [copied rest epochs](issues/milimb-copied-rest-epochs.md),
not posted. Final batch verification:74relevant tests passed and diffcheck passed.
