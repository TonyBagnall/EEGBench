# Remaining MOABB candidates

Liu2024 has subsequently been prepared as
[ImaginedHandsStroke](imagined-hands-stroke-preparation.md), with documented
derived-product and trigger-quality exclusions. The survey counts below remain
the original pinned snapshot, rather than the current unprepared remainder.

Survey date: **5 November 2026**. This was a metadata and loader-source review;
**no EEG recordings were downloaded, converted or changed**.

**Subsequent preparation:** [ImaginedGripForce / MartinezPeon2024](imagined-grip-force-preparation.md)
has since been downloaded and added to the collection. The counts below describe
the survey snapshot before that preparation. Follow-on source-only downloads
are recorded in [open-moabb-download-results.json](open-moabb-download-results.json)
and are now [prepared archive problems](open-moabb-conversions.md).

## How many remain?

The [live MOABB catalogue](https://moabb.neurotechx.com/docs/dataset_summary.html)
contains **206 entries**. Comparing its source collections with our provenance
pages gives:

| Catalogue accounting | Entries |
|---|---:|
| Source recordings already represented in EEGBench | 19 |
| Additional aggregate/subset/view entries excluded from the count below | 5 |
| Remaining candidate entries | **182** |
| Of these: declared fully open data licence | **146** |
| Of these: non-commercial, no-derivatives or research-only terms | **28** |
| Of these: insufficiently established data licence | **8** |

**182 is a screening pool, not 182 confirmed independent classification problems.**
146 have a promising licence declaration, rather than 146 original-host licence
checks. Some families still need recording-level comparison, usable labels and
sensor metadata checks. An exact count of additional independent problems would
require resolving those checks. The five original-host-checked candidates below
are the strongest next batch; all five have CC BY 4.0 data licences.

The full 206-entry accounting, declarations, source links, grouping warnings and
shortlist estimates are in [the machine-readable inventory](moabb-remaining-catalogue.json).
It includes exclusions, so another agent can reproduce the totals.

At the survey snapshot, our registry had 54 problems and `eeg.txt` had 50. Those
are archive problem counts, whereas the 19 above are MOABB catalogue entries:
one source can contribute several archive problems.

## Priority: fully open first, then smaller

Here, fully open means CC0, CC BY, CC BY-SA or ODC BY, with their attribution,
share-alike or database obligations retained. NC and ND licences are separate.
MOABB's software licence does not establish permission to redistribute data.

These five have licences checked through their original repositories' metadata
APIs. Sizes are **decimal GB**. Download sizes are sums of file sizes advertised
by the repository, not measured transfers. Dense estimates describe float64 EEG
epochs at native rate, before any filtering/resampling; endpoint conventions and
dropped epochs can change them slightly. `.ts` files, source caches and conversion
working memory require additional space. No `.ts` size has been measured.

| Suggested order | MOABB source | Task | Subjects / EEG channels / Hz | Planned cases and dense GB | Original-host files GB |
|---:|---|---|---|---|---:|
| 1 | [MartinezPeon2024](https://doi.org/10.6084/m9.figshare.25773342) | Imagine squeezing the right hand at 10%, 40% or 70% of maximum force; 3 classes | 10 / 14 / 128 | 300 Ãƒâ€” 14 Ãƒâ€” 640; **0.022** | **0.048** |
| 2 | [Rodrigues2017 / Alpha Waves](https://doi.org/10.5281/zenodo.2348891) | Eyes closed versus open; 2 classes | 19 in loader / 16 / 512 | 190 Ãƒâ€” 16 Ãƒâ€” 5120; **0.125** | **0.335** |
| 3 | [RomaniBF2025ERP / BrainForm](https://zenodo.org/records/17225966) | Attend a flashing target in a game/speller; target versus non-target ERP | 22 / 8 / 250 | Calibration-only estimate: 26,400 Ãƒâ€” 8 Ãƒâ€” 225; **0.380** | **0.304** |
| 4 | [Castillos2023](https://doi.org/10.5281/zenodo.8255618) | Attend one of four coded visual targets; 2 code types Ãƒâ€” 2 contrasts | 12 / 28 exposed EEG / 500 | Four conditions together: 2880 Ãƒâ€” 28 Ãƒâ€” 1100; **0.710** | **0.588** |
| 5 | [Kumar2024](https://doi.org/10.5281/zenodo.10694880) | Imagine left versus right hand, longitudinal feedback training | 18 / 22 / 512 | Bar-feedback runs: 7200 Ãƒâ€” 22 Ãƒâ€” 2560; **3.244** | **4.471** |

This order uses estimated epoch-array size within the original-host-confirmed
licence tier. It is not a strict ordering of raw download sizes.

Important preparation decisions, still pending:

- **MartinezPeon:** 60 files, each with five cues; 30 trials per participant.
  Force labels are file-level; cue times are supplied by the protocol, not recorded
  event triggers. Preserve that distinction. The loader documents 14 EEG columns
  separately from time/sample/gyroscope columns and names them in column order.
- **Rodrigues:** the original repository describes 20 participants; the loader
  exposes 19 and skips subject 7. Keep original IDs. The repository has MATLAB and
  CSV representations of the same recordings: the 0.335 GB total includes both,
  so a single-format retrieval should be smaller. This is a Grenoble 2017 study,
  distinct from our UCI-derived EyesOpenShut.
- **BrainForm:** the estimate covers two calibration sessions only, not every game
  run. The record contains raw, BIDS, pilot and failed-session archives; these
  must not be counted as independent datasets. Check participant/session coverage
  before choosing the representation and task subset.
- **Castillos:** the four loaders select separately recorded stimulation conditions
  from **one study**. Prefer one four-target problem with a condition sidecar, or
  explicitly document separate recording subsets. MOABB's default two-class
  code-bit task is a different view; do not count it as another independent dataset.
  Four-target extraction must use the original cues and code/target information.
- **Kumar:** the estimate covers 400 bar-feedback trials per participant over six
  sessions. Racing runs are additional. The 5 s interval follows the current
  catalogue; final epoch boundaries need checking against the original protocol.

## Other open-declared candidates, smaller estimates first

The licences in this table are **MOABB declarations** unless stated otherwise;
original-host data terms must be checked before downloading for redistribution.
Cases below are planning estimates, not validated conversions.

| Source | Task | Subjects / EEG channels / Hz | Dense GB estimate | Licence / next check |
|---|---|---|---:|---|
| [BCIComp2020WalkingERP](https://moabb.neurotechx.com/docs/generated/moabb.datasets.BCIComp2020WalkingERP.html) | Walking visual oddball; target/non-target | 15 / 46 / 100 | **0.166**: 4500 Ãƒâ€” 46 Ãƒâ€” 100 | CC BY 4.0; inspect OSF data terms and native versus distributed sampling. Preserve supplied temporal test split; merge training/validation. |
| [BNCI2003_004](https://moabb.neurotechx.com/docs/generated/moabb.datasets.BNCI2003_004.html) | Imagine right hand versus feet | 5 / 118 / 100 | **0.463**: 1400 Ãƒâ€” 118 Ãƒâ€” 350 | CC BY 4.0; resolve test labels. Despite loader name, its code identifies **BCI Competition III IVa**, distinct from our FingerMovements (Competition II IV). |
| [Kueper2024](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Kueper2024.html) | Self-initiated unilateral versus bilateral movement | 8 / 64 / 500 | **1.475 minimum**: 1920 Ãƒâ€” 64 Ãƒâ€” 1500 | CC BY 4.0; extra unilateral run in XP01 raises total. Check movement-onset definition. |
| [Kaneshiro2015](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Kaneshiro2015.html) | Six image categories | 10 / 124 / 62.5 | **1.646**: 51,840 Ãƒâ€” 124 Ãƒâ€” 32 | CC BY 3.0; recover actual retained sensor order rather than accept generated E1Ã¢â‚¬â€œE124 names. Distinct from our face/scramble FaceDetection. |
| [Farabbi2020](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Farabbi2020.html) | Left/right hand imagination with first/third-person feedback | 12 / 32 / 250 | **2.212**: 5760 Ãƒâ€” 32 Ãƒâ€” 1500 | CC BY 4.0; 6 s catalogue interval includes baseline; a 4 s imagery interval would be smaller and must be documented. |
| [BCIComp2020UpperLimb](https://moabb.neurotechx.com/docs/generated/moabb.datasets.BCIComp2020UpperLimb.html) | Three imagined grasp types | 15 / 60 / 250 | **3.240**: 6750 Ãƒâ€” 60 Ãƒâ€” 1000 | CC BY 4.0; separate track/recordings from ImaginedCommands and WalkingERP, although same competition paper/OSF collection. |
| [Thielen2015](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Thielen2015.html) | 36-target coded visual spelling | 12 / 64 / 2048 | **5.708**: 1296 Ãƒâ€” 64 Ãƒâ€” ~8602 | CC0; high native rate. Distinct study from Thielen2021/CodedSymbols. |

Low channel count/rate also makes **Chailloux2020** (19 participants, 8 EEG,
256 Hz, CC0), **Kodera2023** (29, 9 EEG, 500 Hz, CC BY),
**MartinezPeon2024** above, **MIMED2024** (30, 14 EEG, 128 Hz, CC BY) and
**MILimbEEG** (60, 16 EEG, 125 Hz, CC BY) worth early inspection. Missing reliable
total epoch counts prevent a defensible size rank for the first four apart from
MartinezPeon. MILimbEEG has execution and imagination recordings; the MOABB loader
uses imagination only and retrieves the whole source archive. Determine actual
trial/repetition totals and download size before describing it as small.

**ERP CORE has five additional recording tasks**: N170, MMN, N2pc, P3 and
flankers (choose ERN or LRP). N400 is already WordRelatedness. They are additional
problems from an existing study, not five new studies. Source CC BY-SA 4.0 was
previously established in [our N400 report](word-relatedness-preparation.md);
the catalogue's CC BY declaration omits that share-alike condition. They need
epoch-count/source-size checks before ranking by space.

## Larger open candidates

Keep **Cho2017**, **Dreyer2023**, **Lee2019_MI/ERP/SSVEP** and **Schirrmeister2017**
on the list, after the compact queue. Lee2019 MI alone is about **21.43 GB** in
float64 for 54 participants Ãƒâ€” 2 sessions Ãƒâ€” 100 labelled offline trials Ãƒâ€” 62 EEG
Ãƒâ€” 4000 samples. Including another labelled phase doubles the case count; online
MI/SSVEP test labels are not uniformly available through the loader. Do not quote
the smaller offline-only estimate as the complete study.

Cho needs original-host licence reconciliation. Schirrmeister's task is executed
movement despite the imagery catalogue grouping, and its source warns about a
large sensor failure in participant 14. MAMEM1/2 are additional experiments to
MAMEM3/WirelessFlicker, but their 256 EEG channels make them less compact; sensor
names/order also need original-file verification.

BigP3BCI / **Mainsah2025_AÃ¢â‚¬â€œS2** deserves a separate survey. The
[original PhysioNet release](https://physionet.org/content/bigp3bci/1.0.0/)
is public and groups **20 substudies**, not twenty label variants of one run.
The loader exposes those substudies separately, with 16/32 EEG at 256 Hz. It is
therefore inappropriate to collapse all twenty just because they share a DOI.
Select the smallest by per-study file totals and epoch counts, and recover
cross-study participant identities before claiming cohort independence.

## Restricted or unresolved terms come later

The complete inventory separates these from open-declared candidates. Examples:

- **BNCI2014_002:** CC BY-ND; compact (~0.688 GB dense), but the loader supplies
  channel names absent from source columns. Sensor provenance remains a blocker.
- **BNCI2014_009:** CC BY-NC-ND; small flash epochs are possible, but catalogue
  character-selection durations must not be mistaken for flash-epoch lengths.
- Other BNCI NC/ND entries, Stieger2021, Dong2023, MIBMPI2024, Liu2020BETA,
  MartinezCagigal2023 and others remain behind the fully open queue.
- **Shin2017A/B:** GPL declaration plus explicit research agreement handling;
  verify the actual data grant and access terms. Do not infer it from GPL alone.
- **Nguyen2017 variants / Pressel2016:** `other-open` is insufficient detail for
  redistribution approval. **EPFLP300** remains unknown in the catalogue.
- **Schrag2026Pediatric:** openly licensed does not make every loader label ground
  truth. Most game movements are labelled with classifier output; only a small
  subset has instructed targets. Exclude classifier-generated labels from a
  conventional supervised benchmark unless explicitly justified.

## Recording identity and exclusions

The machine-readable inventory records these decisions for every catalogue row:

- Already covered: AlexMI, BI2014a, BNCI2014_001, BNCI2014_004, BNCI2014_008,
  BNCI2015_003, ErpCore2021_N400, Kalunga2016, MAMEM3, Nakanishi2015, Nieto2022,
  Ofner2017, Peterson2020, PhysionetMI, Thielen2021, TrianaGuzman2024,
  Wang2016, Weibo2014 and Zhou2016. More classes or another epoching view of these
  recordings do not establish a new source collection.
- Count Dreyer2023 **once**, not also A/B/C. The aggregate includes those cohorts.
- Exclude the generic ErpCore2021 entry; count its recording tasks instead.
  Exclude LRP from the numerical pool because ERN already represents flankers.
- Castillos' four conditions, Lee2024's five appliance experiments, Lee2019's
  three modalities and Nguyen's four variants share study families. Their file
  membership must be preserved; a common paper alone neither proves identical
  recordings nor proves independence.
- WRCC2023 A/B/C use separate depositions; comparison of cohort/recording identity
  is still required. BEETL leaderboard/final phases and their differing class maps
  likewise need explicit reconciliation, not naive concatenation.
- Unresolved provenance for existing FeedbackButton/ButtonPress and local
  institutional data means that complete non-overlap with the archive cannot be
  certified through metadata alone.

## Reproducibility and next preparation

The catalogue snapshot's SHA256 and counts are saved in the inventory. Loader
inspection used MOABB commit
[`bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`](https://github.com/NeuroTechX/moabb/tree/bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5/moabb/datasets).
The live documentation is recorded separately; its build is not asserted to be
identical to that source commit. Original API evidence for the first five is
summarised in [the inventory](moabb-remaining-catalogue.json), including byte totals
and licence identifiers. Download size includes duplicate representations where
the host supplies them; it is not an estimate of independent EEG volume.

Recommended next preparation: **MartinezPeon2024**, followed by **Rodrigues2017**.
At preparation time, recover actual channel order/types, subject/session/run/file
and cue identifiers; validate labels, flat channels, units, duplicate signals and
splits. Use subject-disjoint splits unless an intentional source protocol specifies
otherwise. Preserve inferred timing separately from recorded event timing. Existing
datasets, results and `eeg.txt` remain unchanged by this survey.

## Subsequent preparation: WalkingTargets

BCIComp2020WalkingERP is now prepared as **WalkingTargets** (6 November 2026): 3,600 train / 900 test, 15 participants, 42 EEG channels, 100 samples at 100 Hz. Original OSF CC BY 4.0 verified; official within-participant split preserved with train+validation merged. See [preparation and metadata](walking-targets-preparation.md). Earlier survey counts are historical snapshots.


## Subsequent preparations: SymbolAttention and ArmCoordination

Chailloux2020 is prepared as [SymbolAttention](symbol-attention-preparation.md); Kueper2024 as [ArmCoordination](arm-coordination-preparation.md), 6 November 2026. Both use verified original data licences and preserve native sensor/participant metadata. Kaneshiro2015/VisualCategories is [deferred after a native label conflict](visual-categories-preparation.md). Survey counts above are historical; the current registry has 66 problems and eeg.txt selects 62.
