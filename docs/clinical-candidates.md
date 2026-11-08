# Clinical EEG classification candidates in EEGDash

A survey of EEGDash for datasets that could become subject-level clinical
classification problems (patients vs controls, or between diagnoses), compiled
5 November 2026 in the aeon-neuro project and moved here on 6 November 2026.

> **Handoff note for the agent working in this repository.** This is a list
> of candidate problems, not prepared datasets. Nothing here has been
> downloaded or converted. Before preparing any of them:
> - check this table against `dataset-provenance.md` and `additional-datasets.md`;
> - define the classes from the original paper;
> - run the usual source lock, metadata completeness and signal scale audits.
>
> Rows marked **In EEGBench** were matched to existing problems on 6 November
> 2026. The other statuses come from the survey and are unchecked.

## Method

- EEGDash's registry API (`data.eegdash.org`) lists 953 datasets. Of these, 125
  are EEG and carry a pathology tag other than Healthy or Unknown. The tags come
  from EEGDash's LLM tagger, so they are a first pass, not ground truth.
- For each of the 125, I pulled every recording document. Each one has the
  subject's row from `participants.tsv`, plus channels, sampling rate, task and
  duration. Subject counts and group counts below are taken from those rows.
- The group columns, such as `Group`, `type` and `GROUP`, are the dataset's own.
  Where the codes are numeric (`0/1/2`), the meaning has to come from the paper
  or the dataset's code folder.
- Duplicates were removed where EEGDash holds both an OpenNeuro copy (`ds…`) and
  a NEMAR copy (`on…`) of the same data. Re-releases that are still listed are
  flagged below.
- Paper DOIs come from the dataset's own metadata (`how_to_acknowledge`,
  `ReferencesAndLinks`, README). "Paper to find" means none was given.
- The survey script and its output are in
  [`source-evidence/eegdash-clinical-survey/`](source-evidence/eegdash-clinical-survey/)
  (`survey.py`, `survey.json`). To rerun, first save the dataset list next to
  the script as `all_datasets.json` (8.9 MB), with
  `curl "https://data.eegdash.org/api/eegdash/datasets?limit=1000"`.
  Then run `python survey.py <that folder>`.

Classes still need defining from each original paper: which contrast it
studied, who it excluded, and how it handled medication and sessions.

## Tier A: patients vs controls, at least 40 subjects, labels in `participants.tsv`

| Dataset | Condition | Subjects (groups) | Recording | Ch / Hz | Paper | Notes |
|---|---|---|---|---|---|---|
| on008768 | Parkinson's | 312 (PD 202, Control 110) | Rest, eyes open, about 3 min | 63–66 / 500 | Paper to find | The largest PD set. 358 recordings, as some subjects have more than one session. Probably the same lab as on004584 (Iowa), so check for overlap. |
| on004584 | Parkinson's | 149 (PD 100, Control 49) | Rest, eyes open, 2 min | 64 / 500 | [medRxiv 10.1101/2022.07.26.22278079](https://doi.org/10.1101/2022.07.26.22278079) | Same cohort as on004574, on004579 and on004580. |
| on004574 | Parkinson's | 146 (PD 98, Control 48) | Cross-modal oddball | 63–66 / 500 | As on004584 | Same cohort. |
| on004580 | Parkinson's | 147 (PD 99, Control 48) | Simon conflict task | 63–66 / 500 | As on004584 | Same cohort. |
| on004579 | Parkinson's | 139 (PD 94, Control 45) | Interval timing task | 63–66 / 500 | As on004584 | **In EEGBench:** the source of LongIntervalTask and ShortIntervalTask (`dataset-provenance.md`). It is also NeuralBench's Parkinson's dataset, "Singh2021" (`singh2021-source-overlap.json`). |
| on007526 | Parkinson's | 144 (PD 116, HC 28) | Rest and walking | 65 / 250 | [Mov. Disord. 10.1002/mds.70348](https://doi.org/10.1002/mds.70348) | Unbalanced. The walking recordings add movement artefacts. |
| on003490 | Parkinson's | 50 (PD 25, CTL 25) | Rest, plus a 3-stimulus oddball | 67 / 500 | Paper to find (Cavanagh lab) | PD recorded ON and OFF medication in two sessions, so the contrast needs choosing (OFF vs control is usual). |
| on003944 | First-episode psychosis | 82 (Psychosis 50, Control 32) | Rest, 5 min | 64 / 1000 | Paper to find | Includes 10 subjects from on003947. Phenotype folder has BPRS and other scales. |
| on003947 | First-episode psychosis | 61 (Psychosis 31, Control 30) | Rest | 64 / 1000 | Paper to find | Second sample. Drop the 10 subjects shared with on003944, or merge the two. |
| nm000114 | Depression (MDD) | 64 IDs (MDD 34, HS 30, by ID prefix) | Rest EC and EO, auditory P300 | 19–22 / 256 | [Mumtaz et al. 2016, BSPC 10.1016/j.bspc.2016.07.006](https://doi.org/10.1016/j.bspc.2016.07.006) | **In EEGBench**, via OpenEEGBench's `mdd_mumtaz2016` (`dataset-provenance.md`). The README says 34 participants (19 HC, 15 MDD), which contradicts the 64 IDs. NeuralBench uses 64. The duplicate windows across healthy-control IDs reported in `issues/mdd-duplicate-windows.md` may be related. |
| on004595 | Hazardous drinking (AUD) | 53 (AUD 27, CTRL 26) | 3-armed bandit with alcohol cues | 66 / 500 | Campbell et al. (Cavanagh lab), DOI to find | on005907 is a re-release of the same data. Task-based. |
| on003522 | Mild TBI | 96 (codes 0: 44, 1: 27, 2: 25) | 3-stimulus auditory oddball, plus rest | 64–65 / 500 | [Neuropsychologia 10.1016/j.neuropsychologia.2019.107125](https://doi.org/10.1016/j.neuropsychologia.2019.107125) | Control, sub-acute mTBI and chronic TBI; the code-to-group mapping needs confirming. Longitudinal with heavy attrition, so use session 1. |
| on005114 | Mild TBI | 91 (codes 0: 57, 1: 34) | DPX cognitive control task | 64–65 / 500 | [Brain Imaging Behav. 10.1007/s11682-019-00171-y](https://doi.org/10.1007/s11682-019-00171-y) | Same cohort as on003522 and on003523. |
| on003523 | Mild TBI | 91 (codes 0: 57, 1: 34) | Visual working memory task | 64–65 / 500 | [CABN 10.3758/s13415-018-0584-6](https://doi.org/10.3758/s13415-018-0584-6) | Same cohort. |
| on007181 | Zoster-associated neuralgia | 59 (ZAN 27, HC 32) | Overnight PSG, about 8 h | 24 / 1024 | Paper to find; code at [ellebai/zan-neuro](https://github.com/ellebai/zan-neuro) | Very long recordings, so it needs a segmenting decision. |
| on007605 | Post-COVID syndrome | 97 (with PCS 60, without 37) | Psychomotor vigilance task | 128 / 1000 | Paper to find | Both groups had COVID, so this isn't patients vs healthy. Also has a fatigue label. |
| on004504 | AD, FTD, control | 88 (A 36, F 23, C 29) | Rest, eyes closed | 19 / 500 | [Data 10.3390/data8060095](https://doi.org/10.3390/data8060095) | **In EEGBench** as Alzheimers. |
| on006036 | AD, FTD, control | 88 (same subjects) | Photic stimulation, eyes open | 19 / 500 | [Data 10.3390/data10050064](https://doi.org/10.3390/data10050064) | **In EEGBench** as PhotoStimulation. |
| on007823 | COVID-19 survivors | 169 (Covid 86, Control 83) | Rest | 22 / 200 | [Clin. Neurophysiol. Pract. 10.1016/j.cnp.2026.02.007](https://doi.org/10.1016/j.cnp.2026.02.007) | Being run in tsml-eval as CovidSurvivors (not found in this repository's docs). on008082 is a later release with 173 subjects. Also has symptom and severity labels. |

## Prognosis rather than diagnosis

| Dataset | Condition | Subjects (labels) | Recording | Ch / Hz | Paper | Notes |
|---|---|---|---|---|---|---|
| nm000289 | Coma after cardiac arrest (I-CARE) | 607 (outcome Good 225, Poor 382) | ICU EEG, hourly segments | 20–22 / 250–500 | [medRxiv 10.1101/2023.08.28.23294672](https://doi.org/10.1101/2023.08.28.23294672) | The PhysioNet 2023 Challenge data, so it has published comparisons. Licence is CC-BY-NC-SA. Large. |
| on007020 | Parkinson's mortality | 94 (living 72, deceased 22) | Rest, eyes open | 63–64 / 500 | Paper to find | All subjects are PD patients; the label is later survival. |

## Tier B: smaller, or the labels need work

| Dataset | Condition | Subjects (groups) | Recording | Ch / Hz | Paper | Notes |
|---|---|---|---|---|---|---|
| on002778 | Parkinson's | 31 (PD 15, HC 16, by ID prefix) | Rest | 41 / 512 | [eNeuro 10.1523/ENEURO.0151-19.2019](https://doi.org/10.1523/ENEURO.0151-19.2019) | UCSD. PD recorded ON and OFF medication. |
| on003506 | Parkinson's | 56 (PD 28, CTL 28) | Reinforcement learning task | 67 / 500 | Cavanagh lab, several papers | Medication ON/OFF sessions. |
| on003509 | Parkinson's | 56 (PD 28, CTL 28) | Simon conflict task | 67 / 500 | Cavanagh lab, several papers | Same cohort as on003506. |
| nm000349 | Migraine (interictal) | 39 (migraine 18, control 21) | Rest, SSVEP, SSAEP | 144 / 512 | [Brain Comms 10.1093/braincomms/fcab061](https://doi.org/10.1093/braincomms/fcab061) | `participants.tsv` records which subjects the paper excluded and why, which makes it easy to follow the paper. Very high density. |
| on006921 | Phantom limb pain | 38 (amputee 19, control 19; pain 13, no pain 25) | Rest EC and EO | 64–128 / 2400 | [Zenodo 10.5281/zenodo.10797803](https://doi.org/10.5281/zenodo.10797803) | Two possible contrasts: amputee vs control, or pain vs no pain. |
| on004367 | Schizophrenia | 40 (Patient 17, Control 23) | Random-dot motion task | 68 / 1200 | Paper to find | on004368 is the preprocessed version (3 s epochs, 128 Hz). |
| on004000 | Schizophrenia | 43 (P 19, HC 24) | Ultimatum game | 132 / 2048 | Paper to find | |
| on003478 | Depression | 122 | Rest | 66–67 / 500 | Paper to find; on003474 uses the same subjects ([10.1162/cpsy_a_00024](https://doi.org/10.1162/cpsy_a_00024)) | Selected for high vs low Beck Depression Inventory scores, but the BDI labels are in a spreadsheet, not `participants.tsv`. Only 32 have a clinical interview. |
| on005048 | AD and MCI | 35 (Normal 10, MCI 6, Mild AD 16, Moderate AD 1, unknown 2) | 40 Hz auditory stimulation | 19 / 250 | [Sci. Rep. 10.1038/s41598-024-63727-z](https://doi.org/10.1038/s41598-024-63727-z) | Small and unbalanced. |
| on004019 | Obesity (preteens) | 62 (obese 28, not obese 33) | Arithmetic task | 128 / 500 | Paper to find | Also has a high vs low maths-skill label. |
| on004151 | Obesity (preteens) | 57 (obese 27, not obese 30) | Stop-signal task | 128 / 500 | [Int. J. Psychophysiol. 10.1016/j.ijpsycho.2021.04.003](https://doi.org/10.1016/j.ijpsycho.2021.04.003) | |
| nm000309 | Chronic MCA stroke | 18 (stroke 9, healthy 9, by subject number) | Motor imagery | 59 / 1000 | [Zenodo 10.5281/zenodo.19599465](https://doi.org/10.5281/zenodo.19599465) | Small. The groups are only in the README. |

## Not suitable as diagnosis problems

- **BCI datasets recorded in patients.** Stroke and spinal cord injury motor
  imagery (nm000144, nm000149, nm000158, nm000270, nm000306, nm000312, nm000347
  and others), ALS P300 (BigP3BCI: nm000187, nm000197, nm000248, nm000303 and
  others), and autism P300 (nm000210). These have no control group. They would
  make BCI problems, and several are also in MOABB.
- **Seizure detection.** CHB-MIT (nm000110), Siena (nm000385), SeizeIT2
  (on005873, 2-channel wearable) and the pediatric HFO set (on003555). The labels
  are events within recordings, so these are segment-level problems from
  patients only.
- **Sleep.** ISRUC-Sleep (nm000111: subgroup I has 100 subjects with sleep
  disorders, subgroup III has 10 healthy) and the PhysioNet 2018 arousal set
  (nm000225). They suit sleep staging or arousal detection; the ISRUC
  control group is too small for diagnosis.
- **Healthy Brain Network** (on005505 to on005516, nm000103). Diagnoses aren't in
  `participants.tsv`; they need HBN's phenotype data, which requires a data use
  agreement. The challenge targets are continuous (p-factor and similar), so
  regression.
- **Animal data.** on004598 (rat LFP, AD model) and on006269 (Syngap1 rats).
- **Not a clinical contrast, or too small.**
  - Not a clinical contrast: on005296 (deaf vs hearing readers) and on006260
    (intervention arms, not diagnoses).
  - Too small: on004840 (9 burn patients), on007314 and on007315 (2 stroke
    patients), on007347 (5 cancer patients), on007720 (5 ALS patients) and the
    Neuroepo PD trials (on003194, on003195, on007864, on007865; treatment arms
    with no controls).

## Suggested first picks

1. **Parkinson's, resting state.** Use on008768, or on004584 if the two
   overlap. It's large, the labels are clear, and the protocol is simple. The
   same cohort's task recordings (on004574, on004580) give related problems.
   That cohort probably shares subjects with ds004579, the source of
   LongIntervalTask and ShortIntervalTask. Check the subject overlap before
   mixing these problems in an analysis.
2. **First-episode psychosis, resting state.** Use on003944 plus on003947, with
   the 10 shared subjects removed from one.
3. **Mild TBI.** Use on003522, session 1, after confirming the group codes. Its
   three groups would make a 3-class problem.
4. **I-CARE outcome** (nm000289). A large prognosis problem with published
   comparisons from the PhysioNet challenge. Check the non-commercial licence
   against the archive's terms.
5. **Migraine** (nm000349). Small, but the paper's exclusions are recorded in
   the data, so it's quick to follow the paper exactly.

## Caveats

- Counts are subjects that have EEG recordings in EEGDash. They can differ from
  the papers' counts after the papers' exclusions.
- The pathology tags are machine-generated. Datasets tagged Healthy or not
  tagged at all were not surveyed, so a few clinical datasets may be missing.
- Overlaps between datasets from the same lab (Iowa PD, Cavanagh's UNM studies)
  were inferred from READMEs and subject counts, not checked subject by subject.
- Nothing has been downloaded. The signal quality, units (volts vs microvolts)
  and flat channels still need checking for each pick.
