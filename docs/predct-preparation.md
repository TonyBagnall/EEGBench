# PRED+CT clinical EEG additions

Completed 5 November 2026. No release upload.

| Archive problem | Native source | Classification task |
|---|---|---|
| ParkinsonsPedalling | 2123 | 842 | 39 | 63 | 2000 | 2 | 500 | 7.094 | PDDL-1.0 |
| ParkinsonsRest | 1216 | 420 | 55 | 63 | 2000 | 2 | 500 | 3.054 | PDDL-1.0 |
| ObsessiveCompulsiveSymptoms | 7754 | 2660 | 35 | 52 | 2000 | 2 | 500 | 20.544 | PDDL-1.0 |

The [original PRED+CT catalogue](https://predict.cs.unm.edu/downloads.php)
explicitly grants **PDDL v1.0 to the database and its contents**. Each pinned
mirror's root LICENSE.txt also contains PDDL. Bundled analysis software licences
are separate. This is evidence for the data licence, not a software-licence
assumption. The selected native files and exact mirror revisions/checksums are
in [predct-source-lock.json](predct-source-lock.json). Original data have no DOI
identified; the DOI stored by the converter is explicitly a reference-paper DOI.

## Conversion definition

Native continuous recordings become consecutive, non-overlapping four-second
windows (2,000 samples at native 500 Hz). These are archive windows, not original
trials. Complete windows only; trailing samples are discarded. Pedalling and
flanker windows include practice/intertrial/break periods within the recording.
Rest windows are bounded separately by native eyes-closed/open marker sequences,
excluding the instruction lead-in. The source script emits markers each second;
each consecutive marker sequence ends at last marker plus one second, capped at
the next sequence or recording end. Marker gaps above 1.5 seconds start a new
sequence; short isolated sequences cannot yield a four-second window. Case rows retain condition, exact sample bounds, original
participant/session strings, group and all native events in that window.

Within each class, sorted original participant strings: first floor(75%) train,
remaining test. No validation partition. This is a new, explicitly documented
participant split: these native sources do not provide OpenEEGBench's fixed
partitions. No participant may cross partitions. This conversion does not claim
to reproduce ETH EEG-Bench's resampled/channel-selected benchmark views.

Native sensor order is checked across every included recording. BrainVision/CNT
MNE-calibrated volts become microvolts with float64 multiplication by 1e6;
EEGLAB resting MAT numerical microvolts are cast to float64 without scaling.
No magnitude-dependent heuristic correction, filtering, resampling, baseline
subtraction or rereferencing. Per the archive's authorised quality policy,
sensors with std <= 1e-7 microvolts in any retained case are removed globally and
listed with their previous indices. Full exact .ts readback, case signal hashes,
metadata alignment, duplicate checks, participant separation and aeon classifier
smoke tests must pass before a dataset directory is published.

## Source-specific evidence and limitations

**Singh2020:** 39 native BrainVision trios, 26 PD and 13 control participants.
The original `ALL_data_Modeling.csv` uses literal backslash-t escapes; the parser
handles these explicitly and retains clinical rows. Native 63 EEG labels include
Aa/Bb/Cc; their anatomical names are unknown and are not invented. X/Y/Z are
accelerometers and excluded. Native header coordinates/filter settings are
retained. The [paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8112379/) documents
Pz reference, FPz ground, 500 Hz and acquisition high-pass 0.1 Hz; its later ICA,
bad-channel rejection, average reference and time-frequency analysis are not
applied by this converter. ETH's 1e5 scaling is not reused.
The recovered first-party `scripts/Patients_MS.xlsx` AllPedaling sheet independently
confirms all 39 group-prefixed participant IDs. The author's preprocessing script
explicitly excludes XYZ, treats the remaining first 63 channels as EEG, and
documents S1 as warning and S2 as GO. Its later Pz reconstruction, electrode
removal, rereferencing and APPLE/FASTER/ICA steps are not applied. Both small files
are checksum-pinned in the source lock; original BrainVision VHDR/VMRK metadata
are copied into the sidecars. Native recording timestamps are preserved in MNE's
representation, with original time zone unverified; they are not invented visit IDs.

**Cavanagh2018b:** source mirror contains 28 patients with two visits and 28
controls with one visit (84 files), whereas the original catalogue says 27+27.
`IMPORT_ME_REST.xlsx` identifies first-visit medication status and matched
controls. Select each patient's OFF visit; exclude 803 because the author's
`PD_Rest_from_BV.m` explicitly says session 1 is bad and not to use it. This
leaves 27 patients and 28 controls. Retain control 8010 as an independent ID,
not as patient 801. Author notes 8070 has only a little closed-eye data; complete
windows are retained where available. Both eye conditions are verified against
native S1/S2 versus S3/S4 markers and author stimulus script; mirror summary's
eyes-open-only description is incomplete. Author script identifies 63 EEG,
VEOG and X/Y/Z accelerometers, with CPz reference. Native reference field
`common` and supplied chanlocs are preserved; CPz is not reconstructed.
Control 896 contains an isolated closed-eye marker approximately 199 seconds
before the regular closed-eye sequence. The provisional conversion was stopped
before publication; regeneration splits marker sequences at gaps above 1.5
seconds, preventing instruction-period windows. All native markers and the
short discarded sequence remain documented.
Raw resting values retain large DC offsets. The optional author processing block
flags FT9,TP9,TP10 andFT10 as consistently bad; their nonconstant traces are
retained under the archive's stated flat-channel policy and flagged in sensor
metadata. No mean removal, artifact correction or additional electrode removal
is applied. Microvolt scale follows the author's EEGLAB import; these raw
baseline offsets must not be interpreted as an instruction to rescale again.
`QUALITY_CHECK.xlsx` concerns other URSI/oddball identifiers and is retained as
evidence, not misapplied as a rest quality mask.

**Gruendler2009:** 46 student recordings, not diagnosed OCD patients. Explicit
int32 CNT decoding follows author `Step1_PreProc.m`; automatic byte-size
inference fails on the pilot. Native labels identify 64 EEG (including M1/M2
and CB1/CB2), HEOG, VEOG and EKG. Author comments and later variable assignments
swap the two EOG names, so distributed labels are retained as primary evidence.
`Info.xlsx` SELECT sheet has duplicate OCI columns: the converter explicitly
uses column B and preserves the raw cells/header. OCI >=21 defines high symptoms,
following the inspected ETH adapter; it is not a clinical diagnosis.
The resulting table groups are 22 high and 24 low, differing from the catalogue's
23+23; original scores remain in each case row and source evidence.
Sex code meanings and distinct visit IDs are not recovered; codes and `unknown` visit
values are explicit. No amplitude-based scale correction or average reference.

The original author README distinguishes **35 nominal raw CNT files and 11
Neuroscan-processed `_ready.cnt` files**. Some electrodes may have been
interpolated in the latter; bad-section markers may be present and stored
references may differ. The author documents an online reference between Cz and
CPz, but cannot confirm whether processed files were rereferenced to linked
mastoids. This is a source limitation: case rows flag the variant and reference
uncertainty; no undocumented harmonisation is attempted. Complete interpretation
of all Neuroscan bad-section markers by MNE is not independently established.
The same README says the original experiment had 60 participants, 46 are
distributed and 36 entered the published analyses; exact historical selection
is not reconstructible. Related papers listed by the author include Cavanagh
et al. (2010), Neuropsychologia 48,2098-2109, and the control-only Cavanagh,
Cohen and Allen (2009), Journal of Neuroscience 29,98-105. These are references
to this source family, not additional independent recording collections.

The conversion therefore retains **only the 35 nominal raw recordings**: 12
high-symptom and 23 low-symptom participants. All 11 processed `_ready` recordings
are deferred, including 10 high and 1 low. Five of them (946,950,956,957,958)
claim approximately 133 million samples despite files that cannot contain that
amount of 32-bit, 66/67-channel data. The
[header audit](gruendler2009-header-audit.json) records every native layout,
sample count and conservative physical-byte bound. ECG is also absent in several
processed files; EEG names/order agree, so this is an auxiliary-layout difference.
The converter now checks physical sample bounds before preloading. No sample
count repair or interpretation of the uncertain processed data is attempted.
This raw-only scope also avoids introducing the strong association between
processing variant and symptom class into the classifier.
The impossible counts are MNE's header interpretation, not proof of corrupt
original signals; a processed-format incompatibility remains possible. A
[local issue/reproduction note](gruendler2009-source-issues.md) preserves the
header-only example without preloading or attempting a repair.

## Outputs and reproducibility

`python -m tools.download_predct_batch` downloads selected native files from
pinned Hugging Face mirrors. `python -m tools.prepare_predct` converts them;
both accept configurable local roots. Source files remain under
`D:/Data/EEGSources/PREDCT/<source>/`; validated outputs are placed under
`D:/Data/EEG/<archive-name>/`. Each output contains TRAIN/TEST .ts, ordered case
TSVs, channel names/types/order, metadata, manifest, validation report, source
evidence and converter code. Intermediates are compressed per-recording NPZ,
numeric float64 `X(case,channel,time)` with `allow_pickle=False`.

Measured results (decimal GB, includes sidecars):

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ParkinsonsPedalling | 2123 | 842 | 39 | 63 | 2000 | 2 | 500 | 7.094 | PDDL-1.0 |
| ParkinsonsRest | 1216 | 420 | 55 | 63 | 2000 | 2 | 500 | 3.054 | PDDL-1.0 |
| ObsessiveCompulsiveSymptoms | 7754 | 2660 | 35 | 52 | 2000 | 2 | 500 | 20.544 | PDDL-1.0 |

All cases passed exact float64 .ts readback, row/hash/label alignment, finite-value
and post-removal variance checks. No duplicate cases within/across partitions,
shared participants or cross-split recording intervals. Every native sensor order
was verified. Aeon load/variance/fit/predict smoke tests used 3 cases per class per
partition; full-size arrays were checked by streaming exact readback. Independent
header/clinical-table expectations agree exactly with flanker counts.

At completion of this batch the registry contained **63 prepared problems**, with **59 selected** in
`eeg.txt`. The published 30 and their results are unchanged.

### Flat-channel transformation

ParkinsonsPedalling and ParkinsonsRest needed no constant/effectively flat sensor
removal. ObsessiveCompulsiveSymptoms had 52 exact-constant case/channel pairs in
51 cases. Per the authorised policy, remove each of the 12 affected sensors
globally, retaining every one of the 10,414 cases. This changes 64 EEG inputs to 52
output channels. No nonconstant tiny pairs were found. Indices below are 0-based
pre-removal EEG indices, also the original native CNT indices.

| Removed sensor | Original index | Constant pairs |
|---|---:|---:|
| FP1 | 0 | 8 |
| F7 | 5 | 1 |
| FCZ | 18 | 5 |
| FC2 | 19 | 3 |
| C4 | 29 | 7 |
| PO7 | 52 | 1 |
| PO5 | 53 | 2 |
| PO8 | 58 | 6 |
| CB1 | 59 | 12 |
| OZ | 61 | 1 |
| O2 | 62 | 1 |
| CB2 | 63 | 5 |

The [case-level removal audit](gruendler2009-flat-channel-cases.tsv) identifies
every failing pair, original sensor, participant, recording, source samples and
archived row. Each affected case was matched by exact post-selection signal hash
to its archived metadata; the identical audit is in the dataset folder.

### Metadata completeness

| Field | ParkinsonsPedalling | ParkinsonsRest | ObsessiveCompulsiveSymptoms |
|---|---|---|---|
| Participant IDs | 39, filenames/table/workbook agree | 55 retained, clinical table and author lists | 35 retained, filenames and OCI table |
| Visits |Original visit ID unknown; native timestamps retained |Original visit 1/2, OFF status retained |Original visit ID/date unknown |
| Recording/window IDs |Native file plus exact window/sample bounds |Native MAT plus exact bounds and inferred original VHDR name |Native CNT plus exact window/sample bounds |
| Original trial IDs |Not assigned to continuous windows; native cue events retained |Not applicable to resting windows; native state markers retained |Not assigned to continuous windows; native task events retained |
| Sensors | 63 names/order; XYZ excluded; native headers and author roles | 63 names/order and template chanlocs; VEOG/XYZ excluded | 52 names/order after flat removal; 64 original EEG plus EOG/ECG documented |
| Positions/reference |Header/MNE montage; documented Pz |Distributed template coordinates; documented CPz, native common field |Header/MNE montage; documented online reference between Cz/CPz |
| Original labels |Clinical group strings, including FOG subgroups |Clinical PD/control role and medication status |Original OCI score; encoded high/low threshold 21 |
| Missing information |Exact visit ID, anatomical meaning of Aa/Bb/Cc, original timestamp time zone |Original VHDR unavailable; individual measured geometry not supplied |Exact visit/date, full historical selection; processed ready files deferred |

IDs are strings. MNE montage/timestamp interpretations, author documentation and
direct native fields are distinguished. No individual electrode digitisation is
invented. Full [machine-readable results](predct-conversion-results.json) and
[metadata completeness](predct-metadata-completeness.json) accompany this report.

## Participant overlap across studies

PDDys rest shares its source cohort with the oddball, Simon/conflict and
reinforcement-learning derivatives described in [the ETH source review](../EEG-Bench.md).
The original rest import script explicitly loads
`{subject}_{visit}_ODDBALL.vhdr` and crops the initial rest. Rest and oddball
therefore may share **original acquisitions**, despite different distributed
MAT filenames and task phases. This does not establish overlapping exported
samples; original signals/event correspondence have not been compared. Case
sidecars retain the inferred original VHDR name and identify its script evidence.
Iowa pedalling and interval-timing releases
also require a participant-identity crosswalk before any claim of distinct people:
their task-specific file IDs end in 9 and 5 respectively. Similar numeric stems
alone do not establish identity. Within-problem subject separation is validated;
cross-dataset participant separation is not claimed. Keep full group-prefixed
native IDs rather than stripping task suffixes or joining them speculatively.
