# WordRelatedness: ERP CORE N400

WordRelatedness classifies **semantically related versus unrelated visual word
pairs**, using EEG epochs around the second (target) word. Source: Kappenman,
Farrens, Zhang, Stewart and Luck, *ERP CORE: An open resource for human event-related
potential research*, NeuroImage 225 (2021), 117465,
[DOI 10.1016/j.neuroimage.2020.117465](https://doi.org/10.1016/j.neuroimage.2020.117465).
The authors' data resource DOI is [10.18115/D5JW4R](https://doi.org/10.18115/D5JW4R).

## Recording provenance and licence

The converter reads the original [OSF N400 BIDS distribution](https://osf.io/29xpq/).
Its metadata identify the original BIDS collection as **OpenNeuro ds003068 v1.0.0**,
DOI 10.18112/openneuro.ds003068.v1.0.0. MOABB calls it `ErpCore2021_N400`; the
combined ERP CORE mirror is NEMAR `nm000132`. These are source aliases, not
independent studies. This is a different recording collection from our auditory
MEG MatchWords problem (OpenNeuro ds004276).

Original files are selected from MOABB's
[Zenodo download manifest](https://zenodo.org/records/14866307/files/erpcore_manifest.csv?download=1),
pinned by SHA-256:
`16ffd88374e29f121e7fd77cade429d25704526baac11ede027a484c50af5cff`.
Only the N400 component and its shared metadata are downloaded. All file sizes
and publisher MD5 values are checked; source SHA-256 values and URLs are retained.
The reviewed MOABB code is pinned to commit
`bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`.

**Use CC BY-SA 4.0 for this derivative.** Both the supplied original `LICENSE`
and [the authors' website](https://erpinfo.org/erp-core) explicitly require attribution
and share-alike. This conflicts with the raw BIDS JSON's CC0 declaration and some
mirror/MOABB CC BY metadata. We retain the explicit original licence, attribution
and conversion changes, and preserve the conflicting declarations as evidence.
This affects the EEG derivative; it does not change the repository's software
licence. No data are uploaded to Zenodo by this preparation.

## Subjects and task definition

The source contains **40 participants**, `sub-001` through `sub-040`, with one
continuous N400 recording each. Participant age, sex and handedness are recovered
from `participants.tsv`. Source IDs and three-digit archive IDs are strings.

The fixed EEGBench split is **001-030 training, 031-040 test**. It is locally
defined; MOABB does not provide a universal fixed TRAIN/TEST partition. There is
no separate validation split. Cases retain participant order, then original event
order. Physical named session/run IDs are absent. The EEGLAB `etc.T0` timestamp is
recovered where available and used transparently as a recording-session identifier,
with timezone unspecified. MOABB's `0/0` session/run identifiers are separate.

Original target-word codes and binary labels are:

| Original code | Meaning | Exported label |
|---|---|---:|
| 211 | Related pair, word list 1 | 1 |
| 212 | Related pair, word list 2 | 1 |
| 221 | Unrelated pair, word list 1 | 2 |
| 222 | Unrelated pair, word list 2 | 2 |

Prime-word codes 111/112/121/122 and response codes 201/202 are retained in the
source tables but do not produce classification cases. The case table retains
word-list ID, original target event row, original EEGLAB event/urevent identifiers,
preceding prime code/sample and subsequent response codes/samples. Responses are
associated only until the next prime or target marker. All target-word cases are
retained regardless of behavioral accuracy; multiple or missing responses remain
explicit. Actual word strings are not supplied by these event files (`stim_file`
is `n/a`), so they are not invented.

## Channels, units and positions

Each recording contains **30 EEG and three EOG channels**. The `.set` labels and
`channels.tsv` are checked against each other for every recording. Only EEG axes
are exported, without reordering:

```text
FP1, F3, F7, FC3, C3, C5, P3, P7, P9, PO7, PO3, O1, Oz, Pz, CPz,
FP2, Fz, F4, F8, FC4, FCz, Cz, C4, C6, P4, P8, P10, PO8, PO4, O2
```

The omitted EOG channels are HEOG_left, HEOG_right and VEOG_lower. All 33 source
sensor definitions remain in the sidecars. Distributed electrode positions and
their **millimetre units / ARS coordinate-system declaration** are retained
directly, with per-participant copies. No transformation to a different head
coordinate frame or claim of individual digitization is added.

The `.fdt` binary is little-endian float32, interleaving channels within each time
sample. Native numeric microvolt values are retained. An independent pilot check
against MNE's EEGLAB reader confirmed the orientation and its corresponding
microvolt-to-volt scaling exactly. The BIDS reference is CMS and EEGLAB says
`common`; both descriptions are retained. No new referencing is applied. Source
EEG JSON records the Biosemi ActiveTwo equipment and acquisition information.

## Epoch boundaries and event-index correction

Each case has **30 channels by 1,024 timepoints**, one second at the original
**1,024 Hz**. The intended interval is approximately [-0.2,0.8) seconds around the
recorded target marker, with an explicit half-open sample definition.

The original event TSV `sample` column contains **one-based EEGLAB latencies**.
This is verified against `.set` event latencies and the rounded onset column,
rather than assuming a zero-based convention from the BIDS column name. The
converter uses:

```text
event_sample_0based = source_sample_1based - 1
start_sample = event_sample_0based - 205
end_sample = start_sample + 1024  # exclusive
```

Thus the integer crop is [-205,819) samples relative to the recorded event,
approximately [-0.200195,0.799805) seconds. Original one-based latency, exact
zero-based index, rounded source onset and crop indices/times are all retained.
Original event/urevent IDs provide an additional link to the native recording.

No filtering, baseline correction, resampling, artifact rejection, amplitude
scaling or monitor-latency shift is added. The reviewed MOABB code mentions a
26 ms LCD delay; this preparation explicitly uses the original acquisition marker
alignment. Source float32 values are written with nine significant digits and
checked for exact float32 readback. Incomplete boundary epochs, if any, are logged
individually rather than padded.

## Files and validation

| Dataset | Train cases | Test cases | Participants | EEG channels | Points | Hz | Classes | Size GB | Licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| WordRelatedness | 3,600 | 1,200 | 40 | 30 | 1,024 | 1,024 | 2 | 1.729 | CC BY-SA 4.0 |

Each class has 1,800 training and 600 test cases. There were no incomplete
epochs to drop. Final size includes arrays and sidecars, in decimal GB.
The [machine-readable report](word-relatedness-local-results.json) records
validation and metadata completeness.

Final files use `D:/Data/EEG/WordRelatedness/WordRelatedness_TRAIN.ts` and
`WordRelatedness_TEST.ts`. `cases_train.tsv` and `cases_test.tsv` align exactly
with their respective cases. `WordRelatedness_rows.tsv` is TRAIN then TEST;
`row` is zero-based within each split. Read participant/session/run identifiers
as strings. Dataset metadata, sensor tables, licence/attribution, recording
metadata, original BIDS sidecars and compact EEGLAB header/event snapshots accompany
the arrays. Source `.set` and `.fdt` files stay in an ignored local cache; they
are represented by checksums in the final manifest.

Checks include source hashes/sizes, FDT schema, frequency, EEG/EOG order and units,
original event identity/sample base, label mapping, shapes/class counts,
subject separation, cross-partition duplicate signals, ordered metadata rows and
every case's exact float32 readback. Representative examples of both classes are
loaded with aeon and used to fit/predict with SummaryClassifier. This adds no
benchmark scores. A full two-person pilot passed with 120 cases per participant
before processing all forty participants.

```powershell
python -m tools.prepare_moabb --dataset erpcore_n400 --output D:/Data/EEG
# Use previously downloaded and checksummed original sources:
python -m tools.prepare_moabb --dataset erpcore_n400 --offline --output D:/Data/EEG
```

The converter stages output and refuses to overwrite an existing final folder.
See [MOABB preparation guide](moabb-preparations.md) and [dataset overview](datasets.md).
