# OpenEEGBench coverage

Reviewed 4 November 2026 against the [configured dataset catalogue](https://github.com/braindecode/OpenEEGBench/blob/main/open_eeg_bench/default_configs/datasets.py).
OpenEEGBench currently configures twelve datasets. Six have been prepared locally;
the remaining entries are overlapping source data, excluded, or require a different
access model. This assessment does not mean all prepared datasets are cleared for
public redistribution.

## Prepared datasets

| OpenEEGBench dataset | EEGBench name | Notes |
|---|---|---|
| Arithmetic (Zyma 2019) | MentalArithmetic | Same original PhysioNet EEGmat collection as the removed EEGMAT alternative preparation. |
| BCI Competition IV 2a | ImaginedHandFeetTongue | Four imagined movements. CC BY-ND 4.0 source terms require review before sharing the processed signals. |
| BCI Competition 2020-3 | ImaginedCommands | Five imagined spoken commands; original run-based split intentionally shares subjects. |
| CHB-MIT | ChildhoodSeizures | Seizure/non-seizure classification. |
| FACED | VideoEmotions | Eight observed emotion classes; Neutral is absent from the pinned upstream preparation. Original access terms remain a release-review item. |
| ISRUC-Sleep | ClinicalSleepStages | Five sleep stages, cohort I. Explicit redistribution permission remains unverified. |

Final `.ts` files and metadata sidecars are under `D:/Data/EEG/<EEGBench name>/`.
See [datasets](docs/datasets.md), [preparation details](docs/openeegbench-local-preparations.md)
and the [earlier source audit](docs/openeegbench-review.md) for revisions, dimensions,
validation and licence evidence. Redundant intermediate folders
`.openeegbench-final-preparation` and `.openeegbench-facet-preparation` were deleted
after validating the final exports; their paths in earlier instructions describe
reproducible preparation locations, not required runtime dependencies.

## Remaining configured datasets

| Dataset | Classification task / status | Decision |
|---|---|---|
| PhysioNet MI | Four-class motor imagery | Same EEG Motor Movement/Imagery Database collection already underlying FeetHands, ImaginedFeetHands, OpenCloseFist and ImaginedOpenCloseFist. A four-class preparation could be useful, but would not add a distinct recording collection. Exact selected cases need comparison before claiming identical arrays. |
| MDD (Mumtaz 2016) | Depression/control | Removed after verified identical signals crossed the pinned train/test split. Reconsider only after a corrected source release and renewed validation. |
| SEED-V | Five-class emotion recognition | Not downloaded; excluded under the user's redistribution constraint. |
| SEED-VIG | Continuous vigilance/PERCLOS prediction | Regression in the upstream configuration, outside the present classification archive. Binning targets would introduce an additional task definition and would still require source-terms review. |
| TUAB | Normal/abnormal clinical EEG | Substantial remaining classification candidate for authorised local use or a download-at-use workflow. Not cleared for inclusion in a redistributed signal archive. |
| TUEV | Six-class EEG event classification | Substantial remaining classification candidate for authorised local use or a download-at-use workflow. From the wider TUH source family; recording overlap with other TUH subsets must be audited rather than assumed absent. |

The [Temple subscriber agreement](https://isip.piconepress.com/projects/nedc/forms/tuh_eeg.pdf)
prohibits releasing the data to third parties or redistributing it. Availability of
a derivative on Hugging Face does not establish permission to republish it.
The OpenEEGBench software licence does not license the underlying EEG datasets.
The [MDD diagnostic report](docs/issues/mdd-duplicate-windows.md) retains evidence
for that exclusion.

## Remaining opportunities

### Local-use candidates with restricted or unresolved redistribution

Rechecked 5 November 2026. The remaining new classification candidates are
**TUAB, TUEV and SEED-V**. SEED-VIG is accessible through a similar research
application but is a regression task. Availability is conditional on the source
provider's approval; this review does not establish that we already hold access.
No restricted EEG signals were downloaded during this review.

| Dataset | Task | OpenEEGBench HF ID | Access and publication status |
|---|---|---|---|
| TUAB | Two classes: normal versus abnormal clinical EEG | `braindecode/tuab` | Temple subscriber application and credentials. Original agreement prohibits third-party release/redistribution. Suitable for authorised local evaluation, not our public signal archive. |
| TUEV | Six event classes: spike/sharp wave, generalized periodic epileptiform discharges, periodic lateralized epileptiform discharges, eye movement, artifact and background | `braindecode/tuev` | Same Temple access model and redistribution prohibition. Audit recording overlap with TUAB and other TUH subsets. |
| SEED-V | Five emotions: happiness, sadness, neutrality, fear and disgust | `braindecode/seed-v` | Original institutional-email application and uploaded licence agreement; provider reviews before issuing download credentials. Not cleared for public redistribution. Still not downloaded under the earlier instruction. |
| SEED-VIG | Continuous vigilance/PERCLOS prediction | `braindecode/seed-vig` | Same SEED application route. Regression upstream; a classification version would require an explicitly chosen discretisation. |

Pinned revisions from the current upstream configuration:

- TUAB: `7afcc5a00b50cac0f7e6e7f36928f7ccd8b91744`.
- TUEV: `a16d2dcaf354a4c1fa1d31e1e591294802939868`.
- SEED-V: `b3498f4b045ade3093ecc646e2162057309479d3`.
- SEED-VIG: `896f1ad81375dc1aaf53f6e73d9d0c829be7bb40`.

Sources: [OpenEEGBench configurations](https://github.com/braindecode/OpenEEGBench/blob/main/open_eeg_bench/default_configs/datasets.py),
[Temple tasks and access instructions](https://isip.piconepress.com/projects/nedc/html/tuh_eeg/),
[Temple agreement, conditions on page 2](https://isip.piconepress.com/projects/nedc/forms/tuh_eeg.pdf),
[SEED application](https://bcmi.sjtu.edu.cn/ApplicationForm/apply_form/),
[SEED download procedure](https://bcmi.sjtu.edu.cn/home/seed/downloads.html),
[SEED-V task](https://bcmi.sjtu.edu.cn/home/seed/seed-v.html),
[SEED-VIG continuous targets](https://bcmi.sjtu.edu.cn/home/seed/seed-vig.html).

Our already-prepared ImaginedHandFeetTongue (BCI IV 2a), ClinicalSleepStages
(ISRUC) and VideoEmotions (FACED) also retain their existing redistribution
review notes; they are not additional unassimilated sources. MDD remains
excluded for duplicate signals, independently of its licence.

Under the current aim of adding distinct classification recording collections
with an acceptable redistribution basis, no further ready-to-admit dataset was
identified in this twelve-entry catalogue. TUAB and TUEV merit separate access and
licence work if local-only evaluation is wanted. PhysioNet offers an optional
four-class view of existing source data. Recovering FACED's missing Neutral cases
from an original source could improve VideoEmotions, but would be a new conversion
requiring validation, not an additional independent dataset.

No datasets were downloaded or uploaded by this coverage review.
