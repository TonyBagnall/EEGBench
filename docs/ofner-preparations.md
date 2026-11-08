# Ofner2017: ArmMovements and ImaginedArmMovements

These two problems classify six right upper-limb movements and rest. **ArmMovements**
uses executed movements; **ImaginedArmMovements** uses imagination. They are different
recordings from the same study and participants, rather than independent cohorts.
Each problem retains all seven original classes.

The original release is [Zenodo 834976, v1](https://doi.org/10.5281/zenodo.834976),
by Patrick Ofner, Andreas Schwarz, Joana Pereira and Gernot Müller-Putz. Its data
licence is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), permitting
redistribution with attribution and identification of modifications. The paper is
[*Upper limb movements can be decoded from the time-domain of low-frequency EEG*](https://doi.org/10.1371/journal.pone.0182578),
PLOS ONE (2017). Data licensing is established from the original record, separately
from the MOABB software licence.

## Local results

Both exports are complete in `D:/Data/EEG/`. Sizes include `.ts` files and sidecars,
in decimal GB. The [machine-readable results](ofner-local-results.json) contain
the full validation summaries and native subject-ID audit.

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---|---|---|---|---|---|---|---|---|
| ArmMovements | 4620 | 1680 | 15 | 61 | 1536 | 7 | 512 | 6.882 | CC-BY-4.0 |
| ImaginedArmMovements | 4620 | 1680 | 15 | 61 | 1536 | 7 | 512 | 6.911 | CC-BY-4.0 |

All 12,600 cases passed exact float32 numeric readback, label/count/order checks,
metadata alignment and sensor-order checks. There are no duplicate cases within
either partition, across train/test, or across the two tasks. The native subject
headers contain no identifier shared by different filename participants, and both
tasks use the same subject split. Representative `.ts` loading and aeon classifier
checks passed for every class; full numeric checking covers all cases.

The source has nonfinite EEG outside the selected windows in 138/150 execution
and 142/150 imagination recordings. Every exported window is complete and finite;
no sample is imputed. Ten execution recordings use the publisher-documented
generic EEG-name mapping; all other EEG names agree directly with the expected order.

The initial two-person, one-run pilot passed for both tasks before full conversion.
Its temporary exports and the 27.336 GB of original GDF downloads have been removed
after validation; source metadata, checksums and attribution remain. The final
datasets occupy approximately 13.794 GB together. A complete problem loaded into
float64 numeric arrays needs approximately 4.722 GB, excluding loader overhead.

## Protocol and representation

The original study has 15 healthy participants, with execution on day 1 and
imagination on day 2, within a week. Each day has ten runs, each with 42 trials:
six trials for each class. Thus each problem has one session per participant,
150 recordings and 6,300 cases. The study has two sessions per participant across
the two problems; these are not two repeat imagery sessions.

| Encoded label | Original GDF code | Task |
|---|---|---|
| 0 | 1536 | Elbow flexion |
| 1 | 1537 | Elbow extension |
| 2 | 1538 | Forearm supination |
| 3 | 1539 | Forearm pronation |
| 4 | 1540 | Hand closing |
| 5 | 1541 | Hand opening |
| 6 | 1542 | Rest |

Original class annotations mark the class cue, two seconds after fixation onset.
We extract **[cue, cue + 3 seconds)**: 1,536 timepoints at the original 512 Hz.
There is no added filter, resampling, baseline correction, reference change or
amplitude scaling. Arrays use float32; nine significant digits in `.ts` preserve
every float32 sample exactly on numeric readback.

Both problems use the same locally defined split: participants `01`–`11` train,
`12`–`15` test. Each has 4,620 training and 1,680 test cases, respectively 660 and
240 cases per class. The source has no official train/test protocol. There is no
validation partition. Ordering is numeric participant, numeric run, then original
class-event order. Identifiers in TSV files must be read as strings.

## Sensors and evidence

The source description's Table 2 specifies 61 EEG, three EOG, 19 glove and 13
exoskeleton channels. Only the original first 61 EEG axes are exported. Their
array order is:

```text
F3 F1 Fz F2 F4 FFC5h FFC3h FFC1h FFC2h FFC4h FFC6h
FC5 FC3 FC1 FCz FC2 FC4 FC6 FTT7h FCC5h FCC3h FCC1h
FCC2h FCC4h FCC6h FTT8h C5 C3 C1 Cz C2 C4 C6 TTP7h
CCP5h CCP3h CCP1h CCP2h CCP4h CCP6h TTP8h CP5 CP3 CP1
CPz CP2 CP4 CP6 CPP5h CPP3h CPP1h CPP2h CPP4h CPP6h
P3 P1 Pz P2 P4 PPO1h PPO2h
```

Participant 1's execution files use generic `eeg-0`–`eeg-60` labels. These are
mapped by the original Table 2, without moving data axes. Every recording is
checked against the expected native order; an unexpected order fails conversion.
Auxiliary EOG order can differ and imagination can contain exoskeleton dummy
channels. Native names and types are retained per recording; auxiliary signals
are excluded, with no replacement of missing values by zeros.

The publication/source PDF describes a right-mastoid reference, AFz ground and
acquisition filters (eighth-order Chebyshev 0.01–200 Hz, 50 Hz notch). These facts
are labelled as publication evidence. Native GDF filter, reference/ground and
sensor-location fields are preserved separately. Zero or absent coordinates are
not presented as individually measured electrode positions.

GDF physical units are ambiguous: the reader reports unspecified dimensions and
MOABB interprets the numeric values as microvolts. We preserve the GDF reader's
numeric scale and record this limitation, rather than silently applying MOABB's
`1e-6` multiplier. Native subject headers and dates are retained; filename IDs
define participants because native subject strings can differ within and between
sessions and some birthday fields are invalid. For example, execution participant
`01` has native IDs `xyz` and `cc2` across runs. These are preserved as header
aliases, not counted as two participants.

Some source recordings contain nonfinite EEG padding at the end. Counts and
locations are retained in recording metadata. Every selected epoch must be
complete and finite; the converter fails if padding enters a retained window.

## Reproduction and files

```powershell
python -m tools.prepare_ofner --mode both --cache D:/Data/EEGSources/Ofner2017 --output D:/Data/EEG
```

Install the standalone environment with
`python -m pip install -r tools/requirements-moabb.txt`.
Requires MNE 1.13.2, NumPy, pandas, SciPy and aeon 1.5.0. Older MNE GDF readers
can be incompatible with NumPy 2. `--subjects`, `--train-subjects`, `--runs` and
`--output` support small pilots; `--download-only` and `--offline` separate transfer
from conversion. Existing destination datasets are never overwritten.

The pinned MOABB loader revision is
`bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`, `moabb/datasets/upper_limb.py`.
The faster original-file mirror is `nemarDatasets/nm000173` at
`74b85c0854dfd31339209db41010633ac92a7852`, using immutable SHA256 annex objects.
Every mirrored GDF must match both the original Zenodo MD5/size and the pinned
mirror SHA256. The mirror's BIDS derivatives are not used. The 300 original GDF
files total 27.336 GB and are temporary download inputs, separate from final `.ts`.

Each `D:/Data/EEG/<problem>/` contains:

- `<problem>_TRAIN.ts` and `<problem>_TEST.ts`, compatible with aeon multivariate
  classification (`case, channel, time` when loaded).
- `cases_train.tsv` and `cases_test.tsv` in exact array order, with participant,
  native subject ID, session/task/date, run, recording, original annotation/trial,
  original GDF event index and one-based sample, original/encoded label,
  zero-based window sample/time bounds and float32 signal hash.
- `<problem>_metadata.json`, `<problem>_manifest.json`, validation report,
  `channels.tsv`, `recordings.json` and `metadata-completeness.json`.
- `source_metadata/`, including compact per-recording native headers and all
  annotations, original licence record/PDF, pinned loader and mirror provenance.
  The compact GDF event header is MNE-parsed: its position vector is zero-based
  because MNE subtracts one from the on-disk GDF positions. Both conventions are
  explicit in case metadata.
- Attribution and conversion code. `cross-task-audit.json` compares exact signals
  across the execution and imagination problems, while noting their shared cohort.

Validation checks all cases, labels, counts, source order, metadata alignment,
channel order, subject separation, finite epochs, within-partition duplicates,
cross-partition duplicates and exact numeric `.ts` readback. An aeon
`SummaryClassifier` fit/predict check uses representative cases of all seven
classes after loading `.ts`; it does not generate benchmark scores.

| Metadata | Availability |
|---|---|
| Participant, session and run | Filename/protocol IDs; native subject strings and dates also retained |
| Original trial/event | Class-event sequence, full annotation index/code/time and raw GDF event header |
| Window bounds | Original recording samples, zero-based, end exclusive |
| Labels | Original GDF codes, encoded 0–6 and class descriptions |
| Sensors | Exact EEG order; per-recording native names/types for all 96 sensors |
| Positions/reference | Native header fields retained; publication reference/ground separate; verified individual positions unavailable |
| Filtering/frequency | Native headers plus labelled publication evidence; 512 Hz unchanged |
| Units | Original header ambiguity explicitly retained; no amplitude scaling |
| Demographics | Study aggregates in publication; individual native fields not assumed reliable |

Large inputs and generated arrays remain outside Git. No archive upload is made.
