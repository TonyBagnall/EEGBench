# MOABB source preparations

These standalone tools prepare original datasets identified through MOABB as
standard multivariate `.ts` classification problems with ordered metadata sidecars.
They are separate from the leaderboard and experiment infrastructure. Dataset
licences come from original data records, not the MOABB software licence.

[FlickerAttention / Kalunga2016](kalunga-preparation.md) is also prepared locally:
576 training / 352 test cases, 12 participant IDs, 29 distinct recordings and
four classes. Its source duplicate, calibration and geometry findings are
documented separately; [machine-readable validation](kalunga-local-results.json)
includes the 0.055 GB final size.

[WordRelatedness / ERP CORE N400](word-relatedness-preparation.md) adds 40 participants
and 3,600 training / 1,200 test cases, with two semantic-relatedness classes, 30 EEG
channels and 1,024 points at 1,024 Hz. Original data are retained under CC BY-SA 4.0;
the [validation report](word-relatedness-local-results.json) records source and
metadata checks.

## VisualSubjects: Brain Invaders 2014a

**VisualSubjects** is the archive name chosen for **BI2014a**, also called
BrainInvaders2014a, bi2014a and BI.EEG.2014a-GIPSA. The related NEMAR identifier is
`nm000244`. The classification target is whether a visual flash included the
attended target, with original codes **1 = NonTarget, 2 = Target**.

The original data are pinned to [Zenodo record 3266223, v1](https://zenodo.org/records/3266223),
DOI [10.5281/zenodo.3266223](https://doi.org/10.5281/zenodo.3266223).
The concept DOI is 10.5281/zenodo.3266222. Authors: Louis Korczowski, Ekaterina
Ostaschenko, Anton Andreev, Gregoire Cattan, Pedro Luis Coelho Rodrigues,
Violette Gautheret and Marco Congedo (2019). The associated description is
[Brain Invaders calibration-less P300-based BCI using dry EEG electrodes Dataset](https://hal.science/hal-02171575).
The [original record metadata](https://zenodo.org/api/records/3266223) explicitly
declares **CC BY 4.0 for the dataset**. The export retains attribution, data DOI,
licence link and a description of conversion changes.

### Subjects, recordings and task

The release distributes 64 participant archives, `subject_01.zip` through
`subject_64.zip`. Each contains a MAT and CSV representation. We use the MAT
`samples` array; the CSV representation rounds signal values more heavily.
The source description reports 71 recruited participants; MOABB explains that
the remaining seven were not distributed because of tagging problems or aborted
experiments. No extra participant exclusions are introduced here.

Participants attended target symbols in a visual P300 Brain Invaders game. A
flash can include or exclude the target symbol. The two-class label is taken
directly from the source `Target` column, not inferred from participant identity
or from the other `Event` column. The latter is preserved separately, without
unverified decoding of its game-condition codes.

Each participant has one distributed continuous recording. MOABB exposes this
as session `0`, run `0`; the source describes up to three game sessions within
acquisition. Physical session boundaries have not been recovered. Case tables
therefore keep physical `session_id` and `run_id` blank and put the software
identifiers in separate `loader_session_id` and `loader_run_id` columns.

### Channels and discrepancy with loader aliases

The original global `Header.csv` declares the following EEG array order:

```text
Fp1, Fp2, F5, AFZ, F6, T7, Cz, T8, P7, P3, PZ, P4, P8, O1, Oz, O2
```

The MAT matrix has columns Time, sixteen EEG values, Event and Target. Every
recording is checked against that 19-column schema and the 512 Hz timebase.
The shared header supplies names for all files; there are no independent
per-participant sensor-name arrays to compare. No channels are reordered.

**Important source conflict:** both the inspected MOABB loader and original
author loader assign **F3/F4** at the positions the distributed header calls
**F5/F6**. The export uses the original header, retaining its AFZ/PZ capitalization.
The sidecars retain the conflicting loader aliases and pinned code evidence.
This establishes which names were used; it does not independently verify the
physical cap wiring. The 16 signal channels are described as EEG; Time, Event and
Target are metadata, not classifier input channels.

Individual sensor positions are unavailable. The layout/reference/hardware
descriptions come from publication/loader evidence, not from the numeric MAT
matrix. Reference: right earlobe; acquisition: dry g.Sahara electrodes and g.USBamp.
Signal scale is retained in source microvolt units, consistent with MOABB's
documented multiplication by 1e-6 when constructing MNE recordings in volts.

The inspected source loaders are pinned to:

- MOABB: `bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`,
  [braininvaders.py](https://github.com/NeuroTechX/moabb/blob/bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5/moabb/datasets/braininvaders.py).
- Original author: `15d9ddd1a9322cce2b70b2a9ba41485047262ddd`,
  [dataset.py](https://github.com/plcrodrigues/py.BI.EEG.2014a-GIPSA/blob/15d9ddd1a9322cce2b70b2a9ba41485047262ddd/braininvaders2014a/dataset.py).

The converter reads the original files directly. It does not execute those
loaders or inherit their channel aliases, analysis filters or label encoders.

### Epochs and fixed split

Each case has **16 channels by 512 timepoints**, a one-second epoch at **512 Hz**.
Onsets are nonzero target-marker transitions; a held pulse produces one onset.
Epoch bounds are `[onset_sample, onset_sample + 512)`, with an exclusive end.
This deliberately defines 512 samples, rather than relying on an inclusive
MNE endpoint that can produce 513 samples. Incomplete epochs at the recording end
are omitted and logged individually in `dropped-events.json`.

No filtering, baseline subtraction, artifact rejection, resampling, scaling or
reference change is added. Values are cast from the MAT float64 representation
to float32 and written with nine significant digits, permitting exact float32
readback. Maximum cast error in source units is recorded in the validation JSON.

The fixed EEGBench split is **subjects 01-48 for training and 49-64 for test**.
MOABB does not supply a universal fixed TRAIN/TEST split for this dataset; this
is our documented participant-level protocol. There is no separate archived
validation set. Order is ascending participant number, then original onset index.
Training and test share neither people nor source recordings. Epochs naturally
overlap within a recording; these stay in the same partition. The source target
and non-target classes are imbalanced; no balancing or subsampling is added.

### Files and validation

| Dataset | Train cases | Test cases | Subjects | EEG channels | Timepoints | Classes | Hz | Size GB | Licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| VisualSubjects | 42,189 | 18,826 | 64 | 16 | 512 | 2 | 512 | 5.815 | CC BY 4.0 |

Training class counts are 35,157 NonTarget / 7,032 Target; test counts are
15,688 NonTarget / 3,138 Target. These are recovered export counts, not estimates
from a headline trials-per-person figure.
Size includes final files and sidecars, in decimal GB. A
[machine-readable report](moabb-local-results.json) records the validation and
metadata completeness. Full readback and aeon compatibility passed; no subjects,
source recordings or exact signal cases cross TRAIN/TEST. Seven incomplete
end-of-recording epochs were dropped and logged. Maximum float32 cast error was
approximately `5e-6` in source microvolt units.

The final destination is `D:/Data/EEG/VisualSubjects/`, containing:

- `VisualSubjects_TRAIN.ts` and `VisualSubjects_TEST.ts`.
- `cases_train.tsv`, `cases_test.tsv` and `VisualSubjects_rows.tsv`. Each per-split
  table exactly follows its cases; the combined table is TRAIN then TEST. `row`
  is zero-based within split. Read identifiers as strings to preserve leading zeros.
- Dataset metadata, validation JSON, a manifest with source and export hashes,
  `channels.txt`, `channels.tsv`, attribution and a local README.
- `recordings.json`, `dropped-events.json`, metadata completeness, source record,
  source channel header, pinned loader snapshots and conversion code.

Recovered case metadata include participant, source recording/archive/member,
zero-based onset-event index, original onset sample/time, exclusive end sample/time,
source Event code, original Target code, label description and the assigned split.
Onset-event IDs are local deterministic identifiers; original game block/selection
IDs are not claimed. Physical session/run IDs, per-person sensor positions and
individual demographic mappings remain unavailable.

Checks cover publisher MD5 checksums, source SHA-256 hashes, source timebase and
schema, shapes/class counts, stable channel-axis order, subject and recording
separation, exact duplicate signals across partitions, all metadata rows and
exact float32 hashes on full `.ts` readback. Representative cases from both
classes are loaded with aeon and used to fit/predict with SummaryClassifier.
This checks compatibility and adds no benchmark scores.

The first full-process pilot used subjects 01 and 02, with 01 for training and
02 for test. Its 1,188 / 492 cases passed numeric readback and aeon compatibility.
The pilot is an ignored local development artifact, not another archive problem.

### Reproduction

```powershell
# Original files and evidence remain in a configurable, ignored source cache.
python -m tools.prepare_moabb --dataset bi2014a --cache .openeegbench/bi2014a-source --output D:/Data/EEG

# A pilot in a separate destination; never overwrite the full archive folder.
python -m tools.prepare_moabb --subjects 1,2 --train-subjects 1 --output .openeegbench/bi2014a-pilot

# Reuse checksummed local sources without downloading.
python -m tools.prepare_moabb --offline --output D:/Data/EEG
```

The converter refuses to overwrite final output and publishes it only after
validation. Downloaded arrays and generated data are not committed to GitHub.
No upload to Zenodo is performed. See [MOABB review](../MOABB.md) for other
candidate source collections and [datasets](datasets.md) for the registry.
