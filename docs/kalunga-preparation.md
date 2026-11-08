# FlickerAttention: Kalunga2016 provenance and conversion

Prepared from [SSVEP-exoskeleton v1, Zenodo 2392979](https://zenodo.org/records/2392979),
DOI 10.5281/zenodo.2392979 (concept DOI 10.5281/zenodo.2392978). Original data
authors: Sylvain Chevallier and Emmanuel Kalunga (2015). The data record explicitly
licenses the dataset under **CC BY 4.0**. Reference: Kalunga et al. (2016),
*Online SSVEP-based BCI using Riemannian Geometry*,
[DOI 10.1016/j.neucom.2016.01.007](https://doi.org/10.1016/j.neucom.2016.01.007).
Other names: Kalunga2016, SSVEP Exo, SSVEPEXO; NEMAR nm000123.

| Dataset | Train cases | Test cases | Participants | Distinct recordings | EEG channels | Points | Hz | Classes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| FlickerAttention | 576 | 352 | 12 | 29 | 8 | 512 | 256 | 4 |

All four classes are balanced: 144 cases each in training, 88 each in test.
Original FIF codes are retained: **1=rest, 2=13Hz, 3=21Hz, 4=17Hz**. The 17/21 Hz
correction is corroborated by the original data record and the pinned MOABB loader;
older example code assigns the opposite names to codes 3/4.

## Source selection and duplicate audit

All 36 released FIF files were downloaded and verified against publisher MD5
checksums. Complete decoded EEG-plus-stimulus arrays were also hashed, detecting
duplicates even when participant headers differ. The pinned
[MOABB loader](https://github.com/NeuroTechX/moabb/blob/bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5/moabb/datasets/ssvep_exo.py)
selects 30 files using per-person run counts `2,2,2,2,2,2,3,2,2,4,2,5`.
Its omitted six filenames are duplicate aliases of recordings selected elsewhere:

| Omitted source alias | Retained alias |
|---|---|
| subject06_run3 | subject07_run3 |
| subject09_run3 | subject10_run3 |
| subject09_run4 | subject10_run4 |
| subject11_run3 | subject12_run3 |
| subject11_run4 | subject12_run4 |
| subject11_run5 | subject12_run5 |

The embedded FIF subject IDs corroborate those six retained aliases. A further
numeric duplicate remains in MOABB's selection: **subject07_run1 and
subject03_run1** have identical EEG and stimulus arrays, but different subject
headers and file checksums. This preparation retains the first sorted canonical
file, subject03_run1, and explicitly omits subject07_run1. This convention removes
duplicate data; it does **not** resolve the original recording's true participant
attribution. Both aliases, hashes and source identities are retained in
`source-file-audit.json`. The other two subject07 recordings remain, preserving
all twelve participant IDs. There are 29 distinct retained recordings / 928 cases.

The original publication's separate protocol exclusions are preserved in the
cached source description; they must not be confused with these demonstrated
duplicate-file exclusions. No additional arbitrary artifact rejection is applied.

## Sensors, timing, sessions and numeric scale

All 36 FIFs directly supply the same eight EEG names/types/order:

```text
Oz, O1, O2, PO3, POz, PO7, PO8, PO4
```

This differs from summary-page ordering. The ninth channel, STI 014, is a stimulus
channel used for epoch extraction and excluded from classifier arrays. No EEG
channels are reordered. The native frequency is 256 Hz. The retained window is
**[2,4) seconds after each FIF marker**, matching MOABB's configured interval but
defining an exclusive endpoint: exactly 512 samples. Each recording has 32 events,
eight per class. There were no incomplete retained windows. No filtering,
baseline correction, resampling or reference change is added. Values are cast to
float32 and written with nine significant digits for exact float32 readback.

FIF measurement datetimes, embedded subject IDs and calibration/reference tags are
directly recovered. `session_id` uses the measurement datetime as a locally defined
recording-session identifier; `session_date` is its UTC calendar date. It is not an
original named session label. MOABB's single session `0` and run indices are kept
separately. Each retained participant's recordings have the same measurement date;
the general source claim of different-day sessions should not override file evidence.

Two source metadata limitations are important:

- **Signal units:** FIF voltage tags are preserved, but numeric calibration is
  uncertain. A direct comparison with the original author's first GDF recording
  found FIF numeric values approximately 1e6 times the GDF values read in SI by MNE.
  We retain the distributed FIF numeric scale without an unverified unit correction.
- **Sensor positions:** raw FIF `loc` vectors have magnitudes around 100 despite
  MNE's metre convention, suggesting an unresolved millimetre/metre discrepancy.
  Raw locations and coordinate-frame tags are retained; verified metre positions
  are left unknown. The FIF custom-reference flag is retained; the original source
  says right (or left) mastoid, so laterality is not asserted.

Original GDF comparison source: [author repository at commit
faf331c1707135a62fcf08db6575d1553c56e196](https://github.com/sylvchev/dataset-ssvep-exoskeleton/tree/faf331c1707135a62fcf08db6575d1553c56e196),
`subject01/record-[2012.07.06-19.02.16].gdf`. For this recording, FIF markers are
one sample later than the GDF VisualStimulationStart annotations. Epoch sample
bounds retain the FIF reference; no undocumented timing shift is applied.

## Output, split and validation

Files are at `D:/Data/EEG/FlickerAttention/`. Training uses participants **01-09**;
test uses **10-12**. This is an EEGBench-defined fixed participant split, with no
separate validation partition. Order is participant, source run number and event
onset. The archive retains .ts TRAIN/TEST arrays, per-split case TSVs, combined
rows TSV, metadata, channels, attribution, full source audit, recording metadata,
original Info FIF snapshots, loader/code snapshots and a hashed manifest.

Case tables retain participant IDs as strings, original S1-S12 identifiers,
measurement timestamps, source/loader run IDs, recording filenames, original event
indices/codes, original event/crop samples and relative times. `end_sample` is
exclusive. Combined rows are TRAIN then TEST; `row` is zero-based within split.

Full `.ts` readback matches source epoch hashes exactly as float32. Shape/label
counts, row correspondence, source channel order, publisher checksums, participant
and recording separation, and duplicate cases were checked. **No duplicate cases
remain**, including within training. An aeon SummaryClassifier successfully loaded,
fitted and predicted representative cases from all four classes. No benchmark
scores were added. A two-person pilot passed before the full export.

```powershell
python -m tools.prepare_moabb --dataset kalunga2016 --output D:/Data/EEG
# Reuse verified local files:
python -m tools.prepare_moabb --dataset kalunga2016 --offline --output D:/Data/EEG
```

MNE 1.10.2 reads the FIF files; source-loader interpretation is pinned to MOABB
commit bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5. Source caches and pilot outputs are
ignored local files. The converter refuses to overwrite an existing final folder.
No data are uploaded to Zenodo. See [MOABB preparations](moabb-preparations.md).
