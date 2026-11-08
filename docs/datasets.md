# Datasets

For original recording sources, alternative names, dimensions, paper references
and unresolved source discrepancies, see [Dataset provenance](dataset-provenance.md).
For the channel and case-metadata sidecar audit, see
[Dataset sidecar audit](dataset-sidecar-audit.md).
For measured amplitudes, flat-channel findings and proposed cleanup changes, see
the [Signal scale and flat-channel audit](signal-scale-audit.md).
Applied signal and metadata corrections are documented in
[Local data corrections](local-data-corrections.md).

The registry includes 41 additions to the original published benchmark.
OpenEEGBench sources are prepared using the
[standalone import tools](openeegbench-import.md).
The [additional dataset descriptions](additional-datasets.md) document MentalArithmetic,
ImaginedCommands and ChildhoodSeizures in `D:/Data/EEG/`, with the same `.ts` and sidecar layout
as the other local datasets. Depression was excluded following source-duplicate validation.

The published benchmark is the 30 EEG classification problems of Table 1 in
[Time Series Machine Learning for Classifying Electroencephalograms](https://data.mlr.press/assets/pdf/v03-8.pdf).
Six come from the UEA multivariate archive, the rest were collated for the paper. The
published results use the data as their owners presented them. The current local
collection includes the documented [local corrections](local-data-corrections.md).

The archive is a sub-collection of the
[Multiverse](https://github.com/aeon-toolkit/multiverse) archive for multivariate time
series classification, and some of these datasets are also in its benchmark subset,
Multiverse-core. The local collection now contains 74 prepared
classification problems, including the additional preparations described below.
The selected problem list in `eeg.txt` contains 70 problems. It excludes Blink,
ButtonPress, Sleep and EpilepticSeizures; their registry entries and local files
are retained.

## Archive datasets

<!-- DATASETS:START -->

| Dataset | Domain | Channels | Length | Classes | Subjects | Train | Test | Hz | Availability |
|---|---|---|---|---|---|---|---|---|---|
| ALSAttention | BCI | 8 | 256 | 2 | 8 | 14400 | 19200 | 256 | local |
| Alzheimers | Med | 19 | 15000 | 3 | 88 | 45 | 43 | 500 | aeon/Zenodo |
| ArmCoordination | BCI | 64 | 1500 | 2 | 8 | 1498 | 505 | 500 | local |
| ArmMovements | BCI | 61 | 1536 | 7 | 15 | 4620 | 1680 | 512 | local |
| Blink | BCI | 4 | 510 | 2 | &mdash; | 500 | 450 | 255 | aeon/Zenodo |
| ButtonPress | BCI | 32 | 1000 | 2 | 1 | 120 | 120 | 1000 | aeon/Zenodo |
| ChildhoodSeizures | Med | 17 | 2000 | 2 | 22 | 34045 | 2140 | 200 | local |
| ClinicalSleepStages | Med | 6 | 6000 | 5 | 82 | 64889 | 8803 | 200 | local |
| CodedFlickerTargets | BCI | 28 | 1100 | 4 | 12 | 2160 | 720 | 500 | local |
| CodedSymbols | BCI | 8 | 16128 | 20 | 30 | 2200 | 800 | 512 | local |
| CovidSurvivors | Med | 19 | 400 | 2 | 172 | 25319 | 11216 | 200 | local |
| EpilepticSeizures | Med | 1 | 178 | 2 | &mdash; | 80 | 11420 | 178 | aeon/Zenodo |
| EyesOpenShut | BCI | 14 | 128 | 2 | &mdash; | 56 | 42 | 128 | aeon/Zenodo |
| FaceDetection | Psy | 144 | 62 | 2 | &mdash; | 5890 | 3524 | 250 | aeon/Zenodo |
| FeedbackButton | Psy | 61 | 450 | 2 | 57 | 1700 | 1150 | 500 | aeon/Zenodo |
| FeetHands | BCI | 64 | 640 | 2 | 105 | 2835 | 1890 | 160 | aeon/Zenodo |
| FibroLiverpool | Med | 64 | 15360 | 2 | 36 | 15 | 21 | 512 | restricted |
| FibroUEA | Med | 64 | 15000 | 2 | 41 | 17 | 23 | 500 | restricted |
| FingerMovements | BCI | 28 | 50 | 2 | &mdash; | 316 | 100 | 100 | aeon/Zenodo |
| FlickerAttention | BCI | 8 | 512 | 4 | 12 | 576 | 352 | 256 | local |
| FlickerSymbols | BCI | 64 | 1500 | 40 | 35 | 6240 | 2160 | 250 | local |
| FlickerTargets | BCI | 8 | 1114 | 12 | 10 | 1440 | 360 | 256 | local |
| GameTargets | BCI | 8 | 225 | 2 | 22 | 20400 | 6000 | 250 | local |
| HandMovementDirection | BCI | 10 | 400 | 4 | &mdash; | 160 | 74 | 400 | aeon/Zenodo |
| ImaginedArmMovements | BCI | 61 | 1536 | 7 | 15 | 4620 | 1680 | 512 | local |
| ImaginedArmTasks | BCI | 17 | 3960 | 10 | 12 | 3240 | 1080 | 1000 | local |
| ImaginedCommands | BCI | 64 | 600 | 5 | 15 | 5250 | 750 | 200 | local |
| ImaginedFeetHands | BCI | 64 | 640 | 2 | 105 | 2835 | 1935 | 160 | aeon/Zenodo |
| ImaginedGrasps | BCI | 60 | 1000 | 3 | 15 | 4500 | 2250 | 250 | local |
| ImaginedGripForce | BCI | 14 | 640 | 3 | 10 | 240 | 60 | 128 | local |
| ImaginedHandFeetTongue | BCI | 22 | 800 | 4 | 9 | 3456 | 1728 | 200 | local |
| ImaginedHandFootActions | BCI | 11 | 500 | 8 | 60 | 2727 | 930 | 125 | local |
| ImaginedHandGestures | BCI | 17 | 3000 | 4 | 11 | 382 | 143 | 500 | local |
| ImaginedHandSides | BCI | 3 | 1125 | 2 | 9 | 3680 | 2840 | 250 | local |
| ImaginedHandTraining | BCI | 22 | 2560 | 2 | 18 | 5568 | 1588 | 512 | local |
| ImaginedHandsEmbodiment | BCI | 32 | 4997 | 2 | 26 | 798 | 240 | 500 | local |
| ImaginedHandsFeet | BCI | 13 | 1250 | 3 | 4 | 1365 | 435 | 250 | local |
| ImaginedHandsRobot | BCI | 32 | 1000 | 2 | 12 | 2880 | 2880 | 250 | local |
| ImaginedHandsStroke | BCI | 29 | 2000 | 2 | 46 | 1400 | 440 | 500 | local |
| ImaginedLeftRightHand | BCI | 60 | 800 | 2 | 10 | 1260 | 320 | 200 | local |
| ImaginedLeftRightHandRest | BCI | 24 | 750 | 3 | 1 | 480 | 240 | 250 | local |
| ImaginedOpenCloseFist | BCI | 64 | 640 | 2 | 105 | 2835 | 1890 | 160 | aeon/Zenodo |
| ImaginedRightHandFeet | BCI | 16 | 1536 | 2 | 8 | 240 | 80 | 512 | local |
| ImaginedRightHandFeetRest | BCI | 24 | 750 | 3 | 1 | 150 | 40 | 250 | local |
| InnerSpeech | BCI | 128 | 3584 | 4 | 9 | 250 | 200 | 1024 | aeon/Zenodo |
| LongIntervalTask | Med | 63 | 4750 | 2 | 139 | 1660 | 1120 | 500 | aeon/Zenodo |
| LowCost | BCI | 15 | 375 | 2 | 10 | 600 | 600 | 125 | aeon/Zenodo |
| MatchWords | Psy | 156 | 1500 | 2 | &mdash; | 360 | 360 | 1000 | local |
| MatchingPennies | Psy | 10 | 10000 | 2 | 7 | 700 | 700 | 5000 | aeon/Zenodo |
| MentalArithmetic | BCI | 19 | 1000 | 2 | 36 | 1515 | 192 | 200 | local |
| MindReading | BCI | 204 | 200 | 5 | &mdash; | 727 | 653 | 200 | aeon/Zenodo |
| MotorImagery | BCI | 64 | 3000 | 2 | &mdash; | 278 | 100 | 1000 | aeon/Zenodo |
| NBackAudioCondition | Psy | 16 | 600 | 12 | 23 | 11520 | 5040 | &mdash; | local |
| ObsessiveCompulsiveSymptoms | Med | 52 | 2000 | 2 | 35 | 7754 | 2660 | 500 | local |
| OpenCloseFist | BCI | 64 | 640 | 2 | 105 | 2835 | 1890 | 160 | aeon/Zenodo |
| ParkinsonsPedalling | Med | 63 | 2000 | 2 | 39 | 2123 | 842 | 500 | local |
| ParkinsonsRest | Med | 63 | 2000 | 2 | 55 | 1216 | 420 | 500 | local |
| PhotoStimulation | Med | 19 | 9000 | 3 | 73 | 37 | 36 | 500 | aeon/Zenodo |
| PronouncedSpeech | BCI | 128 | 3584 | 4 | 9 | 250 | 200 | 1024 | aeon/Zenodo |
| RestingEyeState | BCI | 16 | 5120 | 2 | 19 | 140 | 50 | 512 | local |
| SelfRegulationSCP1 | BCI | 6 | 896 | 2 | &mdash; | 268 | 293 | 256 | aeon/Zenodo |
| SelfRegulationSCP2 | BCI | 7 | 1152 | 2 | &mdash; | 200 | 180 | 256 | aeon/Zenodo |
| ShortIntervalTask | Med | 63 | 2750 | 2 | 139 | 1660 | 1120 | 500 | aeon/Zenodo |
| SitStand | BCI | 17 | 1250 | 4 | 32 | 3200 | 3200 | 250 | aeon/Zenodo |
| Sleep | Psy | 1 | 178 | 5 | 82 | 2394 | 1205 | 100 | aeon/Zenodo |
| SongFamiliarity | Psy | 32 | 3000 | 2 | 29 | 700 | 750 | 1000 | aeon/Zenodo |
| SpellerFlashes | BCI | 8 | 205 | 2 | 10 | 12600 | 12600 | 256 | local |
| SymbolAttention | BCI | 8 | 256 | 2 | 19 | 521259 | 175180 | 256 | local |
| VideoEmotions | Psy | 25 | 2000 | 8 | 123 | 15629 | 3588 | 200 | local |
| VisualSpeech | BCI | 128 | 3584 | 4 | 9 | 250 | 200 | 1024 | aeon/Zenodo |
| VisualSubjects | BCI | 16 | 512 | 2 | 64 | 42189 | 18826 | 512 | local |
| WalkingTargets | BCI | 42 | 100 | 2 | 15 | 3600 | 900 | 100 | local |
| WirelessFlicker | BCI | 14 | 640 | 5 | 11 | 1000 | 375 | 128 | local |
| WordRelatedness | Psy | 30 | 1024 | 2 | 40 | 3600 | 1200 | 1024 | local |

<!-- DATASETS:END -->

### SymbolAttention

Classify attended versus non-target symbol flashes. Original **Chailloux2020**, OpenNeuro `ds003190` v1.0.1, CC0. Nineteen participants and 56 available sessions; 521,259 train / 175,180 test cases, 8 EEG channels, 256 samples at 256 Hz. Split by whole participants (14 train / 5 test). Overlapping one-second flash epochs remain within recordings; no subject crosses partitions. Native values are preserved in float64, with microvolt interpretation explicitly inferred. Exclude one proven copied recording, two no-flash placeholders and 179 flashes without a target marker; preserve source evidence.

Files: `D:/Data/EEG/SymbolAttention/`, approximately 27.83 GB with sidecars. See [source identity, metadata and validation](symbol-attention-preparation.md).

### ArmCoordination

Classify **executed right-arm-only versus both-arm reaching**. Original **Kueper2024**, Zenodo `10229480`, CC BY 4.0; eight healthy participants, 49 physical recordings. 1,498 train / 505 test cases, 64 EEG channels, 1,500 samples at 500 Hz, from two seconds before to one second after motion onset. Six participants train / two test, with no shared people. Preserve all 2,003 native onsets with error/event flags; this is condition classification rather than the paper's movement-versus-rest task. Explicit native microvolt calibration is applied in float64. XP01's fourth unilateral file continues interrupted set 3 rather than adding a complete set.

Files: `D:/Data/EEG/ArmCoordination/`, approximately 3.65 GB with sidecars. See [native participants, sensors, flags and preprocessing](arm-coordination-preparation.md).



### WalkingTargets

Classify attended target versus non-target visual stimuli while walking on a treadmill. Original BCI Competition 2020 Track 5 / BCIComp2020WalkingERP, 15 participants, 3,600 train / 900 test cases, 42 EEG channels (32 scalp and 10 ear), 100 samples at 100 Hz. Official training and validation are merged; all 15 participants intentionally occur in both partitions. Four globally flat ear electrodes were removed, with source-to-case audit. Native numeric values are retained; microvolt units are inferred. Original OSF data licence CC BY 4.0.

Files: `D:/Data/EEG/WalkingTargets/`. See [preparation, metadata and provenance](walking-targets-preparation.md).



Domain is medical (Med), brain-computer interface (BCI) or psychology (Psy). Subjects is
blank where the local participant count is not established. FaceDetection,
HandMovementDirection, MindReading and MatchWords are MEG. Availability distinguishes
automatic aeon/Zenodo downloads, local preparations and restricted access. The table
is written from `eegbench.datasets.metadata()` when the leaderboards are rebuilt.
Sampling frequency is blank where it has not been supplied.

## Additional local preparations

<!-- PREDCT:START -->
### ParkinsonsRest

Parkinson's disease versus controls at rest. One OFF-medication visit per patient and control visit 1: 27 patients and 28 controls. Author-rejected patient 803/OFF visit 1 is excluded. Both native eye conditions are retained. Consecutive marker sequences prevent an isolated marker in control 896 from introducing instruction-period windows.

1,216 train / 420 test cases; 63 EEG channels,
2000 samples at 500 Hz. Four-second non-overlapping windows,
float64 microvolts and a fixed class-stratified participant split. No shared
participants, duplicate cases or archived validation partition. Data licence:
PDDL-1.0 verified against the original PRED+CT catalogue and pinned mirror.
No constant/effectively flat sensors required removal.
Files: `D:/Data/EEG/ParkinsonsRest/`. See
[provenance, metadata and validation](predct-preparation.md).

### ObsessiveCompulsiveSymptoms

High versus low obsessive-compulsive symptoms in 35 students (12 high, 23 low), using an OCI score threshold of 21. This is not a clinical OCD diagnosis task. The 11 processed `_ready` recordings are excluded because their processing history is uncertain and five yield impossible sample counts under the chosen reader. The native 64 EEG channels become 52 after the global flat-channel removal; HEOG, VEOG and EKG are excluded.

7,754 train / 2,660 test cases; 52 EEG channels,
2000 samples at 500 Hz. Four-second non-overlapping windows,
float64 microvolts and a fixed class-stratified participant split. No shared
participants, duplicate cases or archived validation partition. Data licence:
PDDL-1.0 verified against the original PRED+CT catalogue and pinned mirror.
12 sensors removed under the archive flat-channel policy.
Files: `D:/Data/EEG/ObsessiveCompulsiveSymptoms/`. See
[provenance, metadata and validation](predct-preparation.md).

### ParkinsonsPedalling

Parkinson's disease versus controls during a lower-limb pedalling recording. All 39 participants (26 PD, 13 controls) are retained. Native Aa/Bb/Cc labels are preserved; X/Y/Z accelerometers are excluded.

2,123 train / 842 test cases; 63 EEG channels,
2000 samples at 500 Hz. Four-second non-overlapping windows,
float64 microvolts and a fixed class-stratified participant split. No shared
participants, duplicate cases or archived validation partition. Data licence:
PDDL-1.0 verified against the original PRED+CT catalogue and pinned mirror.
No constant/effectively flat sensors required removal.
Files: `D:/Data/EEG/ParkinsonsPedalling/`. See
[provenance, metadata and validation](predct-preparation.md).

<!-- PREDCT:END -->

### ImaginedGripForce

Imagine squeezing the right hand at **10%, 40% or 70% of maximum voluntary
contraction**. This is MartinezPeon2024 / Figshare `25773342` version 1, ten
participants in one documented session each. The preparation has 240 training
and 60 test cases, each with 14 EEG channels and 640 samples (5 seconds at 128 Hz).
Original participants `001`-`008` train and `009`-`010` test; all three classes
are balanced. No validation partition is archived.

Native microvolt values are preserved in float64, with no filtering or resampling.
No constant/effectively flat sensors or duplicate cases were found. Channel names
come from the documented column mapping; cue times are inferred from the fixed
protocol, not recorded triggers. Files and ordered sidecars are in
`D:/Data/EEG/ImaginedGripForce/`. See [provenance, extraction and validation](imagined-grip-force-preparation.md).

### ImaginedHandsStroke

Liu2024 adds imagined left/right hand grasping in acute stroke patients:
1400 train / 440 test cases, 46 retained release IDs, 29 EEG channels and
2000 samples at 500 Hz. Source IDs 05/15/49 are excluded as known derived
products, and 43 is excluded for ambiguous native stage markers. The source
licence is CC BY 4.0. See [source evidence, extraction and validation](imagined-hands-stroke-preparation.md).

### Four further open MOABB conversions

RestingEyeState (Rodrigues2017), GameTargets (BrainForm), CodedFlickerTargets
(Castillos2023) and ImaginedHandTraining (Kumar2024) are prepared in
`D:/Data/EEG/` with ordered sidecars and validated subject splits. All four original
data releases are CC BY 4.0. See [task descriptions, source identities, sensor
harmonisation and measured validation](open-moabb-conversions.md).

### Other local preparations

The local additions use the same `Name/Name_TRAIN.ts`, `Name_TEST.ts` layout,
with ordered channel information, case metadata, provenance and validation
sidecars. Original validation is appended to training; test membership is retained.
The three OpenEEGBench preparations below have passed full signal/label readback, subject-separation and duplicate
checks, plus an aeon load/fit/predict compatibility check. They are prepared for
local research, with source terms and release-review notes included in each folder.

| Dataset | Domain | Channels | Length | Classes | Subjects | Train | Test | Hz |
|---|---|---|---|---|---|---|---|---|
| ImaginedHandFeetTongue | BCI | 22 | 800 | 4 | 9 | 3456 | 1728 | 200 |
| ClinicalSleepStages | Med | 6 | 6000 | 5 | 82 | 64889 | 8803 | 200 |
| VideoEmotions | Psy | 25 | 2000 | 8 | 123 | 15629 | 3588 | 200 |

### Compact MOABB additions

Six further source collections have been prepared with subject IDs on every
case, ordered sensor metadata, source checksums and exact float64 exports.
All cases are in microvolt numeric scale. See the
[full preparation and provenance report](small-moabb-preparations.md).

- **FlickerTargets:** Nakanishi2015, identify one of 12 attended flicker targets.
  Ten subjects, 8 channels ? 1114 points at 256 Hz, 1440/360 subject-disjoint cases.
- **ImaginedHandSides:** BCI IV 2b, imagined left/right hand movement. Nine subjects,
  3 bipolar channels ? 1125 points at 250 Hz, 3680/2840 cases. Original first-three/
  last-two session protocol intentionally shares subjects.
- **SpellerFlashes:** BNCI2015_003, attended/unattended visual speller flashes.
  Ten subjects, 8 channels ? 205 points at 256 Hz, 12600/12600 cases. Original
  train/test runs intentionally share subjects; character and row/column modes
  are identified in the metadata.
- **ImaginedHandsFeet:** Zhou2016, imagined left hand, right hand or feet. Four
  subjects, 13 channels ? 1250 points at 250 Hz, 1365/435 subject-disjoint cases.
  Fp2 was removed globally after three saturated constant windows were found;
  all cases and the original 14-channel source remain available.
- **ALSAttention:** BNCI2014_008, attended/unattended speller flashes in eight ALS
  participants. This predicts attention, not ALS diagnosis. Eight channels ? 256
  points at 256 Hz, 14400/19200 calibration/feedback cases; subjects intentionally
  occur in both partitions.
- **WirelessFlicker:** MAMEM3, attend one of five simultaneous flickering boxes.
  Eleven subjects, 14 wireless channels ? 640 points at 128 Hz, 1000/375
  subject-disjoint cases. Original sensor names/units and exact trial markers
  are recovered from each native file. Source a?e blocks are not asserted as
  five separate acquisition visits.

All six passed complete numeric readback, row/label/count and sensor-order
checks, with zero cross-partition signal duplicates or overlapping recording
intervals and successful aeon load/fit/predict checks. Source-specific licence
and missing-metadata notes accompany each dataset. No validation split is
archived, and no data have been uploaded.

### FlickerSymbols

Classify which of **40 frequency/phase-coded visual symbols** is attended, from
Wang2016 / the Tsinghua SSVEP Benchmark. There are 35 participants, one session
and six blocks per person. All 8400 native six-second epochs are retained:
64 channels ? 1500 points at 250 Hz, in microvolt numeric scale with exact
float64 decimal export. Source acquisition was at 1000 Hz. There is no added
filtering, demeaning, reference change, gain, crop or resampling.

The fixed subject-disjoint split has 6240 training and 2160 test cases, balancing
experienced/novice groups. Labels 1?40 retain the source target indices;
frequency and phase are in the sidecars. Original channel names and polar
positions are retained, including CB1/CB2 without unverified aliases. See the
[preparation and provenance report](flicker-symbols-preparation.md) for source
terms, unavailable recording offsets and the different original block protocol.
Files are in `D:/Data/EEG/FlickerSymbols/`.

### ImaginedHandFeetTongue

Classify four imagined movements: **left hand, right hand, both feet and tongue**.
The source is BCI Competition IV dataset 2a, also known as BNCI2014_001 or the
Graz four-class motor-imagery dataset. Nine people completed two recording
sessions. Our fixed split uses subjects 1â€“6 for training and 7â€“9 for test, keeping
both sessions within each person's assigned partition. Each case is four seconds
of 22 EEG channels, resampled upstream from 250 to 200 Hz; the original EOG
channels are excluded. Labels are feet=0, left hand=1, right hand=2, tongue=3.

Previously stored locally as `BCIIV2a`. The [original publisher](https://bnci-horizon-2020.eu/database/data-sets)
specifies CC BY-ND 4.0; release of the upstream processed signals needs review.
The folder is `D:/Data/EEG/ImaginedHandFeetTongue/`.

### ClinicalSleepStages

Classify overnight clinical EEG into **Wake, N1, N2, N3 and REM** sleep stages.
This preparation comes from ISRUC-Sleep, a separate collection from the
Sleep-EDF-derived `Sleep` problem. The fixed protocol retains 82 cohort-I
participants: 72 for training and 10 for test. Each case is 30 seconds of six
EEG derivations at 200 Hz. Their true array order is
`C3-M2, C4-M1, F3-M2, F4-M1, O1-M2, O2-M1`; the sidecars retain the inverse
mapping from the unrelated electrode names assigned upstream. Stage labels are
Wake=0, N1=1, N2=2, N3=3, REM=4. Second-scorer labels are retained where supplied.

Previously stored locally as `ISRUCSleep`. The [original source](https://sleeptight.isr.uc.pt/)
provides research access; redistribution permission remains unverified.
The folder is `D:/Data/EEG/ClinicalSleepStages/`. Full arrays occupy 10.61 GB as
float32 or 21.22 GB as float64, before loading overhead and classifier memory.

### VideoEmotions

Classify EEG recorded while participants watched emotion-eliciting video clips.
The source is FACED, the Finer-grained Affective Computing EEG Dataset, with 123
participants. This pinned preparation contains **anger, disgust, fear, sadness,
amusement, inspiration, joy and tenderness**. Neutral is absent upstream, so
there are eight observed classes. Original codes `0,1,2,3,5,6,7,8` are preserved;
the missing Neutral code is 4. Each case is ten seconds of 25 selected EEG
channels at 200 Hz. Training uses source subjects 000â€“099 and test uses 100â€“122.
Video identifiers are retained in the case metadata.
The upstream export had 26 channels; F8 (original index 6) was subsequently
removed globally after the flat-channel audit. Units remain microvolts.

Previously stored locally as `FACED`. See the [original study](https://doi.org/10.1038/s41597-023-02650-w)
and [data-specific CC BY 4.0 evidence](https://doi.org/10.1016/j.neuroimage.2024.120890).
The original Synapse terms remain a release-review item. The folder is
`D:/Data/EEG/VideoEmotions/`.

Full pins, processing, metadata completeness and local preparation commands are
in [the preparation guide](openeegbench-local-preparations.md).

### ImaginedLeftRightHand

Classify **imagined left-hand versus right-hand movement** from the Weibo Yi
2014 study, originally released as *EEG data of simple and compound limb motor
imagery*. This preparation retains two of the original seven classes. Ten
participants contribute four-second windows of 60 EEG channels at 200 Hz;
subjects 1â€“8 form training and 9â€“10 form test. There are 1,260 training and 320
test cases, balanced between the two classes. Source labels 1=left hand and
2=right hand are retained alongside the exported text labels. The sidecars give
participant IDs, source files, original trial indices and crop boundaries.

Previously stored locally as `Weibo2014`. Source data:
[Harvard Dataverse, DOI 10.7910/DVN/27306](https://doi.org/10.7910/DVN/27306), CC0;
[Yi et al. (2014)](https://doi.org/10.1371/journal.pone.0114853).
The folder is `D:/Data/EEG/ImaginedLeftRightHand/`.

### ImaginedRightHandFeet

Classify **imagined right-hand versus both-feet movement** from the AlexMI source
dataset. The current preparation retains two classes and excludes Rest. Eight
participants contribute three-second windows of 16 EEG channels at 512 Hz;
subjects 1â€“6 form training and 7â€“8 form test. There are 240 training and 80 test
cases, balanced between right-hand and feet imagery. Participant IDs, source
recordings, event samples and crop information are retained in the sidecars.
Source: [Alexandre Barachant's dataset](https://doi.org/10.5281/zenodo.806023).
The previous local name is `AlexMI`; files are now in
`D:/Data/EEG/ImaginedRightHandFeet/`.

### NBackAudioCondition

Data attributed to **Christoph Tremmel**. **More information to follow.**
Classify the joint condition of an N-back working-memory level (0-, 1- or 2-back)
and one of four audio conditions (codes 0-3). The twelve unchanged original labels
are `10 * audio_condition + nback_level`: `0,1,2,10,11,12,20,21,22,30,31,32`.
Audio-condition descriptions are pending.

The source has 25 participants with 720 trials each. Participants 10 and 16 are
excluded, retaining 23; the archive owner confirmed the subject blocks and
exclusions. The existing NBack subject split is preserved: 16 people / 11,520 cases
for training, seven / 5,040 for test, with 960 / 420 per joint class. Each case has
16 channels and 600 timepoints. Signal values, channel-axis order and source order
within partitions are preserved, with no filtering or resampling added.

The folder is `D:/Data/EEG/NBackAudioCondition/`, with ordered case tables,
component labels, source row indices, participant strings, provenance, validation
and a hashed manifest. Older NBack, NBackR and noise-subset preparations use the
same collection. Sensor names, frequency, sessions, original recording boundaries,
publication and data licence are pending. Channel indices are not anatomical
names. See [NBack provenance](nback-location.md).

### VisualSubjects

Classify **attended-target versus non-target flashes** in the Brain Invaders 2014a
visual P300 task, also known as BI2014a or BrainInvaders2014a. This is a new source
collection for EEGBench, from Korczowski et al. (2019),
[Zenodo v1, DOI 10.5281/zenodo.3266223](https://doi.org/10.5281/zenodo.3266223).
The original data record explicitly declares **CC BY 4.0**.

All 64 distributed participants are retained. Subjects `01`-`48` form training
and `49`-`64` form test; this is an EEGBench-defined subject split, with no separate
validation partition. Each case is one second of 16 EEG channels at the native
512 Hz, giving 512 timepoints. Original codes are `1=NonTarget`, `2=Target`.
Target and non-target counts are imbalanced; there is no class subsampling.

The original header order is `Fp1, Fp2, F5, AFZ, F6, T7, Cz, T8, P7, P3, PZ, P4,
P8, O1, Oz, O2`. We retain **F5/F6**, recording the conflict with the loaders'
F3/F4 aliases. Arrays are not reordered. No filtering, resampling, baseline or
reference change is added; float32 conversion is documented and validated.

The folder is `D:/Data/EEG/VisualSubjects/`, with aligned case tables, source
participant/file/event identifiers, original sample/time bounds, ordered sensor
metadata, attribution, source snapshots and validation manifests. Overlapping
epochs stay within one participant's assigned partition. Physical game-session
boundaries and individual sensor positions remain unavailable; loader session/run
`0/0` are kept separately. See [preparation and provenance](moabb-preparations.md).

### FlickerAttention

Classify attention to **13, 17 or 21 Hz flickering LEDs, or rest**, from
Kalunga2016 / SSVEP-exoskeleton. The original [Zenodo v1 release](https://zenodo.org/records/2392979)
specifies CC BY 4.0. The preparation retains 12 participant IDs and 29 distinct
recordings after documented duplicate exclusions, including a numeric duplicate
that the MOABB loader still includes. Subjects 01-09 form training (576 cases),
10-12 form test (352 cases); all four classes are balanced. Each case has eight
EEG channels by 512 points: [2,4) seconds after a FIF marker, at 256 Hz.

Native order is `Oz, O1, O2, PO3, POz, PO7, PO8, PO4`. Original codes are
`1=rest, 2=13Hz, 3=21Hz, 4=17Hz`, preserving the source's corrected frequency
mapping. Files are in `D:/Data/EEG/FlickerAttention/`, with recovered participant,
recording, measurement-time and event/sample metadata. The distributed numeric
scale is retained, with explicit unit and sensor-position caveats. See
[source audit and preparation](kalunga-preparation.md) and
[validation summary](kalunga-local-results.json).

### WordRelatedness

Classify **semantically related versus unrelated visual word pairs** from the
ERP CORE N400 experiment, a separate recording collection from the auditory MEG
MatchWords problem. All 40 participants are retained: 001-030 for training
(3,600 cases), 031-040 for test (1,200 cases). Classes are balanced. Each case has
30 EEG channels by 1,024 timepoints, one second at the native 1,024 Hz around the
target-word marker. Three EOG channels are excluded from features but retained
in sensor metadata. No filtering, baseline, resampling or reference change is added.

Files are in `D:/Data/EEG/WordRelatedness/`, with ordered channel names/types,
millimetre electrode coordinates, participant demographics, original event and
urevent IDs, word-list conditions, prime/response information and sample bounds.
The original one-based EEGLAB latencies are converted explicitly to zero-based
array indices. Original LICENSE and the authors' website specify **CC BY-SA 4.0**;
conflicting CC0/CC BY metadata are preserved and documented. See
[provenance and preparation](word-relatedness-preparation.md) and
[validation summary](word-relatedness-local-results.json).

### Other additions

- **MentalArithmetic:** arithmetic versus eyes-closed rest; PhysioNet EEGmat,
  36 participants, 19 EEG channels and five-second windows at 200 Hz.
- **ImaginedCommands:** five imagined spoken commands; BCI Competition 2020
  Track 3, 15 participants, 64 channels and three-second trials at 200 Hz.
  Its fixed run split intentionally includes each participant in train and test.
- **ChildhoodSeizures:** seizure versus background EEG; CHB-MIT, 22 known people,
  17 bipolar derivations and ten-second windows at 200 Hz. These three sources
  are described in [Additional EEG datasets](additional-datasets.md).
- **CovidSurvivors:** COVID-survivor versus close-contact cohort membership,
  using 19 channels and two-second windows at 200 Hz. The local split retains
  172 participants; the target is cohort membership.
- **MatchWords:** semantic-relatedness Yes/No judgements following auditory
  words, from [OpenNeuro ds004276](https://openneuro.org/datasets/ds004276/versions/1.0.0).
  Cases have 156 retained MEG channels and 1,500 points, in femtotesla after
  removing constant original axis 55 and applying a gain of 1e15. The source roster lists 18 people,
  but local case-to-person IDs and independently verified array channel identities
  are unavailable; the table leaves the retained participant count unspecified.

### ArmMovements and ImaginedArmMovements

Ofner2017 contributes two seven-class problems: executed and imagined right
upper-limb movements. Both retain elbow flexion/extension, forearm supination/
pronation, hand closing/opening and rest. Each has 15 participants, 61 EEG
channels and 1,536 samples per case (three seconds at 512 Hz), with 4,620 training
and 1,680 test cases. Participants `01`â€“`11` train and `12`â€“`15` test in both tasks.
There is no validation split.

They use different recording days from the same people. Each problem has one
session and ten runs per person; the source study has two sessions per person
across tasks. Do not count these as independent participant cohorts or repeat
imagery sessions. Files are in `D:/Data/EEG/ArmMovements/` and
`D:/Data/EEG/ImaginedArmMovements/`, under the original CC BY 4.0 data licence.

Aligned case sidecars retain subject/session/run, original class events, sample
bounds and labels. Sensor sidecars preserve the exact channel order. Generic
names in participant 1's execution files are mapped using the publisher's table,
without reordering signals. No filtering, resampling, scaling or reference change
is added; ambiguous original unit metadata are explicitly flagged. See the
[source, conversion and metadata report](ofner-preparations.md).

### CodedSymbols

Thielen2021's offline visual-speller task: predict the attended target among
20 coded symbols. Thirty participants each contribute one session with five
blocks of 20 trials. Cases have eight EEG channels and 16,128 samples (31.5 seconds
at the original 512 Hz). Training participants `01`â€“`22` contribute 2,200 cases;
test participants `23`â€“`30` contribute 800. All original target IDs 1â€“20 are retained,
with no validation partition.

Files are in `D:/Data/EEG/CodedSymbols/`, under the original version-3 deposit's
CC0 licence, with exact case/subject/session/block/marker metadata and ordered
sensor lists. These are raw-GDF trials; the separate 180 Hz MATLAB buffers are
not used. The STATUS channel is excluded and EEG axes are preserved in order.

The first sensor is labelled Fpz from the original `.loc` file, but other source
materials say Fp1 or Fz. Its physical identity is explicitly flagged as unresolved;
all aliases and template positions are preserved. See the
[source, conversion and metadata report](coded-symbols-preparation.md).

## Lists

```python
from eegbench.datasets import eegbench, eegbench_paper, eegbench_open, local_only, by_domain, metadata

len(eegbench)        # 60, the full registry
len(eegbench_paper)  # 30, the original paper subset
len(local_only)      # 24, prepared additions without automatic aeon downloads
len(eegbench_open)   # 28, the ones anyone can download
by_domain("Med")     # all registered medical problems
metadata()           # the table above as a DataFrame
```

`eegbench_open` is the 28-problem automatic-download subset, matching aeon's
`eeg2026`. `local_only` contains thirty additional preparations to load from local
`.ts` files. FibroLiverpool and FibroUEA require research access through Tony
Bagnall. `eegbench_paper` identifies the original 30; the default registry and
batch experiment list include all 60. Existing results cover the datasets on
which each estimator has actually been evaluated.

## Downloading and loading

The open datasets are on Zenodo in the
[tsml community](https://zenodo.org/communities/tsml/) and are fetched and cached by
aeon:

```python
from aeon.datasets import load_classification

X_train, y_train = load_classification("Blink", split="train")
X_test, y_test = load_classification("Blink", split="test")
```

`X` has shape `(n_cases, n_channels, n_timepoints)`. Some of these are large:
The current local Alzheimers short variant is 19 channels of 15,000 points a case.
Its retained reported 500 Hz is unverified from the local files.

## The train and test split

Every dataset has a default split, and the leaderboard uses only that. Split
evidence varies by source; consult the sidecars and provenance page.

- For subject-disjoint protocols, no subject has cases on both sides. A classifier
  that learns to recognise a subject or a recording session, rather than the class, gets
  no credit for it.
- ImaginedCommands intentionally shares subjects across its run-based split.
- Single-subject sources may split by session, but the SCP sources have documented
  day/session exceptions.
- Subject indices are supplied where recovered. Some legacy exports, including
  MatchWords, still lack reliable case-to-person mappings.

This is why results here are not resampled. A random or class-stratified resample puts
the same subject in train and test, and scores on it are not comparable to the ones
here. Resampling that keeps subjects together needs the subject index, and is not yet
part of this repository.


## ImaginedHandGestures (MOVING2024)

Imagine opening/closing the right hand, rotating the wrist or tapping fingers,
or rest: four classes from11 participants. TRAIN `(382,17,3000)`, TEST
`(143,17,3000)`,500Hz, whole-subject01-08/09-11 split. Native EDF names/order and
calibration retained, X/Y/Z accelerometers excluded,15 globally flat sensors
removed. Native markers give525 cases, with three expected markers absent.
The movement order is fixed, a source protocol confound. Original
[Zenodo12804784 v1](https://zenodo.org/records/12804784), CC BY4.0;
Mattei et al.(2024), [paper](https://doi.org/10.3390/s24165207).
See [full preparation and metadata](compact-imagery-preparation.md).

## ImaginedArmTasks (Zhang2017)

Nine imagined elbow-centred actions plus rest, including drawer/door opening,
spoon feeding, lifting, cleaning, combing, cutting and picking/placing. TRAIN
`(3240,17,3960)`, TEST `(1080,17,3960)`,1000Hz,12 participants, H1-H9/H10-H12
whole-subject split. Native stimulus captions and codes define the classes;
3.96-second crops stay within every retained cue, one40-sample file-boundary
state fragment excluded. Explicit per-channel gain/offset calibration produces
float64 microvolts; no hemisphere flip or extra filtering/resampling.

**Sensor metadata flag:** all180 native headers have empty ChannelNames. Array
columns remain in their original order, identified only by source_column_00..16.
These are ordinal IDs, not recovered anatomical names. Anatomical correspondence
between recordings is unknown; no guessed EGI mapping or montage is applied.
Published participant demographics are retained separately from native fields.
Original [Figshare5579461 v1](https://doi.org/10.6084/m9.figshare.5579461.v1),
CC BY4.0; Zhang, Yong and Menon(2017),
[paper](https://doi.org/10.1371/journal.pone.0188293).
See [full preparation, validation and limitations](compact-imagery-preparation.md).

MIMED/ImaginedHandsTrunk was downloaded but **not added**: cross-ID copies,
including a conflicting-label waveform, stopped the complete-source conversion.
See [source evidence](mimed-native-quality-audit.json).


## Latest motor imagery preparations

The following three problems are now in **D:/Data/EEG/** after verified transfer
from temporary C:/Temp staging. Existing
problem files/results are unchanged. These add three problems from two source
studies; the two NeuroTUM entries have distinct individual recordings.

### ImaginedRightHandFeetRest (NeuroTUM P1)

Rest, imagined right hand or imagined legs/feet, one tetraplegic participant;
TRAIN `(150,24,750)`, TEST `(40,24,750)`,250Hz. Native sessionsS1-S4 train,S5test.
Intentional within-person session transfer. Exact native XDF sensor spelling,
order and XYZ descriptors retained. Physical coordinate units/reference unknown;
numeric microvolt interpretation inferred, source values unchanged float64.

### ImaginedLeftRightHandRest (NeuroTUM P2)

Rest, imagined left hand or imagined right hand, one healthy participant;
TRAIN `(480,24,750)`, TEST `(240,24,750)`,250Hz. SessionsS1-S2 train,S3test.
Same source study/hardware as P1 but different participant recordings/class map.
The original YAML maps, native markers/sample bounds, clock metadata and shared
participant exception accompany both. No signal/timestamp filtering or resampling.
Original [Zenodo18087806 v1.0.0](https://doi.org/10.5281/zenodo.18087806), CC BY4.0;
Tscherniak et al., [paper](https://doi.org/10.48550/arXiv.2511.23384).
[Full two-problem metadata and validation](neurotum-preparation.md).

### ImaginedHandFootActions (MILimbEEG imagery)

Eight original classes: eyes-open baseline, left/right hand closing, left/right
foot dorsal/plantar flexion, and rest between tasks. TRAIN `(2727,11,500)`, TEST
`(930,11,500)`,125Hz,60 participants; whole-subjectS1-S45/S46-S60 split.
The original source includes a mixed healthy/clinical cohort. Native participant
annotations and exact filename/epoch IDs accompany cases. Sensor identities are
recovered from the author's numbered placement figure, matching checked native
numeric CSV columns; original microvolt numbers unchanged.

**Source-quality subset:** all62ambiguous rest epochs copied across S1/S2 are
excluded symmetrically, without guessing their correct owner; both people retain
unambiguous baseline/imagery trials. S22left-hand trial5 is absent at source.
Five globally flat/effectively flat sensors F4,FC1,Cz,CP1,T8 removed under the
archive policy. Remaining order FC5,F3,Fz,FC6,FC2,T7,CP5,C3,CP2,C4,CP6. Unknown
original continuous offsets/visits stay unknown; R1 is a repetition token.
Original [Mendeley x8psbz3f6x v2](https://doi.org/10.17632/x8psbz3f6x.2), CC BY4.0;
Asanza et al.(2023), [paper](https://doi.org/10.1016/j.dib.2023.109540).
[Complete source audit, exclusions and validation](milimb-preparation.md).


### ImaginedHandsRobot (Farabbi2020)

Left versus right hand/arm motor imagery with first-/third-person Baxter robot
feedback.12participants,3sessions each,144MIrecordings; TRAIN/TEST each
`(2880,32,1000)`,250Hz. Original training-phase recordings form TRAIN and
online-test-phase recordings form TEST. All participants/sessions are intentionally
shared; pooling across days is not unseen-person evaluation or strict chronological
session transfer. Four-second windows start at recorded class cues. Native GDF
calibration is applied in float64 and volts converted to microvolts. Exact32EEG
identities/order and author polar locations come from the original numbered
chanlocs file;3accelerometers and separate rest runs excluded. No additional DSP
or flat-sensor removals. No duplicates; full readback/metadata/aeon checks passed.
Original [Zenodo5882500 v1](https://doi.org/10.5281/zenodo.5882500), CC BY4.0;
[full provenance, protocol and missing metadata](imagined-hands-robot-preparation.md).


### ImaginedGrasps (BCI Competition2020 Track4)

Cylindrical, spherical and lumbrical grasp imagination.15participants across
three days each; TRAIN `(4500,60,1000)`, TEST `(2250,60,1000)`,250Hz. Original
training day then validation day form TRAIN; original test day unchanged, all15
people intentionally shared. Native four-second imagery segment only; deliberately
zeroed test visual-cue interval excluded consistently. Native60EEG names/order
and montage recovered and consistent across45files; FCz reference/Fpz ground
from original organiser PDF. True test labels come from the original organiser
workbook, independently checked against pinned MOABB vectors. Native float64
values unchanged; microvolt interpretation inferred, explicit physical unit and
original continuous offsets unavailable. No EEG removals or duplicate cases.
Original [OSFpq7vb Track4](https://osf.io/pq7vb/), CC BY4.0;
Jeong et al.(2022), [competition review](https://doi.org/10.3389/fnhum.2022.898300).
Distinct recording task from Track3ImaginedCommands and Track5WalkingTargets;
shared project/paper does not prove independent participant cohorts.
[Detailed provenance and validation](imagined-grasps-preparation.md).


### ImaginedHandsEmbodiment (Vagaja2023)

Left/right-hand imagination in VR after Embodied or Control priming;26people,
one visit and one retained MI recording per person. TRAIN `(798,32,4997)`,
TEST `(240,32,4997)`,500Hz. Original [Zenodo8086086 v1](https://doi.org/10.5281/zenodo.8086086),
CC BY4.0; Vagaja and Vourvopoulos(2023), *Electrophysiological Signals of
Embodiment and MI-BCI Training in VR*. Aliases Vagaja2023, NEMAR nm000292.
No separate paper DOI established. Rest/priming runs are excluded. Native32EEG
order, explicit microvolt calibration and header coordinate template retained;
2EMG/temperature/3ACC excluded. Native float32 counts cast to float64 before
physical calibration. Native DC/131Hz, notch off, software filters disabled;
no added DSP. Reference/ground identities and individual demographic mappings
unavailable. SUB31 stale header references explicitly linked to deposited
same-stem binary/marker files.

Common9.994second crop stays inside every native S10 end marker. Two imagery
trials crossing lost-sample markers excluded, yielding1038cases from1040cues;
all original markers/exclusions retained. First10numeric IDs per13-person
priming group TRAIN, remaining3/group TEST: no shared people. No flat EEG
removals or exact duplicate cases; full readback/metadata/aeon checks passed.
Same laboratory/hardware as Batista2022 does not prove shared recordings; its
future admission must compare native identities/dates/waveforms.
[Full provenance, memberships and recovery](imagined-hands-embodiment-preparation.md).
