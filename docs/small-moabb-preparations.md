# Compact MOABB preparations

These preparations use the same `Name/Name_TRAIN.ts`, `Name_TEST.ts` layout as
the archive, with ordered case TSVs, sensor tables, metadata, source evidence,
attribution, validation and manifests. The files are under `D:/Data/EEG/`.
Machine-readable measured counts, sizes and checks are in
[small-moabb-local-results.json](small-moabb-local-results.json).

The standalone [adapter](../tools/prepare_small_moabb.py) reads original native
arrays or the pinned Zhou BIDS release. Source checksums are frozen in
[small-moabb-source-lock.json](small-moabb-source-lock.json), with original
URLs and receipts. MOABB loader evidence is pinned to
`bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`. Large sources and generated arrays
remain outside Git. There is no archived validation partition.

## Measured local results

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ALSAttention | 14400 | 19200 | 8 | 8 | 256 | 2 | 256 | 1.316 | CC-BY-NC-ND-4.0 |
| FlickerTargets | 1440 | 360 | 10 | 8 | 1114 | 12 | 256 | 0.174 | Unspecified original data licence; public author release |
| ImaginedHandSides | 3680 | 2840 | 9 | 3 | 1125 | 2 | 250 | 0.423 | CC-BY-ND-4.0 |
| ImaginedHandsFeet | 1365 | 435 | 4 | 13 | 1250 | 3 | 250 | 0.559 | CC-BY-4.0 (pinned BIDS release) |
| SpellerFlashes | 12600 | 12600 | 10 | 8 | 205 | 2 | 256 | 0.795 | CC-BY-NC-ND-4.0 |
| WirelessFlicker | 1000 | 375 | 11 | 14 | 640 | 5 | 128 | 0.224 | CC-BY-4.0 |

All six full exports passed validation.

## Problems and source provenance

### FlickerTargets — Nakanishi2015

Predict which of 12 frequency/phase-coded visual targets is attended. The
[author release](https://github.com/mnakanishi/12JFPM_SSVEP) is pinned to
`2d4e281a430b4676f75c9270db839e963f172da5`; all ten participants are included.
Paper: Nakanishi, Wang, Wang and Jung (2015), *A Comparison Study of Canonical
Correlation Analysis Based Methods for Detecting Steady-State Visual Evoked
Potentials*, [DOI](https://doi.org/10.1371/journal.pone.0140703).

Each native epoch has 8 channels × 1114 points at 256 Hz. The documented original
acquisition rate is 2048 Hz. No further crop, mean subtraction or filtering is
applied. Original target indices 1–12 map to
`9.25,11.25,13.25,9.75,11.75,13.75,10.25,12.25,14.25,10.75,12.75,14.75 Hz`.
Channel order is documented as `PO7, PO3, POz, PO4, PO8, O1, Oz, O2`; these names
are supported by source documentation/loader evidence, not embedded sensor labels
in the MATLAB signal tensor. Stimulation begins at one-based sample 39.

Training uses source participants 01–08, test 09–10: 1440/360 cases, respectively,
120/30 per class. IDs, target/trial tensor indices, original `sub_i`/`list_sub`
fields and source file checksums are retained. Original continuous offsets,
acquisition dates and individual positions are unavailable. The original data
licence is unspecified; the article's licence is not substituted for it.

### ImaginedHandSides — BCI Competition IV 2b

Predict imagined left versus right hand movement. Aliases: Graz dataset B,
BNCI2014_004 / 004-2014. This is a separate recording collection from IV 2a,
which we call ImaginedHandFeetTongue. Original source:
[BNCI publisher](https://bnci-horizon-2020.eu/database/data-sets), with its
[description](https://bnci-horizon-2020.eu/database/data-sets/004-2014/description.pdf).
Study reference: Leeb et al., *Brain-computer communication: motivation, aim,
and impact of exploring a virtual apartment*,
[DOI](https://doi.org/10.1109/TNSRE.2007.906956).

Nine participants have five source sessions each. Preserve original T/E protocol:
the first three sessions form TRAIN (3680 cases), the last two TEST (2840).
All nine subjects intentionally occur in both partitions, in different sessions.
Actual counts differ by subject; the catalogue's nominal protocol arithmetic is
not used to add or remove trials.

Each case has three bipolar derivations, ordered `C3, Cz, C4`, with 1125 points
at 250 Hz. Windows are [3,7.5) seconds relative to native trial markers, following
the pinned loader. The three original EOG channels are excluded from classification
arrays but retained in source metadata/files. The electrode-pair placements differ
slightly across people; labels must not be treated as identical monopolar sensor
positions. Native session/trial markers, sample bounds, class codes 1/2,
artifact flags and available demographic fields are retained. No artifact trials
are silently rejected. Source terms: **CC BY-ND 4.0**.

### SpellerFlashes — BNCI2015_003

Predict attended versus unattended visual speller flashes. Source study: Guger
et al. (2009), *How many people are able to control a P300-based brain-computer
interface (BCI)?*, [DOI](https://doi.org/10.1016/j.neulet.2009.06.045).
Original MATLAB files are downloaded from the BNCI publisher and frozen by
SHA256 receipts, because those URLs have no immutable release identifier.

Ten participants each have native train/test recording matrices. Preserve these
runs: 12600 cases in each partition, with all ten people intentionally shared.
Participants 01–02 use individual-character flashes (36 codes), while 03–10
use row/column flashes (12 codes). This explains the measured 25200 cases versus
the catalogue estimate. Both conditions retain the binary attention target.

Each case is 8 channels × 205 points at 256 Hz (the nearest sample length to
0.8 seconds). Ordered sensors are `Fz, Cz, P3, Pz, P4, PO7, Oz, PO8`, documented
by the source loader; matrix rows alone do not embed these names. The time,
Flash and Target rows are not EEG. One case is extracted per flash onset,
not per nonzero trigger sample. Raw Target 0/1 encodes to NonTarget=1/Target=2.
Onsets, recording-local samples, flash codes and original partitions are retained;
exact character-selection boundaries remain unavailable. Source terms:
**CC BY-NC-ND 4.0**.

### ImaginedHandsFeet — Zhou2016

Predict imagined left hand, right hand or feet. Study: Zhou et al. (2016),
*A Fully Automated Trial Selection Method for Optimization of Motor Imagery
Based Brain-Computer Interface*,
[DOI](https://doi.org/10.1371/journal.pone.0162657). The actual signal source is
the fixed EDF/BIDS release [Zenodo 16534752](https://zenodo.org/records/16534752),
not an unspecified current mirror. Its data licence is **CC BY 4.0**. The
[original Figshare archive](https://doi.org/10.6084/m9.figshare.2061654.v2)
separately declares **CC0**; the original archive was identified and its metadata
verified, but it was not substituted for the pinned EDF/BIDS signal source.

Four source participants have three sessions, two runs each. Training uses 01–03
(1365 cases), test 04 (435 cases). All 1800 distributed labelled events are
retained. Labels remain feet=1, left_hand=2, right_hand=3. Five-second windows
have 1250 samples at 250 Hz.

The source has 14 channels. **Fp2, original zero-based index 1, was removed
globally**, leaving 13, under the authorised constant-channel cleanup. Three
subject-04 windows were exactly constant at the EDF physical limits
−2055.93/+2055.859 microvolts. See the
[source finding and exact cases](zhou-flat-channel-source-report.json).
Retained order: `Fp1, FC3, FCz, FC4, C3, Cz, C4, CP3, CPz, CP4, O1, Oz, O2`.
No cases or labels were removed. Full 14-channel source files, geometry and
original-to-output indices are preserved.

Names/order are checked against every EDF header and channels.tsv. Supplied
electrodes/coordinate-system files and event rows are retained. These positions
may be template-derived, and scan dates may reflect conversion rather than
original acquisition. Source reference JSON says n/a; the literature's left
mastoid reference is separately marked as documented evidence. MNE-calibrated
volts are multiplied by 1e6 in float64 to preserve microvolt numeric scale.

### ALSAttention — BNCI2014_008

Predict attended versus unattended speller flashes in eight participants with
ALS. **This is an attention task, not ALS diagnosis.** Study: Riccio et al.
(2013), *Attention and P300-based BCI performance in people with amyotrophic
lateral sclerosis*, [DOI](https://doi.org/10.3389/fnhum.2013.00732).
The [original publisher description](https://bnci-horizon-2020.eu/database/data-sets/008-2014/description.pdf)
and source MATLAB fields are retained. Source terms: **CC BY-NC-ND 4.0**.

Each participant spelled seven five-character words. Preserve the first three
calibration words (15 character selections) as TRAIN and the last four feedback
words (20 selections) as TEST: 14400/19200 cases. All eight people intentionally
occur in both partitions. Every selection contains 120 flashes; exact selection
indices and original one-based trial-start markers are retained. Class codes
remain NonTarget=1 and Target=2.

Each case has 8 channels × 256 points at 256 Hz. Sensor names/order are directly
recovered from the native channels field:
`Fz, Cz, Pz, Oz, P3, P4, PO7, PO8`. Available age, gender, ALSFRS and onset
fields are preserved as distributed; the publication's demographic values can
differ. The original PDF documents a right-earlobe reference, left-mastoid ground
and 0.1–30 Hz acquisition filtering. Conflicting generated catalogue filter
descriptions are not treated as directly verified preprocessing history.

### WirelessFlicker — MAMEM3

Predict which of five simultaneous flickering boxes is attended using the
wireless Emotiv EPOC recordings of MAMEM experiment III. This is another source
recording collection, not a new label view of FlickerTargets or FlickerSymbols.
Original source: Figshare **3413851, version 3**,
[DOI](https://doi.org/10.6084/m9.figshare.3413851.v3), **CC BY 4.0**. The acquisition
PDF and versioned file metadata accompany the export.

Eleven participants have five source blocks/subsessions a–e, each divided into
halves i/ii. MOABB groups these into one session: they must not be counted as
five independently verified acquisition visits. Main-experiment files are used;
the separate adaptation x is excluded. Fixed subject split: 001–008 TRAIN,
009–011 TEST. Participant IDs retain their three digits.

Each case contains the full five seconds between exact native start/stop markers
32779/32780: 14 channels × 640 samples at 128 Hz. The MATLAB event matrix is
checked against the Status waveform to verify one-based sample positions.
Original target codes 33025–33029 encode to 1–5, corresponding to
12.00, 10.00, 8.57, 7.50 and 6.66 Hz. The auxiliary Status channel is excluded.
Exact sensor order and microvolt units come directly from each file's info
fields; no standard names or units are substituted. Header timestamps and
prefilter strings are retained without asserting an unverified acquisition date
or interpreting unspecified NaN filter fields as actual filter settings.

## Validation and use

All arrays use float64 and shortest exact decimal representation. There is no
additional filtering, demeaning, resampling, reference change or baseline
correction. Local EEG selection, half-open window bounds, source-label encoding,
Zhou's unit conversion and its Fp2 removal are explicitly documented.

Pilot conversions precede full preparations. Full checks cover every case:
exact numeric hash/readback, shape, finite values, labels, class counts, row
alignment and sensor order. Cross-partition duplicate signals and overlapping
recording intervals must be zero. Subjects are disjoint where the source has no
fixed protocol; original session/run exceptions are reported above. Bounded
aeon load/fit/predict checks cover all classes. Missing fields remain blank or
explicitly flagged; read all case identifiers as strings.

```powershell
python -m tools.prepare_small_moabb --datasets nakanishi bci2b speller zhou als mamem3 --cache D:/Data/EEGSources/SmallMOABB --output D:/Data/EEG
```

Adapters refuse to overwrite an existing destination. The source lock and
cached receipts verify redownloads. Source files and metadata can be retained
without being required at classifier fit time. No data have been uploaded;
licence/access and public release decisions remain separate from local preparation.

## Metadata completeness

| Problem | Subject IDs | Session/run identity | Trial/event identity and offsets | Sensor identity and positions |
|---|---|---|---|---|
| FlickerTargets | Every case; source filename index | One documented session; original date/run IDs unavailable | Original tensor target/repetition indices; epoch-local samples only, no continuous offsets | Eight ordered documented names; no embedded names/individual coordinates |
| ImaginedHandSides | Every case | Five native session arrays, original T/E phase | Native trial number, one-based marker, exact recording samples, artifact flag | Three documented bipolar derivations; EOG separately identified; pair endpoints unavailable |
| SpellerFlashes | Every case | Native train/test runs; one documented session | Exact pulse onset, time/recording samples, flash code, original/encoded target; character-selection boundaries unavailable | Eight documented names/order; time and trigger rows excluded; individual positions unavailable |
| ImaginedHandsFeet | Every case | Native BIDS session/run identifiers | Every source event row, code, exact distributed EDF samples; pre-conversion raw offsets unavailable | Native channels.tsv/EDF names agree; source geometry retained; original Fp2 removal mapped explicitly |
| ALSAttention | Every case | One recording; calibration/feedback phase | Every flash onset, character-selection index, original trial-start marker and samples | Eight names directly in MAT; documented reference; individual positions unavailable |
| WirelessFlicker | Every case; three-digit IDs | Native a?e block/subsession and i/ii half identifiers | Native event-matrix rows, one-based label/start/stop markers and exact source samples | Fourteen names and microvolt units directly in each MAT header; Status excluded; individual positions unavailable |

All case tables remain in exact array order. Source unit claims, reference,
filtering history and positions are explicitly identified as native evidence,
documented source information or unresolved fields. Publication metadata and
derivative header timestamps are not silently presented as original acquisition facts.
