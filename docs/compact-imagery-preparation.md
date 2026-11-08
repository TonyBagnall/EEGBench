# Compact imagined movement preparations

Started 8 November 2026. Original MIMED v3 imagery archive, MOVING Zenodo12804784
v1 EEG archive and Zhang Figshare5579461 v1 KI archive downloaded to the separate
D:/Data/EEGSources cache. Publisher MD5/byte checks and local SHA256 recorded in
the source locks. Original hosts grant CC BY4.0; software licensing is separate.

MOVING is fully converted as **ImaginedHandGestures**. Zhang's two-participant
pilot and full **ImaginedArmTasks** conversion passed, with
anatomical sensor identities explicitly flagged as unknown. MIMED's complete
export is stopped after cross-ID source duplicates; its pilot is not an admitted
archive problem. Original archive problems and experiment results are unchanged.

MIMED native MATs provide channel order, Fs, subject token and four joined_data
cells. Left-hand/stand-sit cells have2432 samples, right-hand1152 in participant01.
Folder-level classes are reliable; individual up/down direction labels are absent.
The archive keeps one four-second window per cell, indices384:896, after the
documented three-second baseline. This crop is an archive choice and cue timing
is not a native trigger. Original article Table1 confirms sensor order; cells0/1
are documented day1 scenarios and2/3 day2. No synthetic original continuous times.
Numeric MAT values are unchanged float64, presumed microvolts with large offsets.

MOVING native EDFs include32 named EEG channels plus X/Y/Z accelerometers. MNE
reads physically calibrated volts; float64 multiplication by1e6 yields microvolts.
Six-second crops follow native Trigger#1/7/13 rest and#3/9/15 MI events; executed
movement windows excluded. Fixed movement ordering is a protocol limitation.
Full export: TRAIN `(382,17,3000)`, TEST `(143,17,3000)`, 500 Hz, four classes,
11 participants, one recording each. Whole-subject split: original IDs01-08
TRAIN,09-11 TEST. Native selected markers give525 cases rather than nominal528:
participant05 lacks one Trigger#13 and one Trigger#15, and09 lacks one#15.
Nothing is padded or assigned an invented marker.

The authorised global flat policy removes15 sensors: Cz,C3,T7,PO4,FC6,FC2,AF4,
CP6,CP2,CP1,CP5,FC1,FC5,AF3,PO3. The retained native order is
P7,P4,Pz,P3,P8,O1,O2,T8,F8,C4,F4,Fp2,Fz,F3,Fp1,F7,Oz. Missing central sensors
are a practical limitation for motor-imagery comparisons. Exact source indices,
affected case counts and threshold are in the metadata/quality report. No added
filtering/resampling, interpolation or rereferencing. Full numeric readback,
case/label/hash alignment, subject separation, no within/across-split duplicates,
remaining flat/tiny channel checks and aeon load/fit/predict smoke passed.
Aeon smoke uses three cases per class per partition; it is not full-cohort fitting.

Zhang native BCI2000 headers have17 float32 source columns, SourceChGain/Offset,
1000Hz, native StimulusCode and full stimulus caption/icon matrices. ChannelNames
is empty in **all180 files**. The pinned loader's EGI E1-16/E28 mapping
is an inference, not recovered native sensor labels. It is not applied. The
export uses opaque source_column_00..16 identifiers, with anatomical names null,
no assigned positions, and anatomical channel-order consistency marked unknown.
The source ordinal order is preserved exactly; this does not certify anatomical
correspondence between files. The dataset remains explicitly flagged for this
metadata limitation even if numeric conversion validates.

Native StimulusCode/caption matrices identify all ten classes. Across180 files,
4317 cue intervals last4000 samples and three last3960. Every retained case uses
the first3960 samples (3.96seconds). A40-sample nonzero state at the beginning of
H6run01 is left-censored, excluded and preserved in the metadata audit. This
leaves4320 complete native task intervals,360 per participant. These measured
counts take precedence over inconsistent published nominal trial arithmetic.
Float32 stored samples are cast to float64 **before** `(raw-offset)*gain`, using
all17 native SourceChOffset/SourceChGain values; the BCI2000 format defines the
result as microvolts. No default gain, hemisphere flip or montage is applied.
TRAIN is H1-H9 and TEST H10-H12, whole people, native run/event order.

Final Zhang shapes are TRAIN `(3240,17,3960)` and TEST `(1080,17,3960)`,1000Hz,
ten classes; all17 source columns retained, no flat channels removed. No shared
subjects, exact within/across-split duplicates or remaining flat/tiny channels.
Every case passed float64 numeric readback and row/hash/label alignment; aeon
load/fit/predict smoke passed. Anatomical channel consistency remains unknown,
explicitly represented as a metadata flag rather than a successful check.
The original article Table2 supplies all12 participants' age, sex and handedness;
the zero-padded published IDs are retained alongside directory IDs. This is
publication metadata, not a direct native header recovery.

## Prepared dataset summary

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB (approximately) | licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ImaginedHandGestures | 382 | 143 | 11 | 17 | 3000 | 4 | 500 | 0.511468 | CC BY4.0 |
| ImaginedArmTasks | 3240 | 1080 | 12 | 17 | 3960 | 10 | 1000 | 5.027821 | CC BY4.0 |

Sizes include `.ts` plus sidecars; exact refreshed totals are in the conversion
result JSONs. Final files are under `D:/Data/EEG/<dataset>/`. Sources, pilots and
compressed numeric intermediates remain separately under EEGSources. No uploads.
The registry now has68 problems and eeg.txt selects64; the original30/results
are unchanged. MIMED is absent from both counts.

## Metadata completeness

| Field | MOVING | Zhang |
|---|---|---|
| Subject ID | Native filename | Native directory; nonunique header alias retained separately |
| Session/run | Assigned sole recording | Native SubjectSession/SubjectRun |
| Trial/event ID | Native annotation ordinal | Native StimulusCode interval ordinal |
| Original recording sample bounds | Recovered from native annotation time/rate | Recovered from native state samples |
| Original/encoded class | Original trigger plus documented task map | Native code and caption matrix |
| Channel names/order | Native EDF names, consistent across all11 files | **Anatomical identities unknown**, source ordinals preserved |
| Calibration/units | Native EDF microvolt dimensions, physical calibration | Native per-column offset/gain, documented BCI2000 units |
| Measured positions | Not available | Not available; no inferred sensor mapping |
| Reference | Not recovered | Cz/COM ground documented in paper |
| Individual demographics | Not recovered | Original published Table2 |
| Original split | None; archive whole-subject split | None; archive whole-subject split |

Each case TSV records exact exported native channel indices after global sensor
removal. Dataset metadata and manifests retain file hashes, original licence
evidence, split membership, transformations, source problems and missing fields.

Sources: [MIMED original release](https://data.mendeley.com/datasets/zs25xxjkm9/3),
[MIMED paper](https://doi.org/10.1016/j.dib.2024.110833),
[MOVING original release](https://zenodo.org/records/12804784),
[MOVING paper](https://doi.org/10.3390/s24165207),
[Zhang original release](https://doi.org/10.6084/m9.figshare.5579461.v1),
[Zhang paper](https://doi.org/10.1371/journal.pone.0188293).


## MIMED source-quality stop

The full360-case audit found **85 exact duplicate pairs across participant IDs**.
All12 selected cases and all complete native block arrays of P17/P24, P18/P25,
P19/P26, P20/P27, P21/P28, P22/P29 and P23/P30 agree exactly:84 pairs. In addition,
P05 stand/sit cell0 and P06 right-hand cell1 have identical384:896 crops with
conflicting class labels; their whole cells differ in length. These are nonflat
signals. No label/identity has been guessed or repaired.

See [machine-readable full-block/crop evidence](mimed-native-quality-audit.json)
and [local issue draft with reproduction](issues/mimed-cross-participant-copies.md).
The30-participant preparation cannot meet duplicate/subject-provenance checks.
It is not registered and no final ImaginedHandsTrunk folder is published. The
14 participants uninvolved in these detected copies could form a documented
reduced cohort, but that would be an explicit scope change; the user has been
asked whether to defer or prepare that subset. Source files and the small pilot
remain separately under EEGSources. No issue has been posted externally.

Final verification:65 relevant tests passed and `git diff --check` passed. Sidecar
artifact hashes/case indices checked after enrichment; validated numeric files
were untouched. Exact sizes in the result JSONs may change slightly with prose.
