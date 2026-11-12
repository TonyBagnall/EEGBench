# Proposed problem taxonomy

Snapshot 12 November 2026, based on current `eeg.txt` and documented prediction targets. One primary category/subclass per selected problem. These assignments do not overwrite the existing Med/BCI/Psy domains or source sidecars. They are proposed editorial groupings, not newly verified acquisition facts.

**82 selected scalp EEG problems; 91 registered archive problems.** The study excludes FaceDetection, HandMovementDirection, MatchWords and MindReading (MEG), plus MotorImagery (ECoG), as confirmed by the user 10 November 2026. Blink, ButtonPress, EpilepticSeizures and Sleep remain excluded for the existing reasons. All registry entries and local files are retained. Planned downloads/pilots are not counted; problems may share studies or source recordings.

| Category | Selected scalp EEG problems |
|---|---:|
| Clinical and physiological states | 22 |
| Brain-computer interfaces | 51 |
| Cognitive and affective states | 6 |
| Behaviour and activity | 3 |
| Individual differences | 0 |
| **Total** | **82** |

*(Note: in `neuroverse.datasets.STUDY_TAXONOMY`, the two physiological eye-state tasks `EyesOpenShut` and `RestingEyeState` sit in `Cognitive` (`8` total) while the `20` clinical disorder, seizure, sleep, and symptom-screening tasks form `by_type("Clinical")` (`20` total), alongside `by_type("BCI")` (`54` total: `30` `MI`, `6` `ME`, `8` `ERP`, `6` `VEP`, `4` `Speech`).)*

The study has **30 strict scalp-EEG motor imagery** problems (`by_type("MI")`, adding `ImaginedFingers` / `Damm2026` to replace the excluded ECoG problem `MotorImagery`), **20 clinical scalp-EEG** problems (`by_type("Clinical")`, adding `MigraineRest`, `ParkinsonsWalking`, `PsychosisRestFirst`, `PsychosisRestSecond`, and `TBIAuditoryOddball`), and **6 executed / movement-intention motor tasks** (`by_type("ME")`: `ArmCoordination`, `ArmMovements`, `FeetHands`, `FingerMovements`, `MatchingPennies`, `OpenCloseFist`).

## Subclasses and complete assignment

| Category | Subclass | Problems | Names |
|---|---|---:|---|
| Clinical and physiological states | Medical diagnosis / clinical cohort | 17 | Alzheimers, AlzheimersAuditory, CovidSurvivors, FibroLiverpool, FibroUEA, LongIntervalTask, MigraineRest, ParkinsonsPedalling, ParkinsonsRest, ParkinsonsRestIowa, ParkinsonsRestUCSD, ParkinsonsWalking, PhotoStimulation, PsychosisRestFirst, PsychosisRestSecond, ShortIntervalTask, TBIAuditoryOddball |
| Clinical and physiological states | Seizure detection | 1 | ChildhoodSeizures |
| Clinical and physiological states | Sleep staging | 1 | ClinicalSleepStages |
| Clinical and physiological states | Physiological eye state | 2 | EyesOpenShut, RestingEyeState |
| Clinical and physiological states | Symptom screening (not diagnosis) | 1 | ObsessiveCompulsiveSymptoms |
| Brain-computer interfaces | ERP / P300 target detection | 6 | ALSAttention, GameTargets, SpellerFlashes, SymbolAttention, VisualSubjects, WalkingTargets |
| Brain-computer interfaces | Motor execution | 5 | ArmCoordination, ArmMovements, FeetHands, MatchingPennies, OpenCloseFist |
| Brain-computer interfaces | Code-modulated VEP | 2 | CodedFlickerTargets, CodedSymbols |
| Brain-computer interfaces | SSVEP | 4 | FlickerAttention, FlickerSymbols, FlickerTargets, WirelessFlicker |
| Brain-computer interfaces | Motor imagery | 30 | ImaginedAnkleRest, ImaginedArmMovements, ImaginedArmTasks, ImaginedFeetHands, ImaginedFingers, ImaginedGrasps, ImaginedGripForce, ImaginedHandFeetTongue, ImaginedHandFootActions, ImaginedHandGestures, ImaginedHandMusicTempo, ImaginedHandPupils, ImaginedHandSides, ImaginedHandTraining, ImaginedHandsCrossSession, ImaginedHandsEmbodiment, ImaginedHandsFeedback, ImaginedHandsFeet, ImaginedHandsHaptics, ImaginedHandsOnline, ImaginedHandsPhysiology, ImaginedHandsRobot, ImaginedHandsStroke, ImaginedLeftRightHand, ImaginedLeftRightHandRest, ImaginedOpenCloseFist, ImaginedRightHandFeet, ImaginedRightHandFeetRest, LowCost, SitStand |
| Brain-computer interfaces | Imagined speech | 2 | ImaginedCommands, InnerSpeech |
| Brain-computer interfaces | Slow cortical potential self-regulation | 2 | SelfRegulationSCP1, SelfRegulationSCP2 |
| Cognitive and affective states | Workload / joint task condition | 2 | MentalArithmetic, NBackAudioCondition |
| Cognitive and affective states | Memory / recognition performance | 1 | SongFamiliarity |
| Cognitive and affective states | Emotion | 1 | VideoEmotions |
| Cognitive and affective states | Visual imagery | 1 | VisualSpeech |
| Cognitive and affective states | Semantic processing | 1 | WordRelatedness |
| Behaviour and activity | Movement intention | 2 | FeedbackButton, FingerMovements |
| Behaviour and activity | Overt speech | 1 | PronouncedSpeech |

Subclasses not represented: anaesthesia, consciousness, dedicated error-related-potential decoding, fatigue, stress, dedicated vigilance/attention-state classification, generic human activity recognition, subject identification/authentication and demographic prediction. This does not mean every task has been audited for every possible secondary interpretation. P300 attention targets are counted under BCI rather than counted again as cognitive attention.

## Assignment decisions

Use the **prediction target**, with BCI motor execution following the supplied taxonomy. Clinical cohorts performing a motor task stay clinical when disease/cohort is the label. Motor preparation versus future movement belongs under behaviour/movement intention. Eye-open/closed is a physiological state rather than assumed vigilance. Symptom screening is separated from clinical diagnosis.

ERP is a cross-cutting signal/paradigm family:6 BCI P300 tasks plus1 N400 semantic EEG task (WordRelatedness) gives **7 explicitly documented ERP problems**. Do not turn all7 into P300, or count them twice in the primary-category total. MatchWords is excluded MEG and is not counted.

The previous P300 review missed existing GameTargets (BrainForm/RomaniBF2025ERP) and WalkingTargets. Its baseline4 was incorrect; the correct current baseline is6P300/7explicit ERP. RomaniBF2025ERP must also be removed from proposed new additions because it is already GameTargets.

- **ObsessiveCompulsiveSymptoms:** OCI-threshold symptom grouping in students; not clinical OCD diagnosis.
- **CovidSurvivors:** COVID-survivor versus close-contact cohort membership; not current disease diagnosis.
- **SitStand:** Mixed imagined transitions and seated/standing idle classes; included in the existing30 MI tally.
- **MatchingPennies:** Executed hand raising while imagining the opposite hand; primary assignment motor execution, secondary motor imagery.
- **VisualSpeech:** Visualised circle direction, not spoken or imagined speech.
- **SongFamiliarity:** Correct versus incorrect song identification, not simply familiar versus unfamiliar.
- **NBackAudioCondition:** Joint3 N-back levels x4 audio codes; not a pure workload contrast.
- **WordRelatedness:** ERP/N400 semantic task; ERP is also a cross-cutting response/paradigm tag.
- **FeedbackButton:** Press/no-press target in prompt-period windows ending before press; original acquisition provenance unresolved.
- **ALSAttention:** Attended versus unattended flashes in ALS participants; not ALS diagnosis.
- **ParkinsonsPedalling:** PD versus control during pedalling; diagnosis target, not activity classification.
- **ParkinsonsWalking:** PD versus control during active treadmill walking; diagnosis target, not gait activity classification.
- **PsychosisRestFirst / PsychosisRestSecond:** Disjoint first-episode psychosis versus healthy control cohorts at eyes-open rest (`ds003944` and `ds003947`).
- **TBIAuditoryOddball:** 3-class TBI diagnosis (control, sub-acute mild TBI, chronic TBI) during Session 1 auditory oddball deviant tones (`ds003522`); diagnosis target, not stimulus-type classification.
- **MigraineRest:** Unmedicated interictal migraineurs versus age- and gender-matched controls during central-cross fixation (`Chamanzar2020`).
- **LongIntervalTask:** PD versus control in interval timing; diagnosis target, not timing-task identity.
- **ShortIntervalTask:** PD versus control in interval timing; diagnosis target, not timing-task identity.

Sources: [dataset descriptions](datasets.md), [provenance](dataset-provenance.md), [BrainForm and other conversions](open-moabb-conversions.md), [selected list](../eeg.txt), [registry](../neuroverse/datasets.py). Machine-readable assignments: [problem-taxonomy.json](problem-taxonomy.json).

## Excluded modalities retained in the archive

- **FaceDetection:** MEG; excluded from this study, data and registry retained.
- **HandMovementDirection:** MEG; excluded from this study, data and registry retained.
- **MatchWords:** MEG; excluded from this study, data and registry retained.
- **MindReading:** MEG; excluded from this study, data and registry retained.
- **MotorImagery:** ECoG; excluded from this study, data and registry retained.
