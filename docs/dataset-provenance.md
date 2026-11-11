# Dataset provenance

The three PRED+CT additions are prepared with original data licence evidence,
pinned source files and native sensor/subject metadata. See
[PRED+CT preparation](predct-preparation.md) for ParkinsonsPedalling (Singh2020),
ParkinsonsRest (Cavanagh2018b) and ObsessiveCompulsiveSymptoms (Gruendler2009),
including catalogue discrepancies, recording exclusions and sensor-removal audits.
All three passed full conversion checks and are registered.

[ImaginedHandsStroke](imagined-hands-stroke-preparation.md) is Liu2024 /
Figshare `21679035` v5 / NEMAR `nm000158`, also misleadingly called Liu2022
by ETH-DISCO. It retains 46 release IDs after the documented derived-product
and ambiguous-trigger exclusions; the original data licence is CC BY 4.0.

Cross-benchmark source checks are now available for
[AdaBrain-Bench](../AdaBrain-Bench.md) and
[ETH-DISCO EEG-Bench](../EEG-Bench.md). In particular, the latter's Singh2021
mirror shares 116 original recording IDs with OpenNeuro ds004579, the source of
ShortIntervalTask/LongIntervalTask. This is strong evidence of shared cohort/task
origin; identical numerical recordings have not been established across its
BrainVision and OpenNeuro EEGLAB representations. See the
[ID audit and source revisions](singh2021-source-overlap.json).

The four further [open MOABB conversions](open-moabb-conversions.md) are
RestingEyeState / Rodrigues2017 (Zenodo 2605110), GameTargets / BrainForm
(17225966), CodedFlickerTargets / Castillos2023 (8255618), and ImaginedHandTraining /
Kumar2024 (10694880). Each has a distinct source collection, original CC BY 4.0
data terms and source IDs on every case. Sensor harmonisation, incomplete-window
exclusions and label evidence are documented in that report.

[ImaginedGripForce](imagined-grip-force-preparation.md) adds MartinezPeon2024 /
Figshare `25773342` v1: three imagined right-hand squeezing force levels,
ten participants, one documented session each, 60 recordings and 300 trials.
The original data licence is CC BY 4.0. The report distinguishes source-file
fields from documented channel mapping and protocol-inferred epoch times.

This page traces the original 30 EEGBench problems to their recording collections,
source names and publications, and links the provenance reports for local additions.
Original benchmark dimensions and extraction details are taken from
Sections 2.1-2.3 and Table 1 of Rushbrooke, Sami, Middlehurst and Bagnall (2026),
[Time Series Machine Learning for Classifying Electroencephalograms](https://data.mlr.press/assets/pdf/v03-8.pdf)
(the root paper, `v03-8.pdf`), and checked against
[`eegbench/datasets.py`](../eegbench/datasets.py). External sources were checked on
3 November 2026. This is primarily a source audit; subsequent verification of
selected local files and their corrections is explicitly identified below and
in [Local data corrections](local-data-corrections.md).

[Locally prepared additions](#locally-prepared-additions) are documented separately
below, including their relationship to datasets already present on the local drive.
Further [BCI IV 2a, ISRUC-Sleep and FACED local preparations](openeegbench-local-preparations.md)
have pinned source revisions, task descriptions and channel/label recovery notes.
[NBackAudioCondition](nback-location.md) adds Christoph Tremmel's joint N-back/audio
task, with owner-confirmed participant blocks and a recording sampling frequency
of 200 Hz (confirmed 9 November 2026); its 600 samples span 3 seconds. Further
source details remain to follow.
[VisualSubjects](moabb-preparations.md) is the BI2014a visual P300 task, with original
Zenodo licence evidence, pinned loader snapshots and the source F5/F6 channel names.
[FlickerAttention](kalunga-preparation.md) is Kalunga2016 / SSVEP-exoskeleton,
with corrected frequency labels and an explicit audit of duplicate recording aliases.
[WordRelatedness](word-relatedness-preparation.md) is ERP CORE N400 / OpenNeuro
ds003068, with original CC BY-SA licence evidence and native EEGLAB event metadata.
[ArmMovements and ImaginedArmMovements](ofner-preparations.md) are the executed
and imagined right upper-limb tasks of Ofner2017, Zenodo `834976` v1 (also BNCI
`001-2017`, NEMAR `nm000173`). They share 15 participants but use different session
recordings. Each has train `(4620, 61, 1536)` and test `(1680, 61, 1536)`, seven
classes at 512 Hz, with common subject split `01`â€“`11` / `12`â€“`15`. The original
data licence is CC BY 4.0; the reference is Ofner et al. (2017),
[*Upper limb movements can be decoded from the time-domain of low-frequency EEG*](https://doi.org/10.1371/journal.pone.0182578).
The report distinguishes native GDF sensor/event metadata from the original PDF's
generic-name mapping and acquisition description, and flags ambiguous GDF units.
[CodedSymbols](coded-symbols-preparation.md) is the 20-target offline experiment of
Thielen2021, Radboud DOI `10.34973/9txv-z787`, version-3 directory
`DSC_2018.00122_448_v3`, also identified as NEMAR `nm000214`. It has train
`(2200, 8, 16128)` and test `(800, 8, 16128)`, 30 participants, 20 classes and
512 Hz sampling. Original CC0 and publisher SHA256 files are retained. The reference
is Thielen et al. (2021), [*From full calibration to zero training for a code-modulated
visual evoked potentials for brainâ€“computer interface*](https://doi.org/10.1088/1741-2552/abecef).
The source's first sensor conflicts between Fpz/Fp1/Fz; this remains flagged.
Its original 512 Hz GDF recordings are distinct from the separate 180 Hz MATLAB
buffers. MOABB's binary bit-state view uses the same recordings and is not added
as an independent collection.

**Dimensions** below describe the benchmark arrays: `(cases, channels, timepoints)`.
Train and test counts are separate; labels have one value per case. Sampling rates
and subject counts are those reported for the benchmark unless explicitly described
as original-source values. An unspecified subject count means it is missing from
Table 1, even when the source identifies the participants. Source collection titles
and accession numbers are included as other names; they need not denote exactly
the same subset or classification task.

The [dataset overview](datasets.md) explains loading and access. Zenodo/aeon releases
are benchmark distributions, not necessarily the original recording source. The
six inherited UEA problems also have the archive reference: Ruiz et al. (2021),
[The great multivariate time series classification bake off](https://doi.org/10.1007/s10618-020-00727-3).
Unresolved provenance and inconsistencies are recorded below rather than silently
replacing the paper's dimensions.

## How to compare another dataset with this archive

For an agent checking another dataset, use the collection identifiers below as the
first lookup, then read the linked entry for task and conversion details. These
are collection identifiers, not claims that files are identical. The two local
fibromyalgia identifiers are labels for this page only, not public accessions.

| EEGBench problem | Origin identifier / collection | Task or subset distinguishing this problem | Evidence |
|---|---|---|---|
| [Alzheimers](#alzheimers) | OpenNeuro `ds004504` | Eyes-closed resting; AD/FTD/control | Identified |
| [Blink](#blink) | GitHub `Kelvin9811/EEG-Blink-dataset` | Short/long blinks; duplicate removed | Identified; counts conflict |
| [ButtonPress](#buttonpress) | Unresolved | Single-subject press/idle exercise | Paper only |
| [EpilepticSeizures](#epilepticseizures) | Bonn / Andrzejak 2001; TF-C `Epilepsy` | Seizure/non-seizure; 178-point windows | Identified; conversion unresolved |
| [EyesOpenShut](#eyesopenshut) | UCI `264`; DOI `10.24432/C57G7J` | EEG Eye State converted to 1 s windows | Identified |
| [FaceDetection](#facedetection) | Kaggle `decoding-the-human-brain` | Face/scramble; UEA subject split 1-10 / 11-16 | Identified; conversion unresolved |
| [FeedbackButton](#feedbackbutton) | Unresolved | Feedback-guided press/no press, 57 subjects | Paper only |
| [FeetHands](#feethands) | PhysioNet `eegmmidb`; OpenNeuro `ds004362` | Executed bilateral fists/feet | Identified |
| [FibroLiverpool](#fibroliverpool) | Local label: Liverpool FMS study | Eyes-open resting; FMS/control | Institution only |
| [FibroUEA](#fibrouea) | Local label: UEA FMS/VR study | FMS/control; distinct Liverpool cohort | Institution only |
| [FingerMovements](#fingermovements) | BCI Competition II `IV` (Berlin) | Upcoming left/right keypress | Identified; local 50-point, 100 Hz version verified |
| [HandMovementDirection](#handmovementdirection) | BCI Competition IV `3`, subject 1 | Four wrist/joystick directions; MEG | Identified |
| [ImaginedFeetHands](#imaginedfeethands) | PhysioNet `eegmmidb`; OpenNeuro `ds004362` | Imagined bilateral fists/feet | Identified; case count query |
| [ImaginedOpenCloseFist](#imaginedopenclosefist) | PhysioNet `eegmmidb`; OpenNeuro `ds004362` | Imagined left/right fist | Identified |
| [InnerSpeech](#innerspeech) | OpenNeuro `ds003626` | Inner speech; four directions | Identified; selection unresolved |
| [LongIntervalTask](#longintervaltask) | OpenNeuro `ds004579` | 7 s timing condition; PD/control | Identified |
| [LowCost](#lowcost) | OpenNeuro `ds003810` | Dominant-hand imagery/rest | Identified |
| [MatchingPennies](#matchingpennies) | GIN `sappelhoff/eeg_matchingpennies` | Left/right hand; opposite-hand imagery | Paper source link; endpoint unavailable |
| [MindReading](#mindreading) | ICANN/PASCAL2 MEG Mind Reading 2011 | Five silent-video categories; one subject | Identified |
| [MotorImagery](#motorimagery) | BCI Competition III `I` | Little-finger/tongue imagery; ECoG | Identified |
| [OpenCloseFist](#openclosefist) | PhysioNet `eegmmidb`; OpenNeuro `ds004362` | Executed left/right fist | Identified |
| [PhotoStimulation](#photostimulation) | OpenNeuro `ds006036` | 10 Hz photic stimulation; AD/FTD/control | Identified |
| [PronouncedSpeech](#pronouncedspeech) | OpenNeuro `ds003626` | Overt speech; four directions | Identified; selection unresolved |
| [SelfRegulationSCP1](#selfregulationscp1) | BCI Competition II `Ia` | Healthy subject; cortical positivity/negativity | Identified |
| [SelfRegulationSCP2](#selfregulationscp2) | BCI Competition II `Ib` | ALS patient; cortical positivity/negativity | Identified |
| [ShortIntervalTask](#shortintervaltask) | OpenNeuro `ds004579` | 3 s timing condition; PD/control | Identified |
| [SitStand](#sitstand) | OpenNeuro `ds005342` | Two postures x imagery/idle | Identified; phase selection unresolved |
| [Sleep](#sleep) | PhysioNet `sleep-edfx`; TF-C `SleepEEG` | Five sleep stages; benchmark subset | Identified; conversion unresolved |
| [SongFamiliarity](#songfamiliarity) | OpenNeuro `ds005876` | Correct/incorrect song identification | Identified |
| [VisualSpeech](#visualspeech) | OpenNeuro `ds003626` | Visual imagery; four directions | Identified; selection unresolved |

Use the following comparison procedure:

1. Trace the candidate's source chain back to a recording collection, using its
   accession, DOI, original repository, authors and acquisition paper. Record the
   candidate's own evidence URL and release/version. Different hosting platforms
   or names alone do not establish different origins.
2. Match participants, sessions/runs, conditions and acquisition details. A common
   collection means possible shared recordings; task-specific subsets may differ.
   Alzheimers and PhotoStimulation have a shared cohort but separate recording
   accessions. MotorImagery and the four eegmmidb tasks are separate collections.
3. Compare selection, channel list, epoch boundaries, filtering/resampling, labels
   and split indices. Different shapes do not rule out shared recordings; matching
   shapes do not prove shared recordings. In particular, the three speech tasks,
   two interval tasks and four eegmmidb tasks are related derived problems.
4. To claim identical examples or train/test overlap, compare recording/subject IDs,
   timestamps and conversion code, then hashes or numerical arrays where available.
   File hashes only establish byte identity; format conversion can change hashes.
   This page does not currently provide recording manifests or file hashes.

Report one of **same recordings confirmed**, **same source collection, overlap
unresolved**, **same cohort, different recordings**, **different source confirmed**,
or **insufficient evidence**, with both source links and the fields that support
the decision. An identified origin here means the collection is traceable; it does
not certify the exact EEGBench extraction. Missing identifiers or unresolved
conversion details must not be treated as proof of a different origin.

A useful handoff request is:

> Compare the candidate dataset against this provenance page. Trace its original
> recording collection, list matching EEGBench entries, and report collection,
> cohort, task and recording overlap separately. Cite the candidate's source and
> the relevant entry here. Check aliases and intermediate releases, and state
> unresolved version, selection and preprocessing differences. Do not infer exact
> data identity from names, dimensions or a shared paper alone.

## Alzheimers

- **Original source / other names:** Miltiadous et al., AHEPA University Hospital;
  [OpenNeuro ds004504](https://openneuro.org/datasets/ds004504), *A dataset of EEG
  recordings from: Alzheimer's disease, Frontotemporal dementia and Healthy subjects*.
- **Benchmark dimensions:** train `(45, 19, 30000)`, test `(43, 19, 30000)`;
  3 classes, 88 subjects, 500 Hz.
- **Current local files:** train `(45, 19, 15000)`, test `(43, 19, 15000)`, verified from both headers and every case. These are the local `Alzheimers_short` variant. The reported 500 Hz is retained but cannot be verified from the local files; cropping versus resampling is unresolved. No signal data were changed by this metadata correction. See [local corrections](local-data-corrections.md).
- **Derivation:** one 60 s eyes-closed resting window per subject; Alzheimer's,
  frontotemporal dementia or healthy control (36/23/29 subjects). PhotoStimulation
  uses a related recording collection from the same cohort.
- **Paper:** Miltiadous et al. (2023), *A Dataset of Scalp EEG Recordings of
  Alzheimer's Disease, Frontotemporal Dementia and Healthy Subjects from Routine
  EEG*, Data 8(6), 95. [DOI](https://doi.org/10.3390/data8060095).

## Blink

- **Original source / other names:** Chicaiza and Benalcazar;
  [EEG-Blink-dataset](https://github.com/Kelvin9811/EEG-Blink-dataset), also titled
  *Open data set of blink EEG signals*.
- **Benchmark dimensions:** train `(500, 4, 510)`, test `(450, 4, 510)`;
  2 classes, subjects unspecified in Table 1, 255 Hz.
- **Derivation:** short versus long blinks, 2 s per case. The paper removes a
  duplicate long-blink file and splits by trial files. It describes six subjects;
  the source repository's About text says ten and its README has inconsistent
  sample totals. Subject assignment and the exact source revision need confirmation.
- **Paper:** Chicaiza and Benalcazar (2021), *A Brain-Computer Interface for
  Controlling IoT Devices using EEG Signals*, IEEE Ecuador Technical Chapters
  Meeting, pp. 1-6; cited in the benchmark paper.

## ButtonPress

- **Original source / other names:** a single-participant EEG training exercise,
  described in the benchmark paper, Section 2.2. No original institution, accession,
  alternative dataset name or independently identifiable release is supplied.
- **Benchmark dimensions:** train `(120, 32, 1000)`, test `(120, 32, 1000)`;
  2 classes, 1 subject, 1000 Hz.
- **Derivation:** button press versus idle; 1 s windows, with 120 presses recorded.
  The [benchmark distribution](https://zenodo.org/records/15522930) is distinct
  from an identified original recording release.
- **Papers / status:** benchmark paper only; original recording citation and
  collection provenance remain unresolved.

## EpilepticSeizures

- **Original source / other names:** the University of Bonn EEG collection
  ([original download page](https://www.ukbonn.de/epileptologie/arbeitsgruppen/ag-lehnertz-neurophysik/downloads/)),
  subsequently reformatted as [UCI Epileptic Seizure Recognition](https://archive.ics.uci.edu/dataset/388/epileptic+seizure+recognition),
  and used in [TF-C](https://github.com/mims-harvard/TFC-pretraining) as **Epilepsy**
  ([processed Figshare release, version 2](https://figshare.com/ndownloader/articles/19930199/versions/2)).
- **Benchmark dimensions:** train `(80, 1, 178)`, test `(11420, 1, 178)`;
  2 classes, subjects unspecified, reported frequency 178 Hz.
- **Derivation / caveat:** the benchmark paper attributes segmentation and merging
  the five source groups into seizure/non-seizure to Zhang et al. (2022). The Bonn
  source contains five sets of 100 single-channel records and reports 173.61 Hz,
  rather than 178 Hz. The transformation to 11,500 windows and frequency metadata
  should be checked against the intermediate release. TF-C separates 60 training
  and 20 validation cases from the 11,420 test cases; combining the former would
  explain the benchmark's 80 training cases, but this is an inference, not a
  verified conversion. The original collection
  includes scalp and intracranial recordings.
- **Papers:** Andrzejak et al. (2001), *Indications of nonlinear deterministic and
  finite dimensional structures in time series of brain electrical activity:
  Dependence on recording region and brain state*, Physical Review E 64, 061907
  ([DOI](https://doi.org/10.1103/PhysRevE.64.061907)); Zhang et al. (2022),
  [Self-Supervised Contrastive Pre-Training for Time Series via Time-Frequency
  Consistency](https://arxiv.org/abs/2206.08496), NeurIPS (also relevant to Sleep).

## EyesOpenShut

- **Original source / other names:** Roesler's
  [UCI EEG Eye State](https://archive.ics.uci.edu/dataset/264/eeg+eye+state)
  ([dataset DOI](https://doi.org/10.24432/C57G7J)).
- **Benchmark dimensions:** train `(56, 14, 128)`, test `(42, 14, 128)`;
  2 classes, subjects unspecified in Table 1, 128 Hz.
- **Derivation:** one subject's 117 s continuous Emotiv recording (14,980 original
  timepoint rows). The benchmark removes values outside 3000-5000, creates 1 s
  intervals and keeps intervals with a single eye state. This changes the original
  timepoint classification task into window classification.
- **Paper:** Roesler and Suendermann (2013), *A First Step towards Eye State
  Prediction Using EEG*, International Conference on Applied Informatics for
  Health and Life Sciences, pp. 141-144; cited in the benchmark paper.

## FaceDetection

- **Original source / other names:** Kaggle's 2014
  [Decoding the Human Brain](https://www.kaggle.com/c/decoding-the-human-brain/data)
  challenge, inherited through the
  [UEA FaceDetection release](https://www.timeseriesclassification.com/description.php?Dataset=FaceDetection).
- **Benchmark dimensions:** train `(5890, 144, 62)`, test `(3524, 144, 62)`;
  2 classes, subjects unspecified in Table 1, 250 Hz. **Modality: MEG**.
- **Derivation / caveat:** face versus scrambled image. The UEA source describes
  16 competition-training subjects, split 10/6 between benchmark train/test;
  its prose refers to 306 original channels and 1.5 s recordings, which do not
  directly explain the released 144 x 62 representation. The channel/time-window
  conversion needs confirmation.
- **Papers:** UEA archive reference (Ruiz et al., 2021) above; the benchmark paper
  cites the competition rather than a separate acquisition paper.

## FeedbackButton

- **Original source / other names:** a feedback-guided button-response experiment
  described in Section 2.3 of the benchmark paper. No original accession, named
  collection, alternative name or acquisition paper is supplied. The
  [benchmark release](https://zenodo.org/records/18957700) is listed by
  [aeon's dataset registry](https://github.com/aeon-toolkit/aeon/blob/main/aeon/datasets/tsc_datasets.py).
- **Benchmark dimensions:** train `(1700, 61, 450)`, test `(1150, 61, 450)`;
  2 classes, 57 subjects, 500 Hz.
- **Derivation:** press versus no press in a task with positive/negative feedback;
  900 ms windows beginning 200 ms before the prompt and ending before the press.
- **Papers / status:** benchmark paper only; original source remains unresolved.
  Similarity to ButtonPress describes the task, not evidence of a shared collection.

## FeetHands

- **Original source / other names:** Schalk et al., *EEG Motor Movement/Imagery
  Dataset*; [PhysioNet eegmmidb](https://physionet.org/content/eegmmidb/1.0.0/)
  and [OpenNeuro ds004362 v1.0.0](https://openneuro.org/datasets/ds004362/versions/1.0.0).
- **Benchmark dimensions:** train `(2835, 64, 640)`, test `(1890, 64, 640)`;
  2 classes, 105 subjects, 160 Hz.
- **Derivation:** executed bilateral fist versus foot movements. The original
  collection has 109 participants; the benchmark removes four and extracts 4 s
  windows starting 1 s before onset. Shares its source with the other three motor
  movement/imagery problems below.
- **Paper:** Schalk et al. (2004), *BCI2000: A General-Purpose Brain-Computer
  Interface (BCI) System*, IEEE TBME 51(6), 1034-1043
  ([PubMed](https://pubmed.ncbi.nlm.nih.gov/15188875/)). The benchmark also cites the
  2022 OpenNeuro release; [PhysioNet dataset DOI](https://doi.org/10.13026/C28G6P).

## FibroLiverpool

- **Original source / other names:** University of Liverpool fibromyalgia study;
  no named public collection, accession or other dataset name supplied in Section
  2.1 of the benchmark paper. Research access is through Tony Bagnall.
- **Benchmark dimensions:** train `(15, 64, 15360)`, test `(21, 64, 15360)`;
  2 classes, 36 subjects in Table 1, 512 Hz (30 s per case).
- **Derivation / caveat:** eyes-open resting EEG, fibromyalgia versus control.
  The prose gives 19 patients and 18 controls (37 people), while the table and
  train/test sizes give 36. The omitted subject and recording release need confirmation.
- **Papers / status:** benchmark paper only; no separate acquisition publication
  identified. Restricted access; distinct cohort from FibroUEA.

## FibroUEA

- **Original source / other names:** University of East Anglia fibromyalgia/virtual
  reality treatment study; no public accession or alternative collection name
  supplied in Section 2.1. Research access is through Tony Bagnall.
- **Benchmark dimensions:** train `(17, 64, 15000)`, test `(23, 64, 15000)`;
  2 classes, 41 subjects reported, 500 Hz (30 s per case).
- **Derivation / caveat:** fibromyalgia versus control; source cohort described as
  27 patients and 14 controls. The paper describes sessions slightly under 2 min
  truncated to a common length, but the table implies 30 s and 40 cases. Subject
  exclusion and the exact extraction window remain unresolved.
- **Papers / status:** benchmark paper only; no separate acquisition publication
  identified. Restricted access.

## FingerMovements

- **Original source / other names:** Berlin BCI, Fraunhofer-FIRST and Freie
  Universitat Berlin; [BCI Competition II (2003), dataset IV](https://www.bbci.de/competition/ii/berlin_desc.html),
  *self-paced 1s* / self-paced key typing; inherited through UEA.
- **Benchmark dimensions:** train `(316, 28, 400)`, test `(100, 28, 400)`;
  2 classes, subjects unspecified in Table 1, reported frequency 128 Hz.
- **Derivation / caveat:** upcoming left versus right hand keypress. The original
  source identifies one subject, 500 ms epochs ending 130 ms before the press,
  at 1000 Hz (500 points) or 100 Hz (50 points). The
  [UEA description](https://www.timeseriesclassification.com/description.php?Dataset=FingerMovements)
  specifies 50 points at 100 Hz. Neither explains Table 1's 400 points at 128 Hz;
  the current local files have now been verified as 50 points at 100 Hz, from every case and the embedded source comments. The registry and sidecars reflect this version; no resampling was performed. Original recording frequency is 1000 Hz. See [local corrections](local-data-corrections.md).
- **Paper:** Blankertz, Curio and Muller (2002), *Classifying Single Trial EEG:
  Towards Brain Computer Interfacing*, Advances in Neural Information Processing
  Systems 14; cited by the competition source. Also Ruiz et al. (2021).

## HandMovementDirection

- **Original source / other names:** Freiburg/Tubingen;
  [BCI Competition IV (2008), dataset 3](https://www.bbci.de/competition/iv/desc_3.pdf),
  *Directionally modulated MEG activity*; inherited through UEA.
- **Benchmark dimensions:** train `(160, 10, 400)`, test `(74, 10, 400)`;
  4 classes, subjects unspecified in Table 1, 400 Hz. **Modality: MEG**.
- **Derivation:** right-wrist joystick movements in four directions. The
  [UEA description](https://www.timeseriesclassification.com/description.php?Dataset=HandMovementDirection)
  identifies subject 1 from a two-subject collection recorded at 625 Hz, filtered
  and resampled to 400 Hz, with 1 s movement-centred windows. Its prose also says
  length 500, inconsistent with its own table and the benchmark's length 400.
- **Papers:** Ruiz et al. (2021), plus the original competition dataset description
  linked above; acquisition-paper attribution should be confirmed from that release.

## ImaginedFeetHands

- **Original source / other names:** *EEG Motor Movement/Imagery Dataset*,
  [PhysioNet eegmmidb](https://physionet.org/content/eegmmidb/1.0.0/) /
  [OpenNeuro ds004362](https://openneuro.org/datasets/ds004362/versions/1.0.0),
  imagined bilateral fists versus feet task.
- **Benchmark dimensions:** train `(2835, 64, 640)`, test `(1935, 64, 640)`;
  2 classes, 105 subjects, 160 Hz.
- **Derivation / caveat:** 4 s windows starting 1 s before onset, four source
  participants removed, as for FeetHands. The 4,770 cases differ from the 4,725 in
  each sibling task; the paper does not explain the extra 45 test cases.
- **Paper:** Schalk et al. (2004), *BCI2000*, and Schalk et al. (2022) dataset
  release; see [FeetHands](#feethands) for citations.

## ImaginedOpenCloseFist

- **Original source / other names:** *EEG Motor Movement/Imagery Dataset*,
  [PhysioNet eegmmidb](https://physionet.org/content/eegmmidb/1.0.0/) /
  [OpenNeuro ds004362](https://openneuro.org/datasets/ds004362/versions/1.0.0),
  imagined left versus right fist task.
- **Benchmark dimensions:** train `(2835, 64, 640)`, test `(1890, 64, 640)`;
  2 classes, 105 subjects, 160 Hz.
- **Derivation:** imagined unilateral fist movements; same participant exclusion
  and 4 s window extraction as FeetHands.
- **Paper:** Schalk et al. (2004), *BCI2000*, and Schalk et al. (2022) dataset
  release; see [FeetHands](#feethands) for citations.

## InnerSpeech

- **Original source / other names:** Nieto et al.,
  [OpenNeuro ds003626 v2.1.0](https://openneuro.org/datasets/ds003626/versions/2.1.0),
  *Inner Speech* / *Thinking out loud*, inner-speech condition.
- **Benchmark dimensions:** train `(250, 128, 3584)`, test `(200, 128, 3584)`;
  4 classes, 9 subjects, 1024 Hz.
- **Derivation / caveat:** imagined speech of up/down/left/right. The source has ten
  participants and three conditions. The benchmark paper describes 3.5 s windows
  starting 0.5 s before the prompt and retaining the first 50 trials per word,
  task and participant. That description would imply more than 450 cases; the
  reduction to nine subjects and 450 cases per condition needs confirmation.
- **Paper:** Nieto et al. (2022), [Thinking out loud, an open-access EEG-based BCI
  dataset for inner speech recognition](https://doi.org/10.1038/s41597-022-01147-2),
  Scientific Data 9, 52. The benchmark cites the 2021 dataset release.

## LongIntervalTask

- **Original source / other names:** Singh et al.,
  [OpenNeuro ds004579](https://openneuro.org/datasets/ds004579), *Interval Timing Task*
  (accession confirmed by the [source metadata](https://raw.githubusercontent.com/OpenNeuroDatasets/ds004579/master/dataset_description.json)).
- **Benchmark dimensions:** train `(1660, 63, 4750)`, test `(1120, 63, 4750)`;
  2 classes, 139 subjects, 500 Hz (9.5 s per case).
- **Derivation:** Parkinson's disease versus control, using the 7 s self-timed
  button-hold condition; 94 patients and 45 controls. Shares the source cohort
  with ShortIntervalTask.
- **Paper:** Singh et al. (2023), [Evoked mid-frontal activity predicts cognitive
  dysfunction in Parkinson's disease](https://jnnp.bmj.com/content/94/11/945),
  Journal of Neurology, Neurosurgery & Psychiatry 94, 945-953.

## LowCost

- **Original source / other names:** Peterson et al.,
  [OpenNeuro ds003810](https://openneuro.org/datasets/ds003810),
  *Motor Imagery vs Rest - Low-Cost EEG System*.
- **Benchmark dimensions:** train `(600, 15, 375)`, test `(600, 15, 375)`;
  2 classes, 10 subjects, 125 Hz.
- **Derivation:** imagined dominant-hand movement versus rest; four sessions per
  subject, 15 trials per class per session; 3 s windows starting 200 ms before stimulus.
- **Paper:** Peterson et al. (2022), *A motor imagery vs. rest dataset with low-cost
  consumer grade EEG hardware*, Data in Brief 42, 108225
  ([DOI](https://doi.org/10.1016/j.dib.2022.108225)).

## MatchingPennies

- **Original source / other names:** Appelhoff, Sauer and Gill (2018),
  [eeg_matchingpennies on GIN](https://gin.g-node.org/sappelhoff/eeg_matchingpennies),
  *Matching pennies: A brain computer interface implementation dataset*.
- **Benchmark dimensions:** train `(700, 10, 10000)`, test `(700, 10, 10000)`;
  2 classes, 7 subjects, 5000 Hz.
- **Derivation:** left versus right hand raising during a game, while imagining
  raising the opposite hand; 100 trials per hand per subject, 2 s windows starting
  500 ms before stimulus, according to Section 2.3 of the benchmark paper.
- **References:** Appelhoff et al. (2018) is a dataset citation in the benchmark
  bibliography, not an identified journal paper. The original GIN endpoint could
  not be retrieved during this audit; extraction details here rely on the paper.

## MindReading

- **Original source / other names:** Aalto University,
  [ICANN/PASCAL2 MEG Mind Reading challenge (2011)](https://www.cis.hut.fi/icann2011/mindreading.php).
- **Benchmark dimensions:** train `(727, 204, 200)`, test `(653, 204, 200)`;
  5 classes, subjects unspecified in Table 1, 200 Hz. **Modality: MEG**.
- **Derivation:** one subject, two sessions on consecutive days; 1 s windows
  labelled screen saver, nature documentary, football, Mr. Bean or Chaplin.
- **Paper:** Klami, Ramkumar, Virtanen, Parkkonen, Hari and Kaski (2011),
  [ICANN/PASCAL2 Challenge: MEG Mind Reading - Overview and Results](https://research.cs.aalto.fi/pml/info/Klami11meg2.shtml),
  Aalto University Science + Technology 29/2011, pp. 3-19.

## MotorImagery

- **Original source / other names:** Tubingen, Max Planck Institute and Bonn;
  [BCI Competition III (2005), dataset I](https://www.bbci.de/competition/iii/desc_I.html),
  *motor imagery in ECoG recordings, session-to-session transfer*; inherited through UEA.
- **Benchmark dimensions:** train `(278, 64, 3000)`, test `(100, 64, 3000)`;
  2 classes, subjects unspecified in Table 1, 1000 Hz. **Modality: invasive ECoG**.
- **Derivation:** imagined left little-finger versus tongue movement in one subject;
  8 x 8 electrode grid, 3 s trials, train/test recorded on different days about
  one week apart. This is a different collection from eegmmidb.
- **Paper:** Lal et al., *Methods Towards Invasive Human Brain Computer Interfaces*,
  NIPS 2004 (as cited by the competition source); also Ruiz et al. (2021).

## OpenCloseFist

- **Original source / other names:** *EEG Motor Movement/Imagery Dataset*,
  [PhysioNet eegmmidb](https://physionet.org/content/eegmmidb/1.0.0/) /
  [OpenNeuro ds004362](https://openneuro.org/datasets/ds004362/versions/1.0.0),
  executed left versus right fist task.
- **Benchmark dimensions:** train `(2835, 64, 640)`, test `(1890, 64, 640)`;
  2 classes, 105 subjects, 160 Hz.
- **Derivation:** real unilateral fist movements; same participant exclusion and
  4 s window extraction as FeetHands.
- **Paper:** Schalk et al. (2004), *BCI2000*, and Schalk et al. (2022) dataset
  release; see [FeetHands](#feethands) for citations.

## PhotoStimulation

- **Original source / other names:** Ntetska et al.,
  [OpenNeuro ds006036 v1.0.2](https://openneuro.org/datasets/ds006036/versions/1.0.2),
  *A complementary dataset of open-eyes EEG recordings in a photo-stimulation
  setting from: Alzheimer's disease, Frontotemporal dementia and Healthy subjects*.
- **Benchmark dimensions:** train `(37, 19, 9000)`, test `(36, 19, 9000)`;
  3 classes, 73 subjects, 500 Hz.
- **Derivation:** an 18 s window during 10 Hz stimulation; 15 participants excluded
  from the related Alzheimer's cohort, leaving 31 Alzheimer's, 22 frontotemporal
  dementia and 20 controls. Same cohort does not mean the recordings are identical.
- **References:** Ntetska et al. (2025) dataset citation in the benchmark paper;
  the [source metadata](https://raw.githubusercontent.com/OpenNeuroDatasets/ds006036/master/dataset_description.json)
  additionally requests the complementary Data descriptor,
  [Data 10(5), 64 (2025)](https://doi.org/10.3390/data10050064).

## PronouncedSpeech

- **Original source / other names:** Nieto et al.,
  [OpenNeuro ds003626 v2.1.0](https://openneuro.org/datasets/ds003626/versions/2.1.0),
  *Inner Speech* / *Thinking out loud*, pronounced/overt speech condition.
- **Benchmark dimensions:** train `(250, 128, 3584)`, test `(200, 128, 3584)`;
  4 classes, 9 subjects, 1024 Hz.
- **Derivation:** speaking up/down/left/right aloud; 3.5 s windows starting 0.5 s
  before the prompt. Shares source and unresolved trial/subject selection with
  [InnerSpeech](#innerspeech).
- **Paper:** Nieto et al. (2022), [Thinking out loud](https://doi.org/10.1038/s41597-022-01147-2),
  Scientific Data 9, 52; 2021 dataset release cited by the benchmark.

## SelfRegulationSCP1

- **Original source / other names:** University of Tubingen,
  [BCI Competition II (2003), dataset Ia](https://www.bbci.de/competition/ii/tuebingen_desc_i.html),
  *self-regulation of SCPs* (slow cortical potentials); inherited through UEA.
- **Benchmark dimensions:** train `(268, 6, 896)`, test `(293, 6, 896)`;
  2 classes, subjects unspecified in Table 1, 256 Hz.
- **Derivation / split caveat:** one healthy subject controlling a cursor through
  cortical positivity/negativity; 3.5 s feedback intervals. The original source
  says train contains trials from days 1 and 2 and test is from day 2. This does
  not support a universal claim that recording days are disjoint in train/test.
- **Paper:** Birbaumer et al. (1999), *A Brain-Controlled Spelling Device for the
  Completely Paralyzed*, Nature 398, 297-298, cited by the competition source;
  also Ruiz et al. (2021).

## SelfRegulationSCP2

- **Original source / other names:** University of Tubingen,
  [BCI Competition II (2003), dataset Ib](https://www.bbci.de/competition/ii/tuebingen_desc_ii.html),
  *self-regulation of SCPs*; inherited through UEA. Distinct subject from SCP1.
- **Benchmark dimensions:** train `(200, 7, 1152)`, test `(180, 7, 1152)`;
  2 classes, subjects unspecified in Table 1, 256 Hz.
- **Derivation / split caveat:** one ventilated ALS patient controlling a cursor;
  4.5 s feedback intervals. Seven channels include a vertical EOG channel, so they
  are not all EEG. Source test trials follow training trials on the same day;
  a separate-session guarantee requires more evidence.
- **Paper:** Birbaumer et al. (1999), *A Brain-Controlled Spelling Device for the
  Completely Paralyzed*, Nature 398, 297-298, cited by the competition source;
  also Ruiz et al. (2021).

## ShortIntervalTask

- **Original source / other names:** Singh et al.,
  [OpenNeuro ds004579](https://openneuro.org/datasets/ds004579), *Interval Timing Task*.
- **Benchmark dimensions:** train `(1660, 63, 2750)`, test `(1120, 63, 2750)`;
  2 classes, 139 subjects, 500 Hz (5.5 s per case).
- **Derivation:** Parkinson's disease versus control using the 3 s self-timed
  button-hold condition; same source cohort as LongIntervalTask.
- **Paper:** Singh et al. (2023), [Evoked mid-frontal activity predicts cognitive
  dysfunction in Parkinson's disease](https://jnnp.bmj.com/content/94/11/945),
  JNNP 94, 945-953. See [LongIntervalTask](#longintervaltask) for source metadata.

## SitStand

- **Original source / other names:** Triana-Guzman et al.,
  [OpenNeuro ds005342](https://openneuro.org/datasets/ds005342), *EEG data offline
  and online during motor imagery for standing and sitting*.
- **Benchmark dimensions:** train `(3200, 17, 1250)`, test `(3200, 17, 1250)`;
  4 classes, 32 subjects, 250 Hz.
- **Derivation / caveat:** seated/standing idle states and imagined sit-to-stand /
  stand-to-sit movements; 5 s windows starting 200 ms before stimulus. The benchmark
  reports retaining 50 cases per class per participant. The source paper describes
  45 offline trials per class plus online trials; exact phase selection needs
  confirmation, and these labels should not all be described as executed movements.
- **Paper:** Triana-Guzman et al. (2022), [Decoding EEG rhythms offline and online
  during motor imagery for standing and sitting based on a brain-computer
  interface](https://doi.org/10.3389/fninf.2022.961089), Frontiers in Neuroinformatics
  16, 961089; linked by the [original dataset metadata](https://raw.githubusercontent.com/OpenNeuroDatasets/ds005342/master/dataset_description.json).

## Sleep

- **Original source / other names:** Sleep-EDF, distributed by
  [PhysioNet as Sleep-EDF Expanded](https://physionet.org/content/sleep-edfx/),
  via the processed EEG sleep-staging data in
  [TF-C](https://github.com/mims-harvard/TFC-pretraining) as **SleepEEG**
  ([processed Figshare release, version 1](https://figshare.com/ndownloader/articles/19930178/versions/1)).
  TF-C links Sleep-EDF Expanded v1.0.0; exact selected records remain to be pinned down.
- **Benchmark dimensions:** train `(2394, 1, 178)`, test `(1205, 1, 178)`;
  5 classes, 82 subjects reported, 100 Hz.
- **Derivation / caveat:** the benchmark describes 153 whole-night recordings,
  segmented into non-overlapping windows labelled W, N1, N2, N3 or REM. Its
  178-point length implies 1.78 s, so the relationship to conventional 30 s sleep
  epochs needs verification in the intermediate TF-C and benchmark files. TF-C's
  README instead reports 200-point windows and 371,055 examples, so it does not
  explain the benchmark's 3,599 cases of length 178.
- **Papers:** Zhang et al. (2022), [Time-Frequency Consistency](https://arxiv.org/abs/2206.08496),
  for the intermediate classification data; Kemp et al. (2000), *Analysis of a
  sleep-dependent neuronal feedback loop: the slow-wave microcontinuity of the
  EEG*, IEEE TBME 47(9), 1185-1194
  ([publisher](https://ieeexplore.ieee.org/document/867928/)), requested by PhysioNet.

## SongFamiliarity

- **Original source / other names:** Girard, Bishop and Hassall (2025),
  [OpenNeuro ds005876](https://openneuro.org/datasets/ds005876), *Song Familiarity*.
- **Benchmark dimensions:** train `(700, 32, 3000)`, test `(750, 32, 3000)`;
  2 classes, 29 subjects, 1000 Hz.
- **Derivation:** first 50 songs per participant; 3 s windows just before the
  familiarity button press. Labels indicate correct versus incorrect song
  identification from four options, rather than simply whether familiarity was reported.
- **References:** Girard et al. (2025) dataset citation in the benchmark paper.
  The [source metadata](https://raw.githubusercontent.com/OpenNeuroDatasets/ds005876/master/dataset_description.json)
  supplies no associated paper in `ReferencesAndLinks`; no separate acquisition
  paper was established in this audit.

## VisualSpeech

- **Original source / other names:** Nieto et al.,
  [OpenNeuro ds003626 v2.1.0](https://openneuro.org/datasets/ds003626/versions/2.1.0),
  *Inner Speech* / *Thinking out loud*, visual-imagery condition.
- **Benchmark dimensions:** train `(250, 128, 3584)`, test `(200, 128, 3584)`;
  4 classes, 9 subjects, 1024 Hz.
- **Derivation:** visualising a circle moving up/down/left/right; this condition
  is visual imagery despite the benchmark name. Same 3.5 s windows and unresolved
  trial/subject selection as [InnerSpeech](#innerspeech).
- **Paper:** Nieto et al. (2022), [Thinking out loud](https://doi.org/10.1038/s41597-022-01147-2),
  Scientific Data 9, 52; 2021 dataset release cited by the benchmark.

## Outstanding provenance checks

- Identify original releases and acquisition citations for ButtonPress,
  FeedbackButton, FibroLiverpool and FibroUEA.
- Pin the exact original release versions and conversion scripts used to produce
  the benchmark files; a link to a current collection alone does not establish this.
- Reconcile Sleep length, EpilepticSeizures
  frequency, FaceDetection channel/window selection, and the subject/trial counts
  flagged above against actual files and subject-index metadata.
- Audit the inherited splits before applying a blanket subject/session-disjoint
  guarantee: TF-C explicitly cannot guarantee recording-disjoint splits for
  Epilepsy, and the SCP source descriptions provide exceptions to the
  simpler recording-day interpretation. No metadata or evaluation code has been
  changed as part of this documentation audit.

## Three additional classification problems

These bring the local collection to 33 problems; the paper's benchmark and its
30 results remain as published. The additions use pinned OpenEEGBench
preparations: original training and validation are concatenated in order, and
the original test partition is retained. Full channel orders, labels, counts,
preprocessing and sidecar details are in [Additional EEG datasets](additional-datasets.md).

| Local problem | Task and dimensions (train; test) | Original source / paper | Other names and processed source |
|---|---|---|---|
| MentalArithmetic | Mental arithmetic vs rest; `(1515, 19, 1000)`; `(192, 19, 1000)` | PhysioNet EEGmat; Zyma et al. (2019), [DOI 10.3390/data4010014](https://doi.org/10.3390/data4010014) | EEGMAT; `braindecode/arithmetic_zyma2019` |
| ImaginedCommands | Five imagined commands; `(5250, 64, 600)`; `(750, 64, 600)` | 2020 International BCI Competition Track 3; Jeong et al. (2022), [DOI 10.3389/fnhum.2022.898300](https://doi.org/10.3389/fnhum.2022.898300) | `bcic2020-3`, NEMAR `nm000113`; `braindecode/bcic2020-3` |
| ChildhoodSeizures | Seizure vs background; `(34045, 17, 2000)`; `(2140, 17, 2000)` | CHB-MIT Scalp EEG Database; Guttag (2010), Shoeb (2009) | CHB-MIT, `chbmit`; `braindecode/chbmit` |

All are at 200 Hz. MentalArithmetic is the retained local preparation of the
PhysioNet EEGmat collection. A previous local EEGMAT-format export of the same
recordings was removed to avoid keeping two preparations of one source
collection. ImaginedCommands uses a within-subject run split. The
ChildhoodSeizures channels are renamed bipolar derivations; they are not
monopolar electrode locations. Each relationship and limitation is described
below.

### MentalArithmetic

- **Original source / other names:** Zyma et al.,
  [EEG During Mental Arithmetic Tasks](https://physionet.org/content/eegmat/1.0.0/),
  EEGmat / EEGMAT / OpenEEGBench Arithmetic. Original frequency 500 Hz.
- **Local dimensions:** train `(1515, 19, 1000)`, test `(192, 19, 1000)`;
  2 classes, 36 participants, 200 Hz, five-second windows.
- **Origin relationship:** This is derived from the same PhysioNet EEGmat
  recordings as the former local EEGMAT export (500 Hz/two-second windows,
  different split and selection). That duplicate local export was removed; the
  retained folder is `D:/Data/EEG/MentalArithmetic/`.
- **Paper / licence:** Zyma et al. (2019), *Electroencephalograms during Mental
  Arithmetic Task Performance*, Data 4(1), 14
  ([DOI](https://doi.org/10.3390/data4010014)); source data ODC-By-1.0.

### ImaginedCommands

- **Original source / other names:** [2020 International BCI Competition](https://osf.io/pq7vb/),
  Track 3 imagined speech; `bcic2020-3`, NEMAR `nm000113`. Source 256 Hz.
- **Local dimensions:** train `(5250, 64, 600)`, test `(750, 64, 600)`;
  5 classes, 15 participants, 200 Hz, three-second trials.
- **Derivation / split:** resampled preprocessed trials; run 00 plus run 01 forms
  training, run 02 forms test. All subjects intentionally occur on both sides;
  this is not subject-independent classification. Local folder
  `D:/Data/EEG/ImaginedCommands/`.
- **Paper / licence:** Jeong et al. (2022), *2020 International brain-computer
  interface competition: A review*, Frontiers in Human Neuroscience 16, 898300
  ([DOI](https://doi.org/10.3389/fnhum.2022.898300)); original OSF data CC BY 4.0.

### ChildhoodSeizures

- **Original source / other names:** [CHB-MIT Scalp EEG Database](https://physionet.org/content/chbmit/1.0.0/),
  Children's Hospital Boston/MIT; `chbmit`. Source 256 Hz.
- **Local dimensions:** train `(34045, 17, 2000)`, test `(2140, 17, 2000)`;
  2 classes, 22 known people represented by 23 case IDs, 200 Hz.
- **Derivation / split:** ten-second windows of 17 selected bipolar derivations.
  Distributed electrode-like names are renamings, not monopolar sensor positions;
  original pairs are retained in sidecars. Train IDs chb01-chb21, test chb22/chb23;
  chb01/chb21 represent one person, both in training. The fixed protocol omits
  chb24. Local folder `D:/Data/EEG/ChildhoodSeizures/`.
- **References / licence:** Guttag (2010), dataset DOI
  [10.13026/C2K01R](https://doi.org/10.13026/C2K01R); Shoeb (2009), *Application
  of Machine Learning to Epileptic Seizure Onset Detection and Treatment*, MIT
  PhD thesis. Source data ODC-By-1.0.

### MatchWords

- **Original source / other names:** [Auditory single word recognition in MEG](https://openneuro.org/datasets/ds004276/versions/1.0.0), OpenNeuro `ds004276` v1.0.0. The archive name `MatchWords` refers to the semantic relatedness judgement task; the cases are MEG epochs, not EEG.
- **Local dimensions:** train and test each contain 360 cases of 156 channels by 1,500 timepoints (1.5 seconds at 1,000 Hz), with 180 `No` and 180 `Yes` labels per split. The data are in `D:/Data/EEG/MatchWords/`.
- **Local correction:** Original axis 55 was constant in all 720 cases and has been removed. Retained values were multiplied by 1e15 (T to fT) using float64. Source channel tables retain the original 157 sensors; current sidecars identify the 156 retained axes. See [local corrections](local-data-corrections.md).
- **Subjects and channels:** The source lists 18 participants (`sub-001`â€“`sub-018`) and provides 157 axial gradiometer channels, `MEG 001`â€“`MEG 157`, in the same order for every participant. `MEG 056` is marked bad for all participants. The source order and count are recorded in the sidecars. The `.ts` files have no per-case participant IDs or sensor names, so participant-to-case mapping and direct proof of the local array channel order are unavailable; the channel order is therefore a source-based correspondence, not independently verified against the exported arrays.
- **Labels / task:** `Yes` and `No` denote semantic relatedness responses to written probes following auditory words. They do not describe imagined movement or a spoken yes/no response.
- **Paper / licence:** Gaston, Brodbeck, Phillips & Lau, *Auditory Word Comprehension Is Less Incremental in Isolated Words*, Neurobiology of Language 4(1), 29â€“52 ([DOI](https://doi.org/10.1162/nol_a_00084)). The OpenNeuro v1.0.0 dataset declares CC0.

### Excluded: Depression (MDDMumtaz2016)

- **Original source / other names:** Mumtaz (2016), *MDD Patients and Healthy
  Controls EEG Data (New)*, [Figshare v2](https://doi.org/10.6084/m9.figshare.4244171.v2);
  `mdd_mumtaz2016`, NEMAR `nm000114`. Source-reported 256 Hz.
- **Audited source dimensions (removed):** train `(8300, 19, 1000)`, test `(6443, 19, 1000)`;
  2 classes, 64 subject IDs, 200 Hz, five-second windows.
- **Quality / location:** 121 distinct P300 windows repeat across different
  source subject IDs, affecting 726 train and 484 test cases. This was independently
  verified in the pinned processed source before conversion. The prepared signal arrays and quarantined `.ts` export have been deleted,
  and this dataset is excluded from download/export choices. Only diagnostic
  reports remain. See the [upstream issue draft](issues/mdd-duplicate-windows.md).
- **Paper / licence:** Mumtaz et al. (2017), *Electroencephalogram (EEG)-based
  computer-aided technique to diagnose major depressive disorder (MDD)*,
  Biomedical Signal Processing and Control 31, 108-115
  ([DOI](https://doi.org/10.1016/j.bspc.2016.07.006)); original Figshare data CC BY 4.0.

### FlickerSymbols

- **Original source / other names:** Wang2016, Tsinghua SSVEP Benchmark, Wang/Chen/Gao/Gao 40-target speller; paper DOI [10.1109/TNSRE.2016.2627556](https://doi.org/10.1109/TNSRE.2016.2627556). Source signals: pinned Zenodo record 14865172 MATLAB files, all 35 participants. NEMAR nm000126 is a 34-participant derivative and is not substituted.
- **Local dimensions:** train `(6240, 64, 1500)`, test `(2160, 64, 1500)`; 40 classes, 35 subjects, one documented session and six blocks per subject, 250 Hz (1000 Hz acquisition). Subject-disjoint split balances experience groups; no validation split.
- **Task / processing:** attended visual target identity, original labels 1?40 with source frequency/phase mapping. Full six-second native epochs, microvolt numeric scale, exact float64 decimal export; no added numerical preprocessing. Original source .loc defines array sensor order; CB1/CB2 and polar positions are preserved. Original continuous offsets and within-block chronology remain unavailable.
- **Licence / report:** CC BY 4.0 declared by the Zenodo data release and NEMAR. Original lab README lacks an explicit grant; redistribution applicability remains a release-review item. See [complete provenance, split and validation](flicker-symbols-preparation.md).

### Compact MOABB source collections

These six new preparations have subject IDs on every case. The
[complete source/processing report](small-moabb-preparations.md),
[source lock](small-moabb-source-lock.json) and
[measured validation results](small-moabb-local-results.json) support source-origin comparisons.

| Archive name | Original source and aliases | Current TRAIN / TEST shapes | Classes; Hz | Original reference |
|---|---|---|---|---|
| FlickerTargets | Nakanishi2015; author repository `mnakanishi/12JFPM_SSVEP`, revision `2d4e281a430b4676f75c9270db839e963f172da5` | `(1440,8,1114)` / `(360,8,1114)` | 12; 256 | Nakanishi et al. (2015), [10.1371/journal.pone.0140703](https://doi.org/10.1371/journal.pone.0140703) |
| ImaginedHandSides | BCI Competition IV 2b; Graz dataset B; BNCI2014_004 / 004-2014 | `(3680,3,1125)` / `(2840,3,1125)` | 2; 250 | Leeb et al. (2007), [10.1109/TNSRE.2007.906956](https://doi.org/10.1109/TNSRE.2007.906956) |
| SpellerFlashes | BNCI2015_003 / 003-2015; Guger2009 visual P300 speller | `(12600,8,205)` / `(12600,8,205)` | 2; 256 | Guger et al. (2009), [10.1016/j.neulet.2009.06.045](https://doi.org/10.1016/j.neulet.2009.06.045) |
| ImaginedHandsFeet | Zhou2016; original Figshare `2061654`; actual pinned EDF/BIDS source Zenodo `16534752` | `(1365,13,1250)` / `(435,13,1250)` | 3; 250 | Zhou et al. (2016), [10.1371/journal.pone.0162657](https://doi.org/10.1371/journal.pone.0162657) |
| ALSAttention | BNCI2014_008 / 008-2014; Riccio2013 ALS P300 speller | `(14400,8,256)` / `(19200,8,256)` | 2; 256 | Riccio et al. (2013), [10.3389/fnhum.2013.00732](https://doi.org/10.3389/fnhum.2013.00732) |
| WirelessFlicker | MAMEM3; MAMEM EEG SSVEP Dataset III; original Figshare `3413851` version 3 | `(1000,14,640)` / `(375,14,640)` | 5; 128 | Nikolopoulos, original data [10.6084/m9.figshare.3413851.v3](https://doi.org/10.6084/m9.figshare.3413851.v3) |

BCI IV 2b is a separate recording collection from our BCI IV 2a
ImaginedHandFeetTongue preparation. Its bipolar derivations are not a
three-channel subset view of our 22-channel IV 2a arrays. Likewise, shared
left/right imagery labels do not make it a view of Weibo2014. Nakanishi2015 and
Wang2016 are separately documented 12- and 40-target studies. MAMEM3 is a
separate experiment from MAMEM1/2, neither of which is prepared here; retain
the common MAMEM source-family identifier if those are added later.

ImaginedHandsFeet retains all distributed cases but removes original Fp2
(index 1) globally after three saturated constant test windows; its original
source has 14 channels. All arrays use microvolt numeric scale and exact
float64 decimal representation. Original source files, source electrode lists,
selection mappings and missing-metadata flags accompany the exports.

For source checks, compare original accessions, source-file hashes, participant,
session/run, event/tensor indices, labels and window bounds. Matching task names
or dimensions alone are insufficient. Local case hashes refer to the retained,
unit-documented signal arrays, which can differ from another preparation of
the same underlying recordings.


## WalkingTargets (BCIComp2020WalkingERP)

Original [OSF pq7vb](https://osf.io/pq7vb/), 2020 International BCI Competition Track 5 / Data Set-E, alias BCIComp2020WalkingERP; pinned loader also declares NEMAR mirror nm000184. Classify visual target/non-target during treadmill walking; distinct task from ImaginedCommands (Track 3). Jeong et al. (2022), [review DOI 10.3389/fnhum.2022.898300](https://doi.org/10.3389/fnhum.2022.898300); this is a paper DOI, not an established dataset DOI. Original data CC BY 4.0, verified through original OSF licence API.

TRAIN `(3600,42,100)`, TEST `(900,42,100)`, 100 Hz, two classes, 15 participants shared intentionally under official temporal partitioning. Merge original training and validation; preserve test. Source 56 inputs include 46 EEG; exclude EOG/IMU and remove four globally flat ear sensors L1/L2/R1/R4. Exact ordered sensor names, native indices, source epochs and original partitions accompany arrays. Original physical units are not explicit: microvolt interpretation is inferred and numbers unchanged. Original continuous offsets/session/run IDs and ear reference remain unknown. Repeated standing calibration is not another classification dataset. See [full provenance, labels, source lock and metadata completeness](walking-targets-preparation.md).


## SymbolAttention (Chailloux2020)

- **Original source:** OpenNeuro `ds003190` v1.0.1, [data DOI 10.18112/openneuro.ds003190.v1.0.1](https://doi.org/10.18112/openneuro.ds003190.v1.0.1), Git `153d0a1633adbf7d079eeabc866a2ad727bcff46`. Original dataset CC0, verified in its own licence and description.
- **Aliases:** Chailloux2020; Single-Option P300-BCI; *Assesment of the visual stimuli properties in P300 paradigm*. Pinned loader raw mirror `on003190`; NEMAR `nm000262` is a derivative of this source, not another study.
- **Task/dimensions:** attended target versus non-target symbols; TRAIN `(521259,8,256)`, TEST `(175180,8,256)`, 256 Hz, 19 participants / 56 available sessions / 381 included recordings. Whole people split 14/5, no shared subjects. Native EEG order FZ,Cz,P3,PZ,P4,PO7,PO8,Oz; Timestamp excluded. Numeric values unchanged; physical microvolt units inferred.
- **Reference:** Chailloux Peguero, Mendoza-Montoya and Antelis (2020), [paper DOI 10.3390/s20247198](https://doi.org/10.3390/s20247198).
- **Source caveats:** one exact copied recording excluded after waveform/event verification; two no-flash placeholders and 179 unlabelled flashes excluded. BIDS sensor types/units are incomplete; sample fields are one-based and native timestamps already lose float32 precision. [Full source identity, exclusions, metadata and pinned files](symbol-attention-preparation.md).

## ArmCoordination (Kueper2024)

- **Original source / aliases:** Kueper2024; *EEG dataset of unilateral and bilateral movement executions*, [Zenodo 10229480 / data DOI](https://doi.org/10.5281/zenodo.10229480). Original CC BY 4.0 data grant; publisher file hash pinned. Different source from Ofner2017/ArmMovements.
- **Task/dimensions:** executed right-arm-only versus both-arm reaching; TRAIN `(1498,64,1500)`, TEST `(505,64,1500)`, 500 Hz, 8 healthy participants / 49 recordings. Subject-disjoint 6/2 split. Native 64 EEG labels/order retained; three accelerometers excluded. Explicit microvolt resolution is applied after float64 casting.
- **Reference:** Kueper, Kim and Kirchner (2024), Scientific Reports 14:16690, [paper DOI 10.1038/s41598-024-65910-8](https://doi.org/10.1038/s41598-024-65910-8).
- **Source caveats:** 2,003 native movement onsets exceed nominal trial counts; retain all with source flags rather than invent valid-trial repairs. Marker keys repeat, so line ordinals/sample positions are retained. XP01 set4 continues set3. Hardware/software filter tables differ; both are preserved. This condition task differs from the paper's movement-versus-rest classifiers. [Full provenance, participant metadata, exact sensor order, flags and preprocessing](arm-coordination-preparation.md).


## ImaginedHandGestures (MOVING2024)

- **Original source/aliases:** MOVING; MOVING2024; EEG/virtual-glove hand tracking,
  [data DOI10.5281/zenodo.12804784](https://doi.org/10.5281/zenodo.12804784), v1,
  publisher-checksummed `edf.rar`. Original-host CC BY4.0; glove archive unnecessary.
- **Task/dimensions:** three imagined right-hand actions plus rest; TRAIN
  `(382,17,3000)`, TEST `(143,17,3000)`,500Hz,11 participants. EEG order, scale,
  source markers, file/date/subject and sample intervals retained. Assigned sole
  session/run IDs distinguished from embedded metadata. Reference/individual
  positions unknown. Whole subjects01-08/09-11; no shared people or cases.
- **Recording relationship:** imagination/execution intervals share each original
  acquisition and rest segments. This entry contains MI plus rest only; a later
  execution view must not be counted as wholly independent recordings.
- **Reference/caveats:** Mattei et al.(2024),
  [10.3390/s24165207](https://doi.org/10.3390/s24165207). Fixed task ordering;
  three absent source markers,15 globally flat EEG sensors removed. Native EDF
  calibrated volts cast float64 before multiplying1e6. No other numerical
  processing. [Complete metadata and source lock](compact-imagery-preparation.md).

## ImaginedArmTasks (Zhang2017)

- **Original source/aliases:** Zhang2017; KI; elbow-centred kinesthetic motor
  imagery, [data DOI10.6084/m9.figshare.5579461.v1](https://doi.org/10.6084/m9.figshare.5579461.v1),
  `KI.rar`,180 native BCI2000 files. Original-host CC BY4.0.
- **Task/dimensions:** nine imagined upper-limb tasks plus rest; TRAIN
  `(3240,17,3960)`, TEST `(1080,17,3960)`,1000Hz,12 participants,15 runs each,
  H1-H9/H10-H12 subject split. Native source IDs, stimulus code/caption matrix,
  run/session, sample bounds, storage times and gain/offset retained. Source
  column ordering preserved without hemisphere flip. Paper Table2 demographics
  retain H01-style published IDs alongside H1-style original directory IDs.
- **Essential unresolved metadata:** no native electrode names in any header.
  source_column_00..16 are explicit ordinal identifiers; anatomical names/order
  correspondence unknown, no inferred EGI sensor labels or coordinates. Cz
  reference/COM ground are publication statements. Numeric validation does not
  resolve these anatomical metadata gaps; the dataset is flagged accordingly.
- **Reference/caveats:** Zhang, Yong and Menon(2017),
  [10.1371/journal.pone.0188293](https://doi.org/10.1371/journal.pone.0188293).
  Three cues last3960 samples; all others4000. Crop first3960 consistently;
  exclude one40-sample initial state fragment in H6run01. Actual4320 complete
  intervals take precedence over inconsistent nominal counts. Calibration
  `(raw-offset)*gain` follows explicit BCI2000 header values after float64 casting.
  [Complete metadata, flags and reproducibility](compact-imagery-preparation.md).

## MIMED / ImaginedHandsTrunk: full preparation stopped

Original [Mendeley zs25xxjkm9 v3](https://doi.org/10.17632/zs25xxjkm9.3), CC BY4.0;
Wirawan et al.(2024), [paper10.1016/j.dib.2024.110833](https://doi.org/10.1016/j.dib.2024.110833).
The30-person,14-channel,128Hz imagery archive contains85cross-ID exact duplicate
window pairs. Seven participant pairs share all12 selected cases and their
complete block arrays. A further P05 stand/sit versus P06 right-hand crop has
conflicting classes. None are flatlines. The complete-source export was stopped;
no final dataset or registry entry added, no identity/class guessed. A14-person
unimplicated subset would require explicit scope selection. See the
[native audit](mimed-native-quality-audit.json) and
[local reproduction/issue draft](issues/mimed-cross-participant-copies.md).


## NeuroTUM: ImaginedRightHandFeetRest / ImaginedLeftRightHandRest

Original [Zenodo18087806 v1.0.0](https://doi.org/10.5281/zenodo.18087806), aliases
NeuroTUMBCI2025/neuroTUM-BCI Cybathlon. Original CC BY4.0 verified; software/paper
licences are separate. Reference Tscherniak et al.,
[10.48550/arXiv.2511.23384](https://doi.org/10.48550/arXiv.2511.23384).

- **P1 / ImaginedRightHandFeetRest:** rest/right-hand/legs imagination, one
  tetraplegic person, five sessions;150/40cases,24channels x750points,250Hz.
  NativeS1-S4train,S5test. Original YAML maps left arrow to LEGS MI, not left hand.
- **P2 / ImaginedLeftRightHandRest:** rest/left-hand/right-hand imagination, one
  healthy person, three sessions;480/240cases,24x750,250Hz. S1-S2train,S3test.
- These are **one study, two individual classification problems**, distinct
  recordings, no cross-person copied cases found. Intentional within-person
  transfer, not unseen-person evaluation. Exact source files/samples/marker IDs
  and exception reason retained. Original source files have no official split.
- Native24channel labels/order/EEG type and capXYZ descriptors recovered from XDF,
  retaining actual case. XYZ physical units/frame/measurement status and reference
  unknown; no guessed montage. Presumed microvolt numeric values cast float64
  unchanged. Native shared-host timestamp alignment with no clock fit/dejitter,
  no filtering/resampling/rereferencing. P1S3coincident empty markers preserved.

Full [source pins, mappings, metadata and validation](neurotum-preparation.md).
These files are now under D:/Data/EEG following checksum-verified relocation.
Their original C:/Temp conversion did not access D: while it was offline.

## ImaginedHandFootActions (MILimbEEG)

Original [Mendeley x8psbz3f6x v2](https://doi.org/10.17632/x8psbz3f6x.2), alias
MILimbEEG motor imagery only. Original CC BY4.0 data grant. Asanza et al.(2023),
[10.1016/j.dib.2023.109540](https://doi.org/10.1016/j.dib.2023.109540).
Source combines execution M and imagination I; this entry uses **I only**,
including original baseline/rest classes, not a diagnostic view of annotations.

Eight original classes,60 people,125Hz,500points; TRAIN `(2727,11,500)`, TEST
`(930,11,500)`, S1-S45/S46-S60whole-subject split. Original16numbered CSV columns
map through the author's indexed electrode graphic; no unverified standard
montage. Explicit source microvolt units preserved, no scale/filter/resample
change. Original sample index verified0..499; offsets within continuous records
and session visits unknown. R1 is native repetition. Participant annotation
tokens are uncorrected source strings; ages/height units not guessed.

The original3719I epochs include31copied rest pairs across S1/S2. All62 ambiguous
copies are excluded, no guessed owner retained. Source S22I2trial5 missing;
five globally flat sensors removed: F4,FC1,Cz,CP1,T8. Final remaining order
FC5,F3,Fz,FC6,FC2,T7,CP5,C3,CP2,C4,CP6. All exclusions/hashes/case accounting
and missing metadata are explicit. Original source CSVs preserved under D:/Data/EEGSources/MILimbEEG;
only admitted classification arrays reflect the changes. This is one source
study, not separate new studies for each limb/rest/clinical label.
[Full source identity, audit and output validation](milimb-preparation.md).


## ImaginedHandsRobot (Farabbi2020)

Original *Motor-Imagery EEG Dataset During Robot-Arm Control*,
[Zenodo5882500 v1](https://doi.org/10.5281/zenodo.5882500), CC BY4.0 original-data
grant; related Farabbi thesis [10589/164451](https://hdl.handle.net/10589/164451).
Aliases Farabbi2020. Twelve participants, three days each, left/right-hand
imagery with robot feedback.144MIrecordings,36sessions. TRAIN/TEST each
`(2880,32,1000)` at250Hz, original training/online phases; people and sessions
intentionally shared. Not independent-person or strictly chronological evaluation.
Native calibrated EEG converted volts to microvolts in float64; exact channel
order supplied by indexed original chanlocs.locs, not generic GDF ChannelN labels
alone. Author polar positions retained; reference/ground and measured individual
geometry unknown. No extra DSP, no removed EEG sensors, no exact duplicates.
[Complete recovery and source locks](imagined-hands-robot-preparation.md).


## ImaginedGrasps (BCI Competition2020 Track4)

Original [OSFpq7vb Track4](https://osf.io/pq7vb/), original CC BY4.0 project grant,
49pinned files5.811GB; no separately established dataset DOI. Aliases
BCIComp2020UpperLimb,2020InternationalBCICompetitionTrack4. Reference Jeong
et al.(2022), [10.3389/fnhum.2022.898300](https://doi.org/10.3389/fnhum.2022.898300).
Cylindrical/spherical/lumbrical grasp imagination,15people,45recordings over
three days/person. TRAIN `(4500,60,1000)`, TEST `(2250,60,1000)`,250Hz. Original
training then validation days merged, original test preserved; shared people
intentional. Native epo.x[1500:2500] is imagery0..3996ms; masked test-cue interval
is excluded. Names/order/montage from actual epo/mnt agree with organiser numbered
sensor table and across all45files. FCz reference,Fpz ground; coordinate
frame/units unspecified. Native numeric float64 scale unchanged, microvolt
interpretation inferred rather than proven. TrueLabel workbook supplies test
labels; root answer workbook is only a prediction template. No flat-channel
removals or exact duplicate cases. Continuous offset/interval overlap unknown.
Track3speech/Track5ERP are different recordings/tasks in the same project;
participant independence is not established.
[Full source lock, inconsistencies and recovered metadata](imagined-grasps-preparation.md).


## ImaginedHandsEmbodiment (Vagaja2023)

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


## ImaginedHandsHaptics (Batista2022)

TRAIN `(3083,32,2495)`, TEST `(1034,32,2495)`; two classes, 500 Hz.

Left/right-hand imagination with abstract, motor-observation, VR and haptic
feedback, pooled as one problem. Twenty original participants, one native
session each, 99 imagery recordings. Executed-movement ME controls excluded.
Keep actual source cues: 4,127 cues become 4,117 cases after ten unusable
timing/discontinuity trials are excluded. The common safe crop is 2,495 samples
at 500 Hz. Native 32 EEG names/order and explicit microvolt calibration retained;
float32 digital samples calibrated in float64, no added DSP. Auxiliary labels
vary without changing EEG order; generic roles and missing geometry stay unknown.
Native main/pilot IDs remain distinct. Whole-subject 15/5-person split balances
pilot/main cohorts. No exact recording or cue-prefix matches with
ImaginedHandsEmbodiment; this does not establish cross-study participant identity.
Original [Zenodo 7664069 v1](https://doi.org/10.5281/zenodo.7664069), CC BY 4.0;
Batista et al. (2022), *Physiological Signals During Motor Imagery Brain-Computer
Interface Training Using Virtual Reality and Haptics*. MOABB alias Batista2022;
declared NEMAR view nm000318 is not another independent dataset.

No EEG sensors removed or exact duplicate cases found; full readback, metadata,
sensor-order and aeon compatibility checks passed.
[Complete recovery, source pins and metadata limitations](mi-next-three-preparation.md).


## ImaginedAnkleRest (PoloHortiguela2025)

TRAIN `(264,28,1000)`, TEST `(132,28,1000)`; two classes, 250 Hz.

Imagined dominant-ankle dorsal/plantar flexion versus relaxation, six people,
one original S1 visit each. STATIC/MOTION exoskeleton conditions are pooled,
not counted as separate visits or problems. Original 132 repetition files each
supply two relaxation windows and one imagery window: first four seconds of
each native labelled phase, 396 cases. Initial settling/audio/return phases
excluded. Native 28 EEG labels/order, 250 Hz, raw float64 numbers and configured
2D layout retained; four EOG and three inertial channels excluded. Microvolt
interpretation inferred; explicit physical units, reference/ground and coordinate
units/frame were not recovered. No added DSP or supplied processed blocks used.
Whole-subject release B01–B04 TRAIN, B05–B06 TEST. Release B06 internally identifies
B07; preserve both IDs with the verified one-to-one mapping.
Original [Zenodo 14672334 v1](https://doi.org/10.5281/zenodo.14672334), CC BY 4.0;
Polo-Hortiguela et al. (2025), *EEG Signal Dataset During Dorsiflexion and Plantar
Flexion Movements*. MOABB alias PoloHortiguela2025, declared NEMAR view nm000302.

No EEG sensors removed or exact duplicate cases found; full readback, metadata,
sensor-order and aeon compatibility checks passed.
[Complete recovery, source pins and metadata limitations](mi-next-three-preparation.md).


## ImaginedHandsFeedback (Leeuwis2021)

TRAIN `(6560,16,1250)`, TEST `(2240,16,1250)`; two classes, 250 Hz.

Left/right-hand imagination by 55 novice BCI users, one visit and four runs
per person: calibration plus three feedback runs, 8,800 cases. Original
non-contiguous subject IDs 7–67 and native 16 EEG column order retained. Locate
actual zero time at epoch index 749 and keep 1,250 samples, 0–4.996 seconds,
at 250 Hz. Native decimal values parsed as round-trip float64 and unchanged;
microvolt interpretation inferred. Original report/paper documents right-earlobe
reference and AFz ground; individual positions and continuous offsets unknown.
Paper filtering protocol retained separately from uncertain exact CSV filtering
history; no added DSP. Whole-subject first 41 numeric native IDs TRAIN, remaining
14 TEST, pooling original calibration/feedback phases. Individual questionnaire
metadata mapped by ppnr: 55 rows, 36 Female/19 Male; the report's 57-person totals
are inconsistent. Irregular Subject40 filenames and pinned file IDs preserved.
Original [DataverseNL 10.34894/Z7ZVOD v1.0](https://doi.org/10.34894/Z7ZVOD),
version ID 3733, CC BY 4.0; Leeuwis, Paas and Alimardani (2021), *Psychological
and Cognitive Factors in Motor Imagery Brain Computer Interfaces*.
Related [Frontiers paper](https://doi.org/10.3389/fnhum.2021.634748).
MOABB alias Leeuwis2021, declared NEMAR view nm000327.

No EEG sensors removed or exact duplicate cases found; full readback, metadata,
sensor-order and aeon compatibility checks passed.
[Complete recovery, source pins and metadata limitations](mi-next-three-preparation.md).
## Daly2020 / OpenNeuro ds002720: reviewed cross-subject duplicate

On 9 November 2026, original `sub-09/eeg/sub-09_task-run10_eeg.edf` and
`sub-15/eeg/sub-15_task-run10_eeg.edf` were confirmed to identify the same
Git-annex object and have identical complete-file SHA256, with identical event
tables. Native headers do not establish the true participant. The derived
conversion excludes both ambiguous run-10 copies, retaining other eligible runs
of both subjects, and re-audits all retained cases. Original sources are kept.
This prevents copied recordings entering TRAIN under09 and TEST under15.
See [investigation and reporting route](daly-duplication-investigation.md),
[machine-readable evidence](daly-cross-subject-duplicate-audit.json) and
[ready-to-paste issue draft](daly-duplication-issue-draft.md). The user reported the issue to OpenNeuro on 9 November 2026. Corrected full conversion passed: 1,698 TRAIN / 643 TEST, 18 subjects, 19 EEG channels, 20,000 samples at 1,000 Hz; no duplicate retained cases or shared subjects.


## Further motor imagery source identities
### ImaginedHandsOnline

Original/source aliases: **Pan2025**. [10.7910/DVN/GH74ZG](https://doi.org/10.7910/DVN/GH74ZG); Pan(2025), Cross-Session Motor Imagery EEG dataset; related Pan et al.(2023), DOI10.1088/1741-2552/ad0a01. Data grant: CC0-1.0. Revision: Harvard Dataverse 10.7910/DVN/GH74ZG; publisher DataCite metadata version 1.0; immutable numeric datafile IDs and recorded content hashes (dataset-version API unavailable). 10 native participant IDs; 28 x 1000, 250 Hz, 2 classes, 2123/1519 TRAIN/TEST. Original session1 and session2 first30 trials TRAIN, remaining session2 trials TEST; intentional shared participants. Native numbers cast to float64; presumed microvolts according to pinned loader, physical unit not embedded. No added filtering, resampling, demeaning, baseline or reference. Native epoch/crop identity retained; original continuous offsets unavailable. Match original source file IDs/hashes and native case indices using [pan25 source lock](pan25-to-30-source-lock.json); repository aliases do not establish different recordings. Both complete Pan releases passed the [native waveform comparison](pan-full-native-identity-audit.json); participant identity across studies remains unestablished.

### ImaginedHandsCrossSession

Original/source aliases: **Pan2023**. [10.7910/DVN/251NOW](https://doi.org/10.7910/DVN/251NOW); Pan et al.(2023), DOI10.1088/1741-2552/ad0a01. Data grant: CC0-1.0. Revision: Harvard Dataverse 10.7910/DVN/251NOW; publisher DataCite metadata version 1.3; immutable numeric datafile IDs and recorded content hashes (dataset-version API unavailable). 14 native participant IDs; 28 x 1000, 250 Hz, 2 classes, 2400/960 TRAIN/TEST. Whole-subject original01-10 TRAIN,11-14 TEST. Native numbers cast to float64; presumed microvolts according to pinned loader, physical unit not embedded. No added filtering, resampling, demeaning, baseline or reference. Native epoch/crop identity retained; original continuous offsets unavailable. Match original source file IDs/hashes and native case indices using [pan23 source lock](pan23-to-30-source-lock.json); repository aliases do not establish different recordings. Both complete Pan releases passed the [native waveform comparison](pan-full-native-identity-audit.json); participant identity across studies remains unestablished.

### ImaginedHandPupils

Original/source aliases: **Rozado2015**. [10.7910/DVN/28932](https://doi.org/10.7910/DVN/28932); Rozado, Duenser and Gruen (2015), DOI10.1371/journal.pone.0121262. Data grant: CC0-1.0. Revision: Harvard Dataverse 10.7910/DVN/28932; publisher DataCite metadata version 2.2; immutable numeric datafile IDs and recorded content hashes (dataset-version API unavailable). 30 native participant IDs; 32 x 3072, 512 Hz, 2 classes, 1150/400 TRAIN/TEST. Whole-subject1-11 and16-26 TRAIN;12-15 and27-30 TEST. Explicit native XDF EEG microvolts cast to float64; select32 EEG by native type/order, exclude trigger/EX/AUX. Six seconds at nominal512Hz per cue. Raw common-host timestamps retained; no clock correction, interpolation, filter or reference change. Known noisy subjects retained with flags. Match original source file IDs/hashes and native case indices using [rozado source lock](rozado-to-30-source-lock.json); repository aliases do not establish different recordings.

### ImaginedHandsPhysiology

Original/source aliases: **Cho2017**. [10.5524/100295](https://doi.org/10.5524/100295); Cho, Ahn, Ahn, Kwon and Jun (2017), DOI10.1093/gigascience/gix034. Data grant: CC0-1.0. Revision: GigaDB10.5524/100295 release2017-05-05; exact publisher object MD5/size pins. 52 native participant IDs; 64 x 1536, 512 Hz, 2 classes, 7880/2640 TRAIN/TEST. Whole-subject01-39 TRAIN,40-52 TEST. Native class-array values cast to float64, presumed microvolts; actual imagery_event onsets define3-second crops. Original trial_sequence values order cases across classes. No mean removal, synthetic gaps or extra DSP. Native coordinates retained; no anatomical names embedded. Match original source file IDs/hashes and native case indices using [cho source lock](cho-to-30-source-lock.json); repository aliases do not establish different recordings.

### ImaginedHandMusicTempo

Original/source aliases: **Daly2020**. [10.18112/openneuro.ds002720.v1.0.1](https://doi.org/10.18112/openneuro.ds002720.v1.0.1); Daly et al., tempo-based brain-computer music interface data, OpenNeuro ds002720 v1.0.1, with original2014/2018 references in README. Data grant: CC-BY-4.0. Revision: OpenNeuro ds002720 v1.0.1; Git commit f704b13bed4383af66b6aef93faa18aeb336c0ca, original annex MD5/SHA256 identities verified then SHA256 recorded. 18 native participant IDs; 19 x 20000, 1000 Hz, 2 classes, 1698/643 TRAIN/TEST. Whole-subject01-13 TRAIN,14-18 TEST; all native labelled non-calibration runs retained. Original calibrated EDF volts multiplied by1e6 in float64; native BIDS event onsets define20-second cases. Both byte-identical09/15run10 copies excluded because true participant attribution is unresolved; all other unique complete runs retained and strictly audited for duplicates. No extra DSP. Original README CC BY4.0 and dataset_description CC0 discrepancy retained, conservative attribution terms. Match original source file IDs/hashes and native case indices using [daly source lock](daly-to-30-source-lock.json); repository aliases do not establish different recordings.

### AlzheimersAuditory: EEGDash diagnostic addition

Original source: [10.18112/openneuro.ds005048.v1.0.1](https://openneuro.org/datasets/ds005048/versions/1.0.1); aliases Lahijanian2024 / OpenNeuro ds005048 / EEGDash on005048, EEGDash `on005048`. Data licence CC0-1.0. Lahijanian et al.(2024), DOI10.1038/s41598-024-63727-z. Source revision: OpenNeuro ds005048 v1.0.1, Git 165a4d407983e5d7d42441ecc007caf6c98d3fad. Participant diagnosis classification during original40Hz auditory stimulation; Normal/MCI/AD, mild+moderate AD merged, unknown-group participants excluded. All complete4second windows within40second Stimulus events, rest excluded. Native250Hz float32 FDT numbers cast to float64; inferred microvolt format convention, no extra DSP. Distributed data already preprocessed; native history/reference/geometry and BIDS differences retained. See [clinical plan](eegdash-diagnosis-plan.md) and the source/manifest hashes in the prepared folder.

### ParkinsonsRestIowa: EEGDash diagnostic addition

Original source: [10.18112/openneuro.ds004584.v1.0.0](https://openneuro.org/datasets/ds004584/versions/1.0.0); aliases Singh et al./Iowa resting eyes-open / OpenNeuro ds004584, EEGDash `on004584`. Data licence CC0-1.0. Singh et al., DOI10.1101/2022.07.26.22278079. Source revision: OpenNeuro ds004584 v1.0.0, Git 261510fd9780d738a77fee52b906b3d56b69b74e. PD/control diagnostic groups from original participant GROUP; full source Rest recordings,4second windows at500Hz, no added DSP. Exact named sensor intersection across149source layouts; Resp and nonshared electrodes excluded explicitly. Native float32 FDT values castfloat64, interpreted as microvolts by EEGLAB convention; BIDS unit/type fields n/a. Source cohort related to existing Iowa interval-timing tasks, distinct rest recordings, not an independent participant study. See [clinical plan](eegdash-diagnosis-plan.md) and the source/manifest hashes in the prepared folder.

### ParkinsonsRestUCSD: EEGDash diagnostic addition

Original source: [10.18112/openneuro.ds002778.v1.0.5](https://openneuro.org/datasets/ds002778/versions/1.0.5); aliases UCSD / OpenNeuro ds002778 / EEGDash on002778, EEGDash `on002778`. Data licence CC0-1.0. Jackson et al.2019;10.1523/ENEURO.0151-19.2019; also Swann2015 and George2013 as requested in source README. Source revision: OpenNeuro ds002778 v1.0.5, Git 2890cbd8da62179735aae536a520008154630dd6. Clinically diagnosed PD OFF medication versus controls. Complete non-overlapping4s rest windows, native512Hz,32named scalp channels before flat review. ON medication sessions excluded to keep one acquisition condition and avoid mixing raw with2processed substitutions. Float64 calibrated microvolts; no new DSP. Original README explicitly discourages diagnostic ML on this31person cohort because of small test-group size and clinical heterogeneity; requests pre-publication author contact. User explicitly authorised inclusion9November2026. Benchmark preparation is not evidence of clinical diagnostic validity. See [clinical plan](eegdash-diagnosis-plan.md) and the source/manifest hashes in the prepared folder.
