# ETH-DISCO EEG-Bench review

Reviewed 5 November 2026, after completing our four cached conversions and the
[AdaBrain-Bench source mapping](AdaBrain-Bench.md). This is the separately named
[ETH-DISCO/EEG-Bench](https://github.com/ETH-DISCO/EEG-Bench), not this repository.
No EEG recordings were fetched for either repository review.

Pinned source revision:
[`db78d893ead8d7ca847f6ae172c0f83d93e4fa2f`](https://github.com/ETH-DISCO/EEG-Bench/tree/db78d893ead8d7ca847f6ae172c0f83d93e4fa2f).
The README describes 25 datasets. The checked task definitions actually reference
**26 distinct adapters: 12 BCI and 14 clinical**, across 14 task classes. These are
not 26 independent studies: labels, tasks, source collections and cohorts have to
be distinguished.

Against our **67 selected / 71 registered problems**:

| Relationship | Adapters |
|---|---:|
| Source already represented in our selected archive | **11** |
| Probable original-source overlap: interval timing and oddball | **2** |
| Sleep-EDF parent-family relationship; exact overlap unresolved | **1** |
| No source match identified so far | **12** |

The 12 are a candidate pool, not a verified count of independent new recording
collections. Several clinical entries share participants, and TUH subsets may
share recordings. Our older unresolved source mappings also limit blanket
non-overlap claims. Full adapter names, pinned code URLs, source identities and
Hugging Face mirror revisions are in
[eth-eeg-bench-mapping.json](docs/eth-eeg-bench-mapping.json).

## BCI sources: aliases matter

| EEG-Bench adapter/name | Actual source | Our match / next action |
|---|---|---|
| Barachant2012 | **MOABB AlexMI**, Zenodo 806023 | **ImaginedRightHandFeet**. Their available rest class is another view of the same source |
| BCICompIV2a | BNCI2014_001 / Competition IV 2a | **ImaginedHandFeetTongue**; reducing to two classes does not create a new recording collection |
| BCICompIV2b | BNCI2014_004 / Competition IV 2b | **ImaginedHandSides** |
| PhysionetMI | PhysioNet eegmmidb | **FeetHands, ImaginedFeetHands, OpenCloseFist, ImaginedOpenCloseFist**; compare the original task/run selection |
| Weibo2014 | Harvard Dataverse 27306 / Weibo motor-imagination study | **ImaginedLeftRightHand**; wider class selections remain the same source |
| Zhou2016 | Zhou2016 motor imagination | **ImaginedHandsFeet** |
| Cho2017 | GigaDB 100295 / MOABB Cho2017 | New source candidate; original data terms need reconciliation with catalogue declarations |
| Faller2012 | **BNCI2015_001** | New source entry, already noted in MOABB survey; not a second dataset in addition to BNCI2015_001 |
| Scherer2015 | **BNCI2015_004** | New source entry; this adapter exposes right-hand/feet from the wider mental-task collection |
| Liu2022 | **MOABB Liu2024**, Figshare 21679035 v5 | **ImaginedHandsStroke**; the adapter's year/name is misleading |
| Schirrmeister2017 | High-Gamma Dataset | New source; **executed movement**, despite its placement in their MI tasks. Review known participant-14 sensor failure |
| Kaya2018 | Figshare collection 3917698 | New source; several paradigms/recording subsets. Left/right, right-hand/feet, four-limb and five-finger views are not four independent studies |

These identities were traced from actual imports and instantiated dataset classes,
not matched from filenames alone. For example,
[`liu2022_m.py`](https://github.com/ETH-DISCO/EEG-Bench/blob/db78d893ead8d7ca847f6ae172c0f83d93e4fa2f/eeg_bench/datasets/bci/liu2022_m.py)
imports `Liu2024`, while
[`barachant2012_m.py`](https://github.com/ETH-DISCO/EEG-Bench/blob/db78d893ead8d7ca847f6ae172c0f83d93e4fa2f/eeg_bench/datasets/bci/barachant2012_m.py)
imports `AlexMI`.

The task-level subject selections are often smaller than the source cohorts:
their left/right task requests only Cho participants 1â€“14, for example. The
custom Kaya loader differs from MOABB's narrower Kaya view, excludes Inter files
and handles HFREQ files specially. Recover paradigm, subject and session membership
and verify imagined versus executed movement before defining an archive problem.

## Clinical sources

Nine loaders use `jalauer/` Hugging Face mirrors. The data cards identify papers
and tasks but are secondary distributions; the public revision hashes are frozen
in our machine-readable mapping.

| Adapter / mirror | Recording task and label | Relationship / provenance note |
|---|---|---|
| Cavanagh2018a (`d001`) | Auditory oddball; PD/control | Possible shared original acquisition with ParkinsonsRest: author rest script loads *_ODDBALL.vhdr; exported sample overlap not established |
| Cavanagh2018b (`d002`) | Eyes-open/closed rest; PD/control | **ParkinsonsRest**; author import script crops rest from `*_ODDBALL.vhdr`, so original acquisitions may also underlie oddball derivatives |
| Albrecht2019 (`d004`) | Reinforcement learning/cognitive conflict; schizophrenia/control | No source match identified; not our Alzheimerâ€™s or fibromyalgia collections |
| Singh2018 (`d005`) | Modified Simon/cognitive control; PD/control | PDDys cohort, source files end `PDDys_CC.mat`; different task recordings |
| Brown2020 (`d007`) | Reinforcement learning; PD/control | PDDys cohort, source files end `PDDys_VV_withcueinfo.mat`; different task recordings |
| Gruendler2009 (`d008`) | Error-related activity and obsessive-compulsive symptoms | **ObsessiveCompulsiveSymptoms**; 35 nominal raw student recordings, high/low OCI symptoms,52 EEG after flat-sensor removal; 11 processed files deferred |
| Cavanagh2019 (`d009`) | Auditory oddball; mTBI/control | No source match identified |
| Singh2020 (`d011`) | Lower-limb pedalling; PD/control | **ParkinsonsPedalling**; different task from interval timing; cross-study participant identity unresolved |
| Singh2021 (`d014`) | 3 s / 7 s interval estimation; PD/control | **Strong probable overlap with ShortIntervalTask / LongIntervalTask**; see audit below |
| CHBMIT | CHB-MIT seizure annotations | **ChildhoodSeizures** source. Their loader recognises chb01/chb21 as the same person |
| SleepTelemetry | Sleep-EDF expanded 1.0.0 **sleep-telemetry** | Different branch from AdaBrain's sleep-cassette. Our historical Sleep subset is insufficiently resolved to certify recording non-overlap. Not ISRUC / ClinicalSleepStages |
| TUEGAbnormal | **TUAB v3.0.1** | Same source version named by AdaBrain TUAB; new to our archive |
| TUEGArtifact | **TUAR v3.0.1** | New source entry. Binary and multiclass artifact tasks reuse the same collection |
| TUEGEpilepsy | **TUEP v2.0.1** | New source entry; epilepsy diagnosis, not seizure-window detection or Bonn EpilepticSeizures |

The TUH versions are explicit in their download commands. TUAB, TUAR and TUEP
need the original TUH access arrangements and data terms; the software licence
does not authorize redistributing them. TUH parent-corpus membership also means
that individual recordings/patients must be compared across subsets.

## Interval-task overlap: do not assimilate as an independent study yet

Our ShortIntervalTask and LongIntervalTask originate from OpenNeuro **ds004579**.
Its [original-ID participant table](https://raw.githubusercontent.com/OpenNeuroDatasets/ds004579/4a2293c1223a497c6e49ed038405b5a900e67c61/participants.tsv)
retains IDs such as `PD1005` and `Control1025`. Comparing these with the pinned
Singh2021 mirror's file metadata finds **116 shared original recording IDs**:
129 BrainVision EEG files in the mirror versus 139 participants in ds004579.
Both descriptions use the intermixed 3-/7-second interval task.

This establishes strong cohort/task overlap, **not byte-identical signals**.
The mirror distributes BrainVision `.eeg`; OpenNeuro distributes converted
EEGLAB `.fdt/.set`. A raw-byte hash comparison therefore cannot establish signal
equality across these formats. No signal files were downloaded to resolve that.
The [machine-readable audit](docs/singh2021-source-overlap.json) preserves the
shared IDs, source revisions and limitations. Treat this as a probable shared
origin pending event/header/numerical comparison, rather than another independent
classification collection. Extra OFF-medication sessions might add recordings,
but they do not establish a separate study.

The Singh2021 mirror explicitly describes some ON/OFF person pairings as guesses.
Do not convert those session IDs into distinct participants or adopt guessed
pairings without original evidence. Conversely, the provided PD task's raw-ID
train/test memberships for Cavanagh2018a/b, Singh2018 and Brown2020 were checked:
no shared original ID crosses train/test across those four cohort-related adapters.
That limited check applies to ETH task configurations, not the new archive rest
split or every other task. It does not establish matching partitions across
these benchmarks.

## Preparation update

**Liu2024 is now prepared as [ImaginedHandsStroke](docs/imagined-hands-stroke-preparation.md)**,
with 1400/440 cases from 46 retained release IDs. Original source files were
checksum-verified, native trigger anomalies were audited, and all exported
cases passed validation. The priority list below records the earlier shortlist.

## Priority candidates: open data terms first, smaller sources next

1. **Liu2024**, despite the wrapper's Liu2022 name. The original
   [version-5 Figshare record](https://doi.org/10.6084/m9.figshare.21679035.v5)
   is *EEG datasets of stroke patients*, with **CC BY 4.0** and
   **2,340,877,001 bytes** advertised. MOABB describes 47 participants, 29 EEG
   channels at 500 Hz, 40 left/right trials per person. A four-second window
   would be about **0.872 GB** of float64 arrays before `.ts` expansion. Actual
   source timing, labels and sensor order still need native-file validation.
2. **Cavanagh2018b**, resting PD/control: approximately **2.089 GB** of current
   mirror files. This adds task/diagnostic diversity and is smaller than most
   of their other clinical mirrors.
3. **Singh2020**, lower-limb movement in PD: approximately **4.032 GB** of current
   mirror files, including ancillary material. Distinct from interval timing.
4. **Gruendler2009**, obsessive-compulsive symptoms: approximately **7.386 GB**
   of current mirror files. Check group/diagnosis semantics before choosing a name.

For the last three, the root **data `LICENSE.txt` files were read and contain
PDDL**, separately from bundled GPL analysis-software licences. Their cards
attribute PDDL to the original authors. This is stronger than a code-licence
assumption. The subsequent [PRED+CT preparation](docs/predct-preparation.md)
verified that the original catalogue explicitly grants PDDL to its contents.
ParkinsonsRest and ParkinsonsPedalling are now prepared; ObsessiveCompulsiveSymptoms is prepared from 35 nominal raw recordings; 11 processed files are deferred.
Sizes above sum current file-tree metadata at the pinned mirror revisions;
they are neither processed `.ts` sizes nor promises of eventual usable case counts.

Cho2017, Kaya2018 and High-Gamma remain useful larger candidates already present
in the [MOABB survey](docs/moabb-remaining-candidates.md). BNCI2015_001 and
BNCI2015_004 have **CC BY-NC-ND** declarations and sit behind the fully open queue.
Changing their names to Faller/Scherer does not remove those terms.

## Implementation differences to preserve when importing

- Clinical loaders often return whole variable-length recordings, or concatenate
  originally epoched arrays. Our fixed-length cases need explicit source-window
  definitions and original trial boundaries; do not treat flattened epoch joins
  as continuous acquisition.
- Their SleepTelemetry loader selects **two EEG derivations plus horizontal EOG**.
  Do not describe all three channels as EEG or confuse this with our excluded
  single-channel Sleep problem.
- Some conversion scaling requires review: Singh2020 uses `raw.get_data()*1e5`.
  Check original header calibration and physical units rather than copying this
  factor into a microvolt archive. The clinical adapters also supply long hardcoded
  channel lists; native header order must be checked before using those labels.
- Multiple targets such as age, sex, BDI, medication or symptom scores are alternate
  labels for the same recordings; some are regression. Task count is not new-data
  count. Likewise, reducing one MI source to several limb combinations changes
  the view, not the recording origin.
- Their GPL-3.0 repository licence covers software. Original data permissions,
  source versions, participant/session identity, auxiliary sensors and split units
  remain dataset-specific requirements.

No downloads, conversions or changes to our existing arrays resulted from this
review. The four preceding MOABB conversions are documented separately and passed
their full validation before this review began.

## Prepared PRED+CT additions

See [current PRED+CT preparations](docs/predct-preparation.md) for validated archive
names, native metadata and recording exclusions. The mapping JSON records only
completed additions; source overlap does not mean identical benchmark windows.
