# AdaBrain-Bench: source mapping to our archive

Reviewed 5 November 2026, after the four [cached MOABB conversions](docs/open-moabb-conversions.md).
Our registry has **60** prepared problems and `eeg.txt` selects **56**.
This review fetched documentation/configuration/code and source-host metadata only;
no additional EEG recordings were downloaded.

Source repository: [Jamine-W/AdaBrain-Bench](https://github.com/Jamine-W/AdaBrain-Bench),
pinned to [`c29be9291b927b037325640137bf0871acc04f57`](https://github.com/Jamine-W/AdaBrain-Bench/tree/c29be9291b927b037325640137bf0871acc04f57).
Its [dataset guide](https://github.com/Jamine-W/AdaBrain-Bench/blob/c29be9291b927b037325640137bf0871acc04f57/DATASETS.md)
identifies 13 entries. The preprocessing directory was checked as well as the README.
The [machine-readable mapping](docs/adabrain-source-mapping.json) preserves all
13 entries, code hashes, source-match categories and task types.

**Two sources match our selected collection**: EEGMAT and BCI-IV-2A. A third,
Sleep-EDF, matches the origin of our historical **Sleep** entry, which remains
outside `eeg.txt`. Thus **10 source entries are new to our complete registry**,
or 11 absent from the selected list if Sleep-EDF is included. This is not a claim
of ten independent recording cohorts: TUAB/TUEV share the TUH parent corpus and
need recording-level overlap checks. Shared source origin does not imply identical
cases, preprocessing or benchmark splits.

## Complete mapping

| AdaBrain name | Original source / identifier | Task | Our problem / relationship |
|---|---|---|---|
| EEGMAT | [PhysioNet eegmat 1.0.0](https://physionet.org/content/eegmat/1.0.0/), Zyma et al. | Rest versus mental arithmetic | **MentalArithmetic**; same original recordings, different extraction |
| BCI-IV-2A | [BNCI 001-2014 / BCI Competition IV 2a](https://bnci-horizon-2020.eu/database/data-sets) | Four imagined movement classes | **ImaginedHandFeetTongue**; same collection, different processing/protocol |
| Sleep-EDF | [PhysioNet sleep-edfx 1.0.0, sleep-cassette](https://physionet.org/content/sleep-edfx/1.0.0/) | Five sleep stages | Historical **Sleep** source; not selected. Exact record subset/epoch equivalence is unresolved |
| SEED | [SJTU SEED](https://bcmi.sjtu.edu.cn/~seed/seed.html) | Three emotion classes | New source; not FACED / VideoEmotions |
| SEED-IV | [SJTU SEED-IV](https://bcmi.sjtu.edu.cn/~seed/seed-iv.html) | Four emotion classes | New recordings within the SEED family; not a renamed SEED view |
| SEED-VIG | [SJTU SEED-VIG](https://bcmi.sjtu.edu.cn/~seed/seed-vig.html) | Continuous vigilance / PERCLOS regression | New source and non-classification target; not SEED-V or NBackAudioCondition |
| SHU | [Figshare 19228725 v3](https://doi.org/10.6084/m9.figshare.19228725.v3) | Left/right hand imagination, 25 participants × five sessions | New source; not Weibo2014 / ImaginedLeftRightHand |
| Things-EEG | [THINGS-EEG2-style raw release linked by AdaBrain](https://github.com/Jamine-W/AdaBrain-Bench/blob/c29be9291b927b037325640137bf0871acc04f57/preprocessing/Things-EEG/data_process.py) | Image/EEG retrieval | New source; not FaceDetection or MatchWords. Exact Google Drive file version needs pinning |
| TUEV | [TUH EEG Events, v2.0.1](https://isip.piconepress.com/projects/nedc/html/tuh_eeg/) | Six EEG event classes | New source entry; not CHB-MIT / ChildhoodSeizures or Bonn / EpilepticSeizures |
| TUAB | [TUH Abnormal EEG, v3.0.1](https://isip.piconepress.com/projects/nedc/html/tuh_eeg/) | Abnormal versus normal | New source entry; shares TUH parent with TUEV; file identity comparison needed |
| Siena | [PhysioNet siena-scalp-eeg 1.0.0](https://physionet.org/content/siena-scalp-eeg/1.0.0/) | Seizure versus non-seizure | New adult seizure collection; distinct from ChildhoodSeizures / CHB-MIT |
| HMC | [PhysioNet hmc-sleep-staging 1.1](https://physionet.org/content/hmc-sleep-staging/1.1/) | Five sleep stages | New source; not ISRUC / ClinicalSleepStages or Sleep-EDF |
| SHHS | [NTU mirror, DOI 10.21979/N9/EAMYFO](https://doi.org/10.21979/N9/EAMYFO), Sleep Heart Health Study | Five sleep stages | New source; not HMC, ISRUC or Sleep-EDF. Mirror membership/version and original access terms need checking |

## The three overlapping origins are different benchmark views

- **EEGMAT:** their [adapter](https://github.com/Jamine-W/AdaBrain-Bench/blob/c29be9291b927b037325640137bf0871acc04f57/preprocessing/EEGMAT/data_process.py)
  takes the last minute of rest and first minute of arithmetic, using four-second
  epochs, 19 channels and native frequency, with filtering. Our MentalArithmetic
  has 19 × 1000 samples at 200 Hz and a separately documented split. Do not add
  EEGMAT as another independent recording collection.
- **BCI IV 2a:** their [adapter](https://github.com/Jamine-W/AdaBrain-Bench/blob/c29be9291b927b037325640137bf0871acc04f57/preprocessing/BCI-IV-2A/data_process.py)
  crops four seconds at 250 Hz and filters. Our prepared version is 22 × 800 at
  200 Hz. The checked script literally loops over `range(1)`, processing only
  participant 1, although the guide describes all nine: code defaults alone do
  not establish the leaderboard's actual subject coverage. Its T/E and subsequent
  JSON splitting also differ from our prepared train/test protocol.
- **Sleep-EDF:** their [adapter](https://github.com/Jamine-W/AdaBrain-Bench/blob/c29be9291b927b037325640137bf0871acc04f57/preprocessing/Sleep-EDF/data_process.py)
  uses Fpz-Cz **and** Pz-Oz and sleep annotations. Our retired Sleep is a
  single-channel TF-C-derived distribution with 178 points; original epoch/record
  correspondence is not fully established. It is a source-family match, not an
  exact case match. Removing Sleep from the selection did not remove its provenance.

The four new problems RestingEyeState, GameTargets, CodedFlickerTargets and
ImaginedHandTraining have no direct source match among AdaBrain's 13 entries.

## Useful additions and restrictions

**SHU** is the most compact clearly identified new classification candidate here.
The [original version-3 Figshare metadata](https://api.figshare.com/v2/articles/19228725/versions/3)
declares **CC BY 4.0**, with **2,227,787,569 bytes** of advertised files. It documents
100 trials per session, five sessions per participant. However, its description
requires contacting the author for ZIP passwords. An open data licence does not
remove that access step; no email has been sent.

**HMC** and **Siena** are also original-host-confirmed **CC BY 4.0** data releases.
HMC 1.1 advertises a 12.9 GB ZIP / 15.7 GB uncompressed; Siena 1.0.0 advertises
13.0 GB / 20.3 GB. These are source sizes, not `.ts` sizes. They add new recording
collections but require substantially more storage than the compact MOABB queue.
See their original host links in the table for the data terms and versioned DOIs.

SEED-family access/redistribution terms, TUH agreements and the particular SHHS
mirror's rights require separate checks. AdaBrain's **MIT code licence does not
license any of these data**. SEED-VIG is regression and Things-EEG is retrieval;
neither becomes one of our classification problems without a separately defined
and justified target/split. No SEED-V data were downloaded.

## Reuse the source identities, not unchecked preprocessing

Their cross-subject, multi-subject and few-shot JSONs are evaluation settings,
not additional recording collections. A reproduction would need their actual
JSON memberships and processed-file version; our arrays cannot reproduce their
leaderboard simply by renaming datasets.

For example, the checked Siena code marks a fixed window positive when a seizure
**boundary** lies strictly inside it. A window wholly inside a long seizure can
therefore be incorrectly marked negative. It also adds overlapping seizure-focused
windows, with an unguarded short final crop. An import should derive labels from
interval overlap, enforce complete windows and group recording intervals across
splits. SHU defines a resampling helper that is not called; the executed path
keeps the native 250 Hz. These are source-code observations, not a claim that the
published experiments used every checked default.

For an agent checking duplication, compare the accession/version and original
participant/session/recording names first, then event/crop definitions, sensors,
labels and split membership. See [our provenance index](docs/dataset-provenance.md).
The next requested repository review is [ETH-DISCO EEG-Bench](EEG-Bench.md).
