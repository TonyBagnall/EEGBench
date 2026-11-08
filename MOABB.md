# MOABB dataset review for EEGBench

**Latest completion8November2026:** ImaginedHandsRobot, ImaginedGrasps and ImaginedHandsEmbodiment (Vagaja2023) are fully validated and registered:74registered/70selected,22MI including one ECoG. [Results and metadata](docs/mi-completion-batch.md). Eight further MI problems needed for30; Batista2022 is next, not downloaded here. Earlier batch/survey snapshots below are historical.

**MI target of30:** [the current19-to30 roadmap](docs/motor-imagery-road-to-30.md)
identifies two existing unfinished additions plus nine further candidate
collections, with reserves and explicit identity/licence/size checks. This is a
metadata-only plan, not11already validated additions.

**Latest batch, restored to D:** two NeuroTUM single-participant problems and
ImaginedHandFootActions/MILimb are prepared;71registered/67selected. MILimb has
explicit copied-rest exclusions and global flat-sensor removals. The user resumed
D: access; all staged data/sources/pilots are now checksum-verified on D:. [Batch details](docs/temp-c-mi-preparations.md).

**Latest completed batch:** ImaginedHandGestures and ImaginedArmTasks,
68 registered /64 selected. Zhang has an explicit unknown anatomical sensor
identity flag. MIMED was stopped on cross-participant copies; see
[the preparation report](docs/compact-imagery-preparation.md).

**8 November 2026 motor imagery priority update:** see the
[small motor imagery queue](docs/motor-imagery-next-candidates.md). The strongest
next pilots are MIMED2024 (19.526 MB imagery-only) and MOVING2024 (98.204 MB
EEG-only), both original-host CC BY 4.0. NeuroTUM and Shin2022 are also small but
have task/split and sensor-identity issues respectively. That initial update inspected metadata/loading code only. The user subsequently
authorised the first three downloads: see the [conversion/source-quality report](docs/compact-imagery-preparation.md).
MIMED has cross-participant copies and a conflicting-label waveform; the full
release is stopped rather than admitted from the earlier metadata-only shortlist.

Liu2024 is now prepared as [ImaginedHandsStroke](docs/imagined-hands-stroke-preparation.md):
1400/440 cases, 46 retained IDs and 29 EEG channels. The current registry has
**60** prepared problems and `eeg.txt` selects **56**.

Further source comparisons and candidate aliases are documented in
[AdaBrain-Bench](AdaBrain-Bench.md) and [ETH-DISCO EEG-Bench](EEG-Bench.md).
The latter's Liu2022 adapter is actually MOABB Liu2024, now prepared here with
original-host CC BY 4.0 evidence and explicit release-integrity exclusions.

All four follow-on cached sources are now [converted and validated](docs/open-moabb-conversions.md):
RestingEyeState, GameTargets, CodedFlickerTargets and ImaginedHandTraining. The
four-source batch brought the registry to **59** prepared problems and `eeg.txt`
to **55**; the subsequent stroke preparation raises those counts as stated above.

## Remaining candidates: 5 November 2026

See the [updated survey, ranked by open data licence then size](docs/moabb-remaining-candidates.md)
and [complete machine-readable catalogue accounting](docs/moabb-remaining-catalogue.json).
Of 206 catalogue entries, 19 source entries are already represented and five
aggregate/subset/view entries are excluded, leaving **182 candidate entries**:
**146 open-declared**, 28 restrictive and eight unresolved. These are screening
counts, not a claim of 182 independent, validated problems. The recommended next
source is **MartinezPeon2024** (three imagined grip-force levels; approximately
48 MB source files and 22 MB dense float64 epochs), followed by **Rodrigues2017**.
Five leading candidates have original-host CC BY 4.0 checks. This survey retrieved
only documentation, loader code and repository metadata; no EEG data.

## Earlier review and preparation history

The first preparation from the new open-data queue is now complete:
[ImaginedGripForce / MartinezPeon2024](docs/imagined-grip-force-preparation.md),
240/60 cases, ten participants, 14 EEG channels, three force classes at 128 Hz.
The registry has 55 problems and `eeg.txt` has 51. Additional native source
downloads are tracked in [the batch progress and source inspection](docs/open-moabb-downloads.md);
downloaded sources are not counted as prepared problems.

Reviewed 4 November 2026. Starting points: [MOABB documentation](https://moabb.neurotechx.com/docs/index.html)
and [dataset catalogue](https://moabb.neurotechx.com/docs/dataset_summary.html).
Compared with the archive inventory in [eeg.txt](eeg.txt), using our
[provenance documentation](docs/dataset-provenance.md).

**MOABB has substantial useful data that we have not assimilated.** The strongest
opportunity is to broaden our task coverage with P300/ERP, SSVEP and c-VEP data,
alongside selected new motor-imagery recording collections. This is a catalogue
review and a candidate shortlist, not a completed licence or signal audit of every
loader. The initial review downloaded no EEG data. BI2014a was subsequently
prepared as **VisualSubjects**, followed by Kalunga2016 as **FlickerAttention**,
and ERP CORE N400 as **WordRelatedness**. Ofner2017 supplies **ArmMovements** and
**ImaginedArmMovements**. Thielen2021 adds **CodedSymbols**, bringing the registry
to 47 problems. These six prepared MOABB problems represent five source studies;
the Ofner pair share people but use different recording days. See the
[first preparation report](docs/moabb-preparations.md),
[Ofner report](docs/ofner-preparations.md) and
[CodedSymbols report](docs/coded-symbols-preparation.md).

## Follow-up shortlist, 5 November 2026

Rechecked the live catalogue, individual dataset pages and selected loader code
against the current 47-problem registry. No further EEG files were downloaded.
These are candidates for source/file inspection, not approved archive additions.
Licences below are MOABB declarations unless explicitly described otherwise;
original-record applicability to redistribution remains an admission check.

Wang2016 has now been prepared as **FlickerSymbols**. Next inspect **OpenBMI** and
**Sosulski2019**. **Kaneshiro2015** is particularly attractive for task diversity,
but its sensor mapping needs investigation before conversion.

| Candidate | Classification task / possible archive name | Subjects | EEG channels | Frequency | Why consider it / qualification |
|---|---|---:|---:|---:|---|
| [Wang2016](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Wang2016.html) | Which of 40 flickering symbols is attended? **FlickerSymbols** | 35 | 64 | 250 Hz | 8400 source trials, six blocks, each 64 ? 1500. Already shortlisted but unprepared. MOABB declares CC BY 4.0. Retain original CB1/CB2 names; their proposed correspondence to P9/P10 is unconfirmed. |
| [Lee2019_MI](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Lee2019_MI.html) | Imagined left/right grasping; **ImaginedHandGrasp** | 54 | 62 | 1000 Hz | Two sessions and useful repeat-session structure. CC0 declared. Default offline data provide 100 labelled trials/session; documented online MI runs lack labels. |
| [Lee2019_SSVEP](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Lee2019_SSVEP.html) | Attend one of four directional flicker targets; **FlickerDirections** | 54 | 62 | 1000 Hz | Same OpenBMI study/cohort, separate task recordings. CC0 declared. Offline 100 trials/session, four classes; documented online runs lack labels. |
| [Lee2019_ERP](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Lee2019_ERP.html) | Attended versus unattended speller flashes; **SpellerAttention** | 54 | 62 | 1000 Hz | Third OpenBMI experiment, two sessions. CC0 declared. Preserve flash, sequence and character identities; this is a binary flash task, not a 36-class symbol task. |
| [Sosulski2019](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Sosulski2019.html) | Attended high tone versus low tone; **AuditoryAttention** | 13 | 31 | 1000 Hz | New auditory oddball collection, CC BY-SA 4.0 declared. Original BrainVision events and sensor metadata are available. Variable tone spacing causes overlapping epochs; split subjects/recordings, not random overlapping windows. |
| [Kaneshiro2015](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Kaneshiro2015.html) | Six viewed object categories; **VisualCategories** | 10 | 124 | 62.5 Hz | Human/animal faces and bodies, fruit/vegetables and objects. Distributed processed trials are 124 ? 32. Loader source declares CC BY 3.0, but generates E1?E124 names: recover actual retained electrodes before accepting that correspondence. |
| [Cattan2019_VR](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Cattan2019_VR.html) | Visual target/non-target flashes across screen and VR; **DisplayAttention** | 21 | 16 | 512 Hz | CC BY 4.0 declared; original record is Zenodo 2605204. Retain PC/VR condition metadata in one problem; do not count two views of this study as two independent studies. |
| [Cho2017](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Cho2017.html) | Imagined left/right hand; name to distinguish existing hand tasks | 52 | 64 | 512 Hz | Large independent cohort with electrode locations and EMG. Already shortlisted. MOABB declares CC BY 4.0; original data accession is GigaDB 100295, whose record-specific terms need reconciliation with that declaration. |
| [Thielen2015](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Thielen2015.html) | Which of 36 coded symbols is attended? **CodedCharacters** | 12 | 64 | 2048 Hz | Independent c-VEP study, CC0 declared. Already shortlisted; high sample rate and long trials increase archive size. Preserve whole-trial target labels rather than turning code bits into another view. |
| [Zhou2016](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Zhou2016.html) | Imagined left hand, right hand or feet; **ImaginedHandsFeet** | 4 | 14 | 250 Hz | Small three-session collection, 1800 nominal trials. CC BY 4.0 declared. Document the small subject count; task cue lasts five seconds although the snapshot lists a ten-second trial. |
| [Huebner2017](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Huebner2017.html) | Visual speller target/non-target flashes | 13 | 31 | 1000 Hz | CC BY 4.0 declared; many trials but limited task novelty. Three loader sessions represent blocks. Snapshot's 25 seconds is a character selection, not the single-flash epoch. |
| [Schirrmeister2017](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Schirrmeister2017.html) | Executed left/right hand, feet or rest; **HandFeetRest** | 14 | 128 nominal | 500 Hz | High-gamma dataset; executed movements despite the Imagery catalogue tag. CC BY 4.0 declared. Lower priority: source warns approximately half of subject 14's sensors lose meaningful test signal. Verify actual channel types and current distributed frequency before choosing an export. |

### More tasks from the existing ERP CORE study

Beyond our N400 **WordRelatedness**, inspect **N170** (faces versus other visual
stimuli), **MMN** (standard versus quieter deviant tones), **N2pc** (left versus
right visual target location), **P3** (attended versus unattended letters), and
**ERN** (correct versus incorrect responses). These use 40 participants and
30 scalp EEG channels at 1024 Hz, plus auxiliary channels in the source. They
can supply five additional recording experiments from an existing study.
**ERN and LRP reuse the same flankers recordings**, so choose one for a collection
requiring unique recordings. Preserve meaningful task labels instead of the
loader's generic Target/NonTarget aliases. The original licence discrepancy
already documented for WordRelatedness also needs to be retained for these tasks.
Source: [ERP CORE loader and event encodings](https://github.com/NeuroTechX/moabb/blob/develop/moabb/datasets/erpcore2021.py),
[existing licence/source audit](docs/word-relatedness-preparation.md).

### Size and metadata priorities

Calculated signal memory, excluding metadata and loading overhead, is about
**6.45 GB float64** for all Wang2016 trials (8400 ? 64 ? 1500), and **1.65 GB**
for Kaneshiro2015 if all nominal 51840 trials are present (51840 ? 124 ? 32).
Each OpenBMI MI/SSVEP offline task is approximately **21.43 GB float64** at its
native rate (54 ? 2 ? 100 ? 62 ? 4000); `.ts` size is additional and has not been
measured. These are arithmetic estimates, not validated case totals or exports.

Wang supplies sensor locations, frequency/phase and participant files at the
[original laboratory download page](https://bci.med.tsinghua.edu.cn/download.html).
The [3.7 GB MOABB mirror](https://zenodo.org/records/14865172) is a reupload;
its licence declaration alone does not establish the original authors' grant.
OpenBMI's loader reads channel names, sampling rate, event classes and EMG from
source MATLAB structures; preserve them before array conversion. The relevant
[loader](https://github.com/NeuroTechX/moabb/blob/develop/moabb/datasets/Lee2019.py)
points to [GigaDB 100542](https://doi.org/10.5524/100542). GigaDB's
[host policy](https://gigadb.org/term) supports CC0 unless otherwise specified,
but individual files still need checking. Kaneshiro's loader reconstructs
artificial continuous data from original epochs, so use original trial indices
and avoid interpreting synthetic sample offsets as acquisition times.
Sources: [Kaneshiro loader](https://github.com/NeuroTechX/moabb/blob/develop/moabb/datasets/kaneshiro2015.py),
[Wang loader](https://github.com/NeuroTechX/moabb/blob/develop/moabb/datasets/ssvep_wang.py).

The documentation's Sosulski "80 sessions" groups task conditions/files and must
not be reported as 80 acquisition visits. Huebner's block sessions and Cattan's
PC/VR grouping likewise need explicit original-session interpretation. Candidate
recording independence is provisional until file/event identity checks; shared
cohort, separate task and alternate labels remain separate provenance fields.

## Smaller candidates, 5 November 2026

A second survey prioritised small multichannel problems, allowing restricted
research licences. These sources are absent from the current registry; source
recording independence still needs confirmation during admission. No EEG files
were downloaded. Counts below are nominal documentation/protocol counts, not
validated exports. Size is for all cases across both partitions.

| Candidate | Task | Subjects / sessions per person | EEG channels | Nominal cases | Points per case used for estimate | Float64 GB | Estimated .ts GB |
|---|---|---|---:|---:|---:|---:|---:|
| [Nakanishi2015](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Nakanishi2015.html) | Attend one of 12 flickering targets | 10 / 1 | 8 | 1800 | 1114 native samples at 256 Hz | 0.128 | 0.26?0.38 |
| [BCI IV 2b / BNCI2014_004](https://moabb.neurotechx.com/docs/generated/moabb.datasets.BNCI2014_004.html) | Imagined left/right hand movement | 9 / 5 | 3 | about 6500 | about 1125 for a 4.5-second epoch at 250 Hz | 0.176 | 0.35?0.53 |
| [BNCI2015_003](https://moabb.neurotechx.com/docs/generated/moabb.datasets.BNCI2015_003.html) | Attended/unattended visual speller flashes | 10 / 1, two runs | 8 | about 18000 | about 205 for 0.8 seconds at 256 Hz | 0.236 | 0.47?0.71 |
| [Zhou2016](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Zhou2016.html) | Imagined left hand, right hand or feet | 4 / 3 | 14 | 1800 | 1250 for five seconds at 250 Hz | 0.252 | 0.50?0.76 |
| [ALS P300 / BNCI2014_008](https://moabb.neurotechx.com/docs/generated/moabb.datasets.BNCI2014_008.html) | Attended/unattended speller flashes in ALS patients | 8 / 1 | 8 | 33600 | about 256 for one second at 256 Hz | 0.551 | 1.10?1.65 |
| [BNCI2014_002](https://moabb.neurotechx.com/docs/generated/moabb.datasets.BNCI2014_002.html) | Imagined right hand versus feet | 14 / 1 | 15 | 2240 | 2560 for five seconds at 512 Hz | 0.688 | 1.38?2.06 |

Float64 memory is calculated as cases ? EEG channels ? points ? 8 bytes.
Decimal .ts text is provisionally estimated at 2?3 times that size; these are
not measured downloads or exported file sizes. Raw recordings, temporary cache,
metadata and peak classifier memory are additional. Endpoint conventions can
add one sample; artifact policy can alter case totals. These estimates do not
silently introduce resampling or float32 conversion. Native Nakanishi epochs
are retained in its estimate; other rows illustrate the stated task epochs.

**Recommended next inspections:** Nakanishi2015 for the smallest footprint and
12 classes; BCI IV 2b for five sessions and three EEG derivations; ALS P300 for
a new clinical cohort. ALS P300 predicts attention, not ALS diagnosis. Zhou2016
is another small three-class, repeated-session collection, but only four people
limit subject-disjoint evaluation. BNCI2015_003 is a compact healthy-participant
speller alternative. These are source-study candidates, not additional binary
views of our existing problems.

### Source and metadata qualifications

- Nakanishi's [author release](https://github.com/mnakanishi/12JFPM_SSVEP)
  explicitly specifies 12 ? 8 ? 1114 ? 15 per person and ten people. MOABB marks
  the licence Unknown; public availability is not a redistribution grant. Earlier
  MOABB versions exposed only nine participants. Recover the original frequency
  order and 39th-sample stimulation onset, rather than accepting synthetic Raw
  offsets as acquisition timestamps.
- The [original BNCI publisher](https://bnci-horizon-2020.eu/database/data-sets)
  supplies direct downloads: BCI IV 2b and BNCI2014_002 are CC BY-ND 4.0;
  BNCI2015_003 and ALS P300 are CC BY-NC-ND 4.0. These are reasonable candidates
  for local noncommercial research with source terms retained; sharing an
  adapted processed release needs separate consideration.
- BCI IV 2b is a separate dataset from our BCI IV 2a preparation. Its three
  EEG channels are bipolar derivations C3/Cz/C4; three auxiliary EOG channels
  must remain distinct and are excluded from the EEG-only size estimate.
  The [original description](https://bnci-horizon-2020.eu/database/data-sets/004-2014/description.pdf)
  describes screening and feedback recordings. Final counts need checking:
  nominal protocol arithmetic gives 6480, while MOABB's metadata lists 6520.
- ALS P300's [original description](https://bnci-horizon-2020.eu/database/data-sets/008-2014/description.pdf)
  supports 35 character selections ? 120 flashes = 4200 events/person, before
  conversion/boundary exclusions. Actual original sensor names, reference and
  demographics are available; the original PDF should take precedence over
  conflicting headline demographic/reference text on the generated page.
- **Deprioritise BNCI2014_002 for now:** its
  [current loader](https://github.com/NeuroTechX/moabb/blob/develop/moabb/datasets/bnci/bnci_2014.py)
  explicitly invents an approximate standard electrode-name mapping for 15
  unlabeled source columns. Exact physical channel order is undocumented. That
  conflicts with our requirement to recover true sensor identities rather than
  manufacture them; preserve anonymous axes and flag the gap if reconsidered.

## What MOABB provides

MOABB provides dataset loaders, processing paradigms and evaluation procedures,
rather than one fixed archive of classification arrays. Loaders expose MNE
recordings; the chosen paradigm determines channels, filtering, epoching and
labels. Within-session, cross-session and cross-subject evaluations answer
different questions. They do not define one universal TRAIN/TEST partition.
See the [documentation overview](https://moabb.neurotechx.com/docs/index.html).

| Task family | Classification question | Value to our archive |
|---|---|---|
| Motor imagery | Which movement is imagined, sometimes including rest? | More independent studies and richer movement vocabularies. |
| P300 / ERP | Which event or stimulus condition produced an epoch? | Visual/auditory attention, oddball responses and cognitive tasks. |
| SSVEP | Which periodic visual target is being attended? | A distinct task family, often with several or many targets. |
| c-VEP | Which code-modulated visual response or code state is present? | Another distinct visual-response family; epoch versus whole-trial targets need explicit definition. |
| Cognitive / speech imagery | Which mental or imagined speech task is performed? | Broader tasks, with some sources already represented here. |
| Resting state | Depends on the dataset and supplied annotations | Review the scientific target; creating arbitrary windows does not establish a useful classification problem. |

These are review categories, not a claim that every MOABB class under a category
has the same experimental design. In particular, an entry tagged Imagery can
include executed movements or non-motor tasks.

## Dataset counts are not study counts

At review time the homepage advertised **158 datasets**, while the data-summary
page displayed **206 entries** and 4,500 participants. Its displayed family counts
were Imagery 104, P300/ERP 70, SSVEP 18, c-VEP 8 and Resting State 3; these total
203, not 206. The live pages are not internally consistent enough to use these
numbers as a verified inventory of independent studies.
Sources: [homepage](https://moabb.neurotechx.com/docs/index.html),
[summary](https://moabb.neurotechx.com/docs/dataset_summary.html).

The number of studies with unique recordings remains **unestablished** by this
review. Deduplication must operate on original accessions and recording/trial
identities. There are several different relationships:

- A different label subset or sampling rate can reuse exactly the same recordings.
- An aggregate loader can contain recordings also exposed by its subset loaders.
- One study can contain separate experiments with different recordings but the
  same participants. Those are not automatically duplicate signals.
- Separate studies can use the same left/right imagery labels while contributing
  independent recordings. Identical task names do not establish source overlap.

For a concrete aggregate example, [Dreyer2023](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Dreyer2023.html)
concatenates Dreyer2023A, B and C. Counting the aggregate and all three components
as four independent collections would duplicate their data. Likewise, compound
loaders and participant subsets need to be traced back to their members.

## Sources already represented in EEGBench

This table identifies source coverage, not equality of processed files. Additional
trials, classes or subjects in MOABB can be useful without constituting a new
independent study.

| MOABB entry | Our problem(s) | Relationship / next action |
|---|---|---|
| AlexMI | ImaginedRightHandFeet | Same source. Our preparation retains right hand and feet; the source also contains Rest. Rest would extend the task, not add a study. |
| BNCI2014_001 | ImaginedHandFeetTongue | Same BCI Competition IV 2a collection; retain its source licence caveat. |
| PhysionetMI | FeetHands, ImaginedFeetHands, OpenCloseFist, ImaginedOpenCloseFist | Same PhysioNet EEG Motor Movement/Imagery Database. Multi-class views reuse this source family. Compare exact run/trial selection before claiming identical cases. |
| Weibo2014 | ImaginedLeftRightHand | Same seven-class source collection; our preparation retains only left/right hand imagery. Other source classes could extend coverage. |
| Peterson2020 | LowCost | Same OpenNeuro ds003810 source, despite the different year/name. Useful for recovering missing identities and checking run/session interpretation. |
| TrianaGuzman2024 | SitStand | Same OpenNeuro ds005342 study. MOABB documents offline/online phases and imagery/idle events; compare our selection before replacement. |
| Nieto2022 | InnerSpeech, PronouncedSpeech, VisualSpeech | Same OpenNeuro ds003626 collection. MOABB exposes condition/direction labels and three sessions; useful for metadata recovery or a documented fuller preparation. |

The first four mappings follow our [existing source audit](docs/dataset-provenance.md)
and [local dataset descriptions](docs/datasets.md).
The latter three are directly corroborated by the MOABB documentation for
[Peterson2020](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Peterson2020.html),
[TrianaGuzman2024](https://moabb.neurotechx.com/docs/generated/moabb.datasets.TrianaGuzman2024.html)
and [Nieto2022](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Nieto2022.html).

Peterson2020 is described as **one session with four task runs**. We should not
count those four runs as four repeat acquisition sessions without original-source
evidence. Nieto2022's page also mixes a 12-condition/direction snapshot with a
four-class summary, so exact event selection needs to be recorded explicitly.
These are reasons to inspect the files and loader, rather than copy headline counts.

## Candidates for new recording collections

The following numbers describe the documentation's source/loader metadata, not
validated final exports. EEG counts exclude additional sensor channels where the
page distinguishes them. Frequencies are those exposed by the documented loader
or release; they are not necessarily the original acquisition frequency.

For unprepared candidates, the licence column reports **MOABB's declaration only**.
Verify the original data record and its applicability to processed-data
redistribution before downloading for publication. Prepared entries link reports
of the original licence checks. Names for unprepared candidates remain proposals.

| Candidate and documentation | Task | Subjects | EEG channels | Hz | Sessions / design | Declared licence | Suggested name / reason |
|---|---|---:|---:|---:|---|---|---|
| [BI2014a](https://moabb.neurotechx.com/docs/generated/moabb.datasets.BI2014a.html) | Visual P300 target/non-target | 64 distributed | 16 | 512 | One loader session per person | CC BY 4.0 | User-selected archive name: VisualSubjects. See [source preparation](docs/moabb-preparations.md). |
| [Kalunga2016](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Kalunga2016.html) | Attend 13, 17 or 21 Hz LEDs, or rest | 12 | 8 | 256 | One loader session; repeated recordings recovered | CC BY 4.0 | Prepared as FlickerAttention; see [source audit](docs/kalunga-preparation.md). |
| [Wang2016](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Wang2016.html) | Forty visual speller targets with frequency/phase modulation | 35 | 64 | 250 | One session, six blocks | CC BY 4.0 | FlickerSymbols; richer SSVEP task, not forty separate datasets. |
| [Thielen2021](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Thielen2021.html) | Code-modulated visual speller | 30 | 8 | 512 | One session | Original CC0 1.0 verified | Prepared as CodedSymbols: 20 targets, full nominal 31.5-second raw trials. First-sensor naming conflict flagged; see [report](docs/coded-symbols-preparation.md). |
| [Thielen2015](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Thielen2015.html) | Code-modulated visual speller | 12 | 64 | 2048 | One session | CC0 1.0 | Alternative c-VEP study; 36 symbol targets, high acquisition rate and larger arrays. |
| [ErpCore2021_N400](https://moabb.neurotechx.com/docs/generated/moabb.datasets.ErpCore2021_N400.html) | Semantically related/unrelated visually presented word pairs | 40 | 30 | 1024 | One recording per person | Original LICENSE: CC BY-SA 4.0, conflicting declarations documented | Prepared as WordRelatedness; see [source and label audit](docs/word-relatedness-preparation.md). |
| [Cho2017](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Cho2017.html) | Imagined left/right hand | 52 | 64 | 512 | One session | CC BY 4.0 | Another independent hand-imagery study; also supplies EMG and electrode-location information. A final name must distinguish it from ImaginedLeftRightHand. |
| [Lee2019_MI](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Lee2019_MI.html) | Imagined left/right grasping | 54 | 62 | 1000 | Two sessions | CC0 1.0 | OpenBMI hand imagery; useful for repeat-session evaluation. |
| [Ofner2017](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Ofner2017.html) | Six right upper-limb movements plus rest | 15 | 61 | 512 | Executed movements on day 1; imagined on day 2 | CC BY 4.0 | Prepared as ArmMovements and ImaginedArmMovements; same cohort, different recordings. See [conversion report](docs/ofner-preparations.md). |
| [Shin2017B](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Shin2017B.html) | Subtraction/rest | 29 | 30 | 200 | Three sessions | GPL 3.0 | MentalSubtraction; different source from MentalArithmetic. Original agreement needs review; loader has an acceptance parameter. |
| [Shin2017A](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Shin2017A.html) | Imagined left/right hand | 29 | 30 | 200 | Three sessions | GPL 3.0 | Hybrid EEG/NIRS study's imagery experiment. Same source study as Shin2017B; establish which recording files/segments each uses. |

BI2014a recruited 71 people but distributes 64; the loader exposes one session even
though game sessions occurred within acquisition. Kalunga2016's overview and
summary tables give different trial/window durations, so no final timepoint count
is proposed here. Wang2016 was acquired at 1000 Hz, while the distributed data are
documented at 250 Hz; preserve both. Thielen2021 uses custom sensor locations;
retain the actual array order rather than assuming a standard eight-channel cap.
These details are documented on their linked dataset pages.

## Useful additional families to inspect later

The [catalogue](https://moabb.neurotechx.com/docs/dataset_summary.html) also lists
Brain Invaders cohorts, additional ERP CORE components, mobile BCI experiments,
longitudinal motor imagery, clinical participants and further SSVEP/c-VEP studies.
Their presence makes this a much larger expansion opportunity than OpenEEGBench.
This review does not establish original redistribution permission or recording
independence for those additional entries.

OpenBMI's Lee2019 MI, ERP and SSVEP entries belong to one study, but different
experimental recordings can support separate problems. ERP CORE describes six
experiments measuring seven components: its seven component loaders cannot be
assumed to be seven disjoint recording collections. Preserve a common source-study
identifier and compare recording/epoch boundaries before choosing entries.
Sources: [Lee2019](https://moabb.neurotechx.com/docs/generated/moabb.datasets.Lee2019_MI.html),
[ERP CORE](https://moabb.neurotechx.com/docs/generated/moabb.datasets.ErpCore2021_N400.html).

## Task definitions and conversion considerations

MOABB does not automatically reduce every dataset to left versus right hand.
[LeftRightImagery](https://moabb.neurotechx.com/docs/generated/moabb.paradigms.LeftRightImagery.html)
is a particular paradigm; [MotorImagery](https://moabb.neurotechx.com/docs/generated/moabb.paradigms.MotorImagery.html)
supports multiple classes and explicit event selection. Store the original event
dictionary and selected classes. A binary view of a larger task is another
preparation of that source, not another independent recording collection.

[P300](https://moabb.neurotechx.com/docs/generated/moabb.paradigms.P300.html)
normally predicts target versus non-target epochs, not the identity of an entire
spelled character. Repetitions of one selection belong together when splitting
within a person. Preserve block, selection and stimulus IDs where available.

[CVEP](https://moabb.neurotechx.com/docs/generated/moabb.paradigms.CVEP.html)
normally predicts the target code's intensity at individual stimulation epochs.
This is different from predicting which of 20 or 36 symbols was attended over a
whole trial. An archive entry must state its target and epoch boundaries; nearby
code epochs can overlap and must not be randomly scattered across train/test.

For future assimilation:

1. Pin the MOABB release/commit, loader parameters and original data versions.
   The reviewed homepage cites version 1.7.1, but these live documentation pages
   should not be treated as an immutable release snapshot.
2. Trace each loader to the original accession, papers, data licence and files.
   Record source-study, recording and task-view identities separately. Verify
   declared licences at the original host; software licensing alone is insufficient.
3. Prefer new recording collections and retain all scientifically relevant classes
   unless a reduced task is explicitly chosen. Check auxiliary sensors and recover
   channel names/order, types, montage and reference from actual MNE/file metadata.
4. Specify preprocessing explicitly. For example, MotorImagery currently documents
   an 8-32 Hz default bandpass; that is an analysis choice, not untouched source EEG.
   Record original and processed frequencies, units, references and epoch offsets.
5. Use a fixed, documented subject-disjoint split where appropriate. For intentional
   cross-session or run-based tasks, declare the different split unit. No separate
   archived validation set: merge a supplied train/validation protocol where one
   exists; otherwise define our own reproducible training/test membership.
6. Recover case identifiers before converting MNE epochs to arrays. Preserve raw
   recording identity, original event sample/code, session/run strings, epoch
   selection/drop information and crop intervals alongside labels. Library
   subject/session/run metadata alone may not identify the original trial.
7. Export the existing `.ts` plus sidecar layout to a configurable local directory.
   Validate shape, class counts, channel order, case alignment, group overlap,
   duplicate signals and overlapping recording intervals across partitions;
   check aeon loading and classifier compatibility.

## Suggested order

**BI2014a, Kalunga2016, ERP CORE N400, Ofner2017 and Thielen2021** have now been
prepared; Ofner contributes both execution and imagination problems, and Thielen
contributes the 20-target offline task. The remaining initial shortlist includes
**Lee2019_MI or Cho2017** for a larger independent hand-imagery cohort and
**Wang2016** for a 40-target visual task.
Treat Shin2017 as a separate licence/access review rather than assuming its
declaration is sufficient.

This ordering is our recommendation based on task diversity and the documented
structures, not a claim that those sources have already passed archive admission.
Keep existing benchmark results unchanged while any additions are prepared.
For the narrower OpenEEGBench assessment, see [OpenEEGBench.md](OpenEEGBench.md).

FlickerSymbols (Wang2016) was subsequently prepared with all 35 participants,
6240/2160 subject-disjoint cases, 64 ? 1500 native epochs at 250 Hz and 40 classes.
The registry now contains 48 problems. See [source and validation report](docs/flicker-symbols-preparation.md).

## Six compact preparations completed

FlickerTargets (Nakanishi2015), ImaginedHandSides (BCI IV 2b), SpellerFlashes
(BNCI2015_003), ImaginedHandsFeet (Zhou2016), ALSAttention (BNCI2014_008)
and WirelessFlicker (MAMEM3) are now prepared in `D:/Data/EEG/`. Every case has
a subject ID. Original session/run splits are preserved where supplied; other
splits are subject-disjoint. Zhou Fp2 is removed globally after three saturated
constant windows. See [counts, source terms and complete provenance](docs/small-moabb-preparations.md).

The registry now contains 54 problems. The user-selected `eeg.txt` contains 50,
excluding Blink, ButtonPress, EpilepticSeizures and Sleep without deleting their
local files or historical registry entries.


## Follow-on source checks, 6 November 2026

**WalkingTargets** is prepared from BCIComp2020WalkingERP; see [the conversion report](docs/walking-targets-preparation.md). **SymbolAttention / Chailloux2020** has now been prepared following a successful two-subject pilot. Its original OpenNeuro release is CC0; source label omissions and BIDS metadata discrepancies are documented [here](docs/symbol-attention-preparation.md).

The earlier sensor-identity question for **VisualCategories / Kaneshiro2015** has been resolved at the documentation level. The original README, version 2.0.0, explicitly identifies the array electrode dimension as EGI HydroCel 128 sensors 1-124, in order. Stanford's original XML specifies **CC BY 3.0**. Native MAT variables and per-case metadata still require inspection before conversion; no EEG MATs have been downloaded in this follow-on check. [Original README](https://stacks.stanford.edu/file/bq914sc3730/Kaneshiro_etAl_objectCategoryEEG_README.pdf), [captured source metadata](docs/source-evidence/kaneshiro-stanford.xml).

**Kueper2024** is a further compact candidate: distinguish executed right-arm-only versus both-arm reaching, two classes. The original Zenodo record declares CC BY 4.0; its pinned source zip is 3.101 GB. The loader uses movement-onset epochs from -2 to +1 seconds at 500 Hz. Actual native channel roles, subject metadata and marker counts remain to be checked. [Original record](https://zenodo.org/records/10229480), [captured licence metadata](docs/source-evidence/kueper-zenodo-10229480.json).

**BNCI2003_004** refers to BCI Competition III IVa (2005), despite its MOABB name. The competition supplies right-hand versus right-foot imagination, not a third left-hand class. It is small, but the original pages inspected do not establish the loader's CC BY 4.0 claim; keep that licence status unresolved. [Original description](https://www.bbci.de/competition/iii/desc_IVa.html).

Machine-readable source checks: [next-candidate-source-inspection.json](docs/next-candidate-source-inspection.json). These follow-on checks downloaded metadata/documentation only; EEG sources for those three candidates remain pending.


**VisualCategories native-data update:** the sensor correspondence is documented, but S1 contains four exact duplicate epoch pairs with different exemplar labels; one pair also has conflicting category labels. Conversion is deferred, with [native evidence](docs/visual-categories-preparation.md). It has not been added to the archive. Kueper2024 was subsequently prepared as ArmCoordination; see completed preparations below.


**Completed follow-on preparations (6 November 2026):** SymbolAttention and ArmCoordination passed full conversion/validation and are now registered. Current collection: 66 registered / 62 selected problems. VisualCategories remains deferred with source-label evidence. See [dataset descriptions](docs/datasets.md) and [machine progress](docs/assimilation-progress.json).
