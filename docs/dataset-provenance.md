# Dataset provenance

This page traces all 30 EEGBench problems to their recording collections, source
names and publications. Benchmark dimensions and extraction details are taken from
Sections 2.1-2.3 and Table 1 of Rushbrooke, Sami, Middlehurst and Bagnall (2026),
[Time Series Machine Learning for Classifying Electroencephalograms](https://data.mlr.press/assets/pdf/v03-8.pdf)
(the root paper, `v03-8.pdf`), and checked against
[`eegbench/datasets.py`](../eegbench/datasets.py). External sources were checked on
3 November 2026. This is a source audit, not a verification of downloaded data files.

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
| [FingerMovements](#fingermovements) | BCI Competition II `IV` (Berlin) | Upcoming left/right keypress | Identified; dimensions conflict |
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
  verify the benchmark files before assuming these versions are interchangeable.
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
- Reconcile FingerMovements length/frequency, Sleep length, EpilepticSeizures
  frequency, FaceDetection channel/window selection, and the subject/trial counts
  flagged above against actual files and subject-index metadata.
- Audit the inherited splits before applying a blanket subject/session-disjoint
  guarantee: TF-C explicitly cannot guarantee recording-disjoint splits for
  Epilepsy, and the SCP source descriptions provide exceptions to the
  simpler recording-day interpretation. No metadata or evaluation code has been
  changed as part of this documentation audit.
