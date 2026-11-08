# Route from 19 to 30 motor imagery problems

**Live update 8 November 2026:** Batista2022/ImaginedHandsHaptics, PoloHortiguela2025/ImaginedAnkleRest and Leeuwis2021/ImaginedHandsFeedback are complete and registered. Current collection: 77 registered / 73 selected; 25 MI problems (24 scalp EEG plus one ECoG), five short of 30. [Latest results and metadata](mi-next-three-preparation.md). The original survey below is historical. Remaining candidates Pan2023, Pan2025, Rozado2015, Cho2017 and Daly2020 still need their original access/licence/recording-identity checks; none started in this batch.

Reviewed8November2026 against current eeg.txt, source provenance, live MOABB
documentation and original-host metadata. This review downloaded **no EEG**.
Current selected collection:67problems, of which19 are motor imagery under the
existing count (18scalp EEG plus the invasive ECoG MotorImagery entry).
Imagined speech/commands and executed movements are excluded from this MI count.

## Finish two existing preparations first: 19 to 21

| Problem | Original MOABB source | Task | People | Current state |
|---|---|---|---:|---|
| ImaginedHandsRobot | Farabbi2020 | Left/right hand with first-/third-person robot feedback | 12 | Full validated D:/Data/EEG output exists,2880/2880cases32x1000at250Hz; not yet registered/selected. No redownload needed. |
| ImaginedGrasps | BCIComp2020UpperLimb, competition Track4 | Cylindrical/spherical/lumbrical grasp imagination | 15 | Pilot passed; full49-file original source receipt present, pilot=false. Final output absent; reverify cached source hashes and run full conversion. |

Both original data grants were verified CC BY4.0. Neither is included in the
current19. Source phase/session splits, original channel identities and metadata
are already implemented in their standalone adapters. Completing their remaining
work adds two problems, not two newly downloaded studies in this review.

## Nine further candidate collections: potential 21 to 30

This is an admission queue, **not nine already validated datasets**. Reported
participant counts are source/MOABB counts before native quality checks. New
problem names will follow task/source inspection. Source links lead to dataset
documentation and its original accession.

| Priority | MOABB source | Task | People | EEG / Hz | Compressed original files where verified | Licence/access status |
|---:|---|---|---:|---|---|---|
| 1 | [Vagaja2023](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Vagaja2023.html) | Left/right hand after VR embodiment priming | 26 | 32 /500 | 2.178GB original ZIP | Original Zenodo8086086 CC BY4.0 rechecked. MI run only; resting/priming runs are not additional MI problems. |
| 2 | [Batista2022](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Batista2022.html) | Left/right hand with VR/haptic feedback | 20 | 32 /500 | 2.863GB original files | Original Zenodo7664069 CC BY4.0 verified. Preserve pilot IDs and distinguish condition runs from recording visits. |
| 3 | [PoloHortiguela2025](https://moabb.neurotechx.com/docs/generated/moabb.datasets.PoloHortiguela2025.html) | Imagined ankle movement versus rest with exoskeleton conditions | 6 | 28 /250 | 2.936GB original files | Original Zenodo14672334 CC BY4.0 verified. STATIC/MOTION are conditions, not automatically separate visits or independent problems. |
| 4 | [Leeuwis2021](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Leeuwis2021.html) | Left/right hand, calibration and feedback | 55 | 16 /250 | 5.135GB across224original files | Original DataverseNL10.34894/Z7ZVOD API succeeded and CC BY4.0 confirmed. Four runs, one session; nominal8800trials. |
| 5 | [Pan2023](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Pan2023.html) | Left/right hand across two days | 14 | 28 /250 | Not yet verified | MOABB declares CC0. Harvard Dataverse10.7910/DVN/251NOW metadata API currently403; confirm original data grant/access and exact file pins before retrieval. |
| 6 | [Pan2025](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Pan2025.html) | Further cross-session left/right hand recordings | 10 | 28 /250 | Not yet verified | MOABB declares CC0; same current API403 for10.7910/DVN/GH74ZG. Different accession/protocol in documentation, but compare source recordings with Pan2023 before counting both. |
| 7 | [Rozado2015](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Rozado2015.html) | Left-hand grasp imagination versus rest, with pupillometry | 30 | 32 /512 | Not yet verified | CC0 declared; verify original Harvard Dataverse10.7910/DVN/28932. Native XDF labels distinguish scalp EEG from trigger/EX/AUX inputs. |
| 8 | [Cho2017](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Cho2017.html) | Left/right hand | 52 | 64 /512 | Not yet verified | Original GigaDB10.5524/100295 record/file terms still need reconciliation with MOABB's CC BY4.0 declaration. Four EMG inputs are not EEG. |
| 9 | [Daly2020](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Daly2020.html) | Imagine right-hand squeezing versus relax, controlling music tempo | 18 released | 19 /1000 | Not yet verified | OpenNeurods002720 v1.0.1 has documented CC0/CC BY4.0 declaration discrepancy; retain/resolve original terms and attribution. Calibration/targetless runs need explicit accounting. |

The priority reflects readiness and verified source download size where known;
it is not a strict final `.ts` size ranking. In particular,20second Daly trials,
high channel counts and native sampling rates can expand substantially. Verify
full source+extraction+NPZ+text footprints before each batch. Do not resample or
invent shorter epochs solely to force a storage target. D had approximately121GB
free following the most recent transfer; recheck live space before starting.

## Identity, licence and quality gates

- Count recording collections, not alternate labels, sampling rates or condition
  views. Compare Pan2023/Pan2025 native file/waveform membership. Batista and
  Vagaja share a research lineage/hardware: distinct documented protocols are
  promising, but inspect native recording identity before admitting both.
- Dreyer2023 aggregate and A/B/C must not all be counted. Similarly, OpenBMI MI
  is one MI problem; its ERP/SSVEP recordings do not contribute to the MI target.
- The catalogue's broad Imagery label includes speech, visual imagery and some
  executed-movement datasets. It is not a motor-imagery admission criterion.
  Schirrmeister2017 and execution-only upper-limb tasks do not fill this quota.
- Original data grant, exact channel identities/order, units, labels, IDs, split,
  duplicate/flat audit, full numeric readback and aeon checks remain required.
  Unknown anatomical names must be flagged rather than invented. Raw-source
  copies and suspect labels are not fixed by choosing an owner/class blindly.
- Rozado documentation flags unusually noisy subjects10/15. Large amplitude is
  not by itself a flat channel or a reason for an undocumented rescaling/drop.
- MIMED remains outside the queue: widespread cross-ID copies and a conflicting
  class require resolution or a separately chosen reduced scope. It is not a
  numerical shortcut to30. Existing Zhang anatomical-sensor metadata flag remains.

## Reserves if a primary candidate fails

1. [GrosseWentrup2009](https://moabb.neurotechx.com/docs/generated/moabb.datasets.GrosseWentrup2009.html):
   ten people,128EEG,500Hz, haptic left/right hand imagination. Documentation
   describes150trials per condition per person, not150total. Large dense/text
   footprint; native sensor/rate/source terms require inspection.
2. [Dreyer2023](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Dreyer2023.html):
   87people,27EEG,512Hz, left/right hand. Count the aggregate once; larger source.
3. [Lee2019_MI](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Lee2019_MI.html):
   OpenBMI54people,62EEG,1000Hz, two sessions; retain only genuinely labelled
   source phases and account for its much larger native storage requirements.
4. Alawieh2025 or Chang2025 for further independent MI cohorts, after file-size,
   clinical/condition scope and original metadata checks.

Jia2019, Shin2022 and Perdikis2018 remain behind the stronger queue because their
original anatomical sensor mappings need recovery. Kodera additionally has
unresolved cross-date participant correspondence and two recording setups.
Do not split those into extra apparently independent datasets to meet a count.

If30specifically means **scalp EEG MI**, the existing18scalp EEG entries need12
additional problems; one reserve is needed beyond the11above. The headline
19-to30 plan retains the existing counting rule including one ECoG entry.

## Reproducibility and status

Existing source snapshot: MOABB commit
`bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`; live documentation reviewed separately.
Original-host checks: [mi-roadmap-source-checks.json](mi-roadmap-source-checks.json),
with exact retrieved metadata under `source-evidence/motor-imagery-survey/`.
Vagaja and Leeuwis original metadata succeeded; Harvard API403 does not itself
prove human approval or registration is required. No attempt was made to bypass
an access gate. No new EEG downloaded and no current registry/arrays changed.

Recommended next action: register the already validated ImaginedHandsRobot,
finish cached ImaginedGrasps, then pilot Vagaja/Batista/Polo and progress through
the queue after each native audit. Use [the conversion handover](../DATASET_CONVERSION_HANDOVER.md).
