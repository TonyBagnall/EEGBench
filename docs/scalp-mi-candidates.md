# Scalp EEG Motor Imagery Candidate Queue

Surveyed and verified against live original-repository APIs (OpenNeuro GraphQL, Zenodo REST API, and Figshare API v2) on **12 November 2026** alongside the selection of **`ImaginedFingers`** (`Damm2026`, OpenNeuro `ds008446` v1.0.1) as the 30th strict scalp-EEG Motor Imagery problem in Neuroverse.

All candidates below are **independent of the existing 85-problem Neuroverse archive** (checked against [`dataset-provenance.md`](dataset-provenance.md)), record **scalp EEG during genuine motor imagery** (excluding overt motor execution tasks such as `Schirrmeister2017` and `PerezBlanco2026`), and report original-host licence terms and exact repository file sizes rather than unverified catalogue declarations.

---

## Tier 1 — Compact, Open-Licence (`CC0` / `CC BY 4.0`) Reserves

| Priority | Source (`MOABB` / Accession) | Proposed Archive Name | Imagined Task & Classes | Subj | Scalp EEG / Hz | Nominal Cases | Verified Licence | Verified Source Size | Admission & Conversion Notes |
|---:|---|---|---|---:|---|---:|---|---:|---|
| 1 | **`Lee2022`** ([OpenNeuro `ds004022`](https://openneuro.org/datasets/ds004022) v1.0.0, Korea Univ.) | `ImaginedLimbActions` | **4-class** right-arm functional MI in orthopaedic-impairment patients: `reaching`, `grasping`, `lifting`, `twisting` (5 s imagery window after 3 s fixation + 4 s cue + 3 s ready) | 7 | `18` ch (`10-20`) @ `500 Hz` | `840` (`120`/subj across 3 runs) | **CC0** | **0.647 GB** | BIDS EEGLAB `.set` (unfiltered BrainVision ActiCHamp, `FCz` ref); drop co-recorded fNIRS files on export. Standard 10–20 labels (`LaBraM`-compatible). |
| 2 | **`Tavakolan2017`** ([Zenodo `18967205`](https://zenodo.org/records/18967205), Simon Fraser Univ., *PLOS ONE* 2017) | `ImaginedArmGraspElbow` | **3-class** same-arm MI: `rest`, `right_hand` grasp, `right_elbow_flexion` (3 s window across 4 sessions) | 12 | `32` ch (`GSN-HydroCel-32`) @ `1000 Hz` | `2,880` (`240`/subj) | **CC0-1.0** | **5.191 GB** | Native BCI2000 `.dat` across 12 archive files. Uses EGI HydroCel `E1..E32` sensor labels rather than 10–20 names; preserve native labels without invented 10–20 aliases. |
| 3 | **`PardoGarcia2026`** ([Zenodo `19599465`](https://zenodo.org/records/19599465), UCM / UPM Madrid) | `ImaginedPinchFist` | **2-class** fine hand MI prior to auditory go cue: `precision_pinch` vs `closed_fist` (1.5 s pre-execution imagery phase) | 18 | `59` ch (`10-10`) @ `1000 Hz` | ~`2,160` | **CC BY 4.0** | **7.223 GB** | 87 files on Zenodo; extract strictly the pre-go-cue imagery interval (`1.5 s` / `1500` samples) so overt post-cue execution does not leak into windows. |

---

## Tier 2 — Larger Open-Licence (`CC0` / `CC BY 4.0` / `ODC-BY`) Multi-Session Cohorts

Suitable when `30+ GB` of scratch + `.ts` storage is available on `D:`:

| Source (`MOABB` / Accession) | Proposed Archive Name | Imagined Task & Classes | Subj | Scalp EEG / Hz | Verified Licence | Verified Source Size | Key Notes |
|---|---|---|---:|---|---|---:|---|
| **`Alawieh2025`** ([Zenodo `15454354`](https://zenodo.org/records/15454354), UT Austin) | `ImaginedHandsLongitudinal` | **2-class** longitudinal kinesthetic MI (`left_hand`, `right_hand`, 4 s) in 25 able-bodied + 2 spinal-cord-injury participants | 27 | `32` ch (`10-20`) @ `512 Hz` | **CC BY 4.0** | **18.288 GB** | 5 GDF archive bundles; drop 3 EOG channels and retain participant clinical-group metadata in sidecars. |
| **`Chang2025`** ([Figshare `28831730`](https://figshare.com/articles/dataset/28831730), *Sci. Data* 2025) | `ImaginedBothHands` | **3-class** rehabilitation MI (`left_hand`, `right_hand`, `both_hands`, 6 s, 4 sessions &times; 30 trials) | 28 | `59` ch (`10-05`) @ `1000 Hz` | **CC BY 4.0** | **19.981 GB** | Record contains 6 paradigms (`ME`, `MI`, `VR-MI`, `MT`, `SRG`, `MG`) in EEGLAB `.set`; extract only the pure `MI` paradigm (`3,360` trials). |
| **`Zuo2025`** ([Figshare `28740260`](https://figshare.com/articles/dataset/28740260), *Sci. Data* 2025) | `ImaginedLegs` | **2-class** lower-limb MI (`left_leg`, `right_leg`, 4 s, 5 sessions &times; 100 trials) | 30 | `30` ch (`10-05`) @ `500 Hz` | **CC BY 4.0** | **22.519 GB** | 335 MAT files; adds bilateral lower-limb flexion/extension MI (`15,000` nominal trials). |
| **`Dreyer2023`** ([Zenodo `8089820`](https://zenodo.org/records/8089820), Inria Bordeaux, *Sci. Data* 2023) | `ImaginedHandsBordeaux` | **2-class** Graz-protocol MI (`left_hand`, `right_hand`, 240 trials/subj) | 87 | `27` ch (`10-20`) @ `512 Hz` | **CC BY 4.0** | **27.475 GB** | Single 27.5 GB archive covering sub-cohorts A/B/C; count once as a single 87-subject problem rather than splitting sub-cohorts. |
| **`Lee2019_MI`** (OpenBMI, GigaDB `100542`) | `ImaginedHandGrasp` | **2-class** two-session MI (`left_hand`, `right_hand`, 4 s) | 54 | `62` ch (`10-20`) @ `1000 Hz` | **CC0-1.0** | >`20 GB` | Retain offline labelled runs (`200` trials/subj across 2 sessions, ~`21.4 GB` dense float64); online runs lack uniform labels. |
| **`Ma2022`** (NEMAR `nm000288`, Shanghai Univ., *Sci. Data* 2022) | `ImaginedHandsMultiSession` | **2-class** 5-session MI (`left_hand`, `right_hand`, 4 s, `11,988` retained trials) | 25 | `32` ch (`10-20`) @ `250 Hz` | **CC BY 4.0** | Inspect NEMAR | EDF format, standard 10–20 channels; verify original OpenNeuro/Figshare checksums before conversion. |
| **`GuttmannFlury2025_MI`** (SJTU, *Sci. Data* 2025) | `ImaginedHandsGraspSJTU` | **2-class** hand-grasping MI (`left_hand`, `right_hand`, `2,520` MI trials across 63 sessions) | 31 | `62` ch (`10-05`) @ `1000 Hz` | **CC0** | Inspect host | Multi-paradigm BDF release; select strictly the `MI` sessions (separate from `GuttmannFlury2025_ME`). |
| **`Wang2025`** ([HF `Jiaheng-Wang/ZJU-MI-EEG`](https://huggingface.co/datasets/Jiaheng-Wang/ZJU-MI-EEG), ZJU, *IEEE TNSRE* 2025) | `ImaginedLimbsZJU` | **4-class** two-day MI (`left_hand`, `right_hand`, `tongue`, `feet`) | 15 | `62` ch (`10-10`) @ `256 Hz` | **ODC-BY** | Inspect HF | Verify native MAT sensor order and calibration vs online feedback runs before conversion. |

---

## Tier 3 — Restricted / Qualified Reserves (Local-Only or Pending Metadata Resolution)

- **`MIBMPI2024` (`ImaginedPhoneGestures`, [Zenodo `13626922`](https://zenodo.org/records/13626922))**: **Already piloted and validated locally** ([`mibmpi-to-30-pilot-result.json`](mibmpi-to-30-pilot-result.json): 8 subjects, 13 scalp EEG channels @ 128 Hz, 2.5 s window, `imagined_screen_tap` vs `imagined_thumb_swipe_down`). Held in reserve because the Zenodo description specifies **CC BY-NC 4.0** (non-commercial).
- **`MIMED2024` (`ImaginedHandsTrunk`, Mendeley `zs25xxjkm9` v3)**: Deferred after [`mimed-native-quality-audit.json`](mimed-native-quality-audit.json) uncovered 85 cross-participant duplicate waveforms and one conflicting label pair.
- **`Shin2022` (Figshare `20383716`, CC BY 4.0, 0.35 GB, 10 subj, 16 ch @ 250 Hz)** & **`Jia2019` (Figshare `7636301`, CC BY 4.0, 15 subj, 63 ch @ 512 Hz)**: Require primary-author electrode-order recovery because native files omit anatomical channel names.
- **`Kodera2023` (Zenodo `7893846`, CC BY 4.0, 1.77 GB)**: Mixes two sensor/rate cohorts with unresolved cross-date participant correspondence.
