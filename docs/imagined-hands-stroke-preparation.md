# ImaginedHandsStroke — Liu2024

Prepared in `D:/Data/EEG/ImaginedHandsStroke/`. Predict **imagined left-hand versus
right-hand grasping** while an acute stroke patient watches a guiding video.
This is a hand-task classification problem, not stroke-versus-control diagnosis.

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ImaginedHandsStroke | 1400 | 440 | 46 retained IDs | 29 | 2000 | 2 | 500 | 2.026 | CC BY 4.0 |

All 1840 cases are four seconds long. Train has 700 cases per class; test has
220 per class. Data are float64 microvolts. Measured checks are in
[liu2024-local-results.json](liu2024-local-results.json).

## Provenance and licence

- Source: Liu and Lv, *EEG datasets of stroke patients*,
  [Figshare article 21679035 **version 5**](https://doi.org/10.6084/m9.figshare.21679035.v5).
  The original-host metadata grants **CC BY 4.0 to the data release**.
- Paper: Liu, Wei, Wang et al. (2024), *An EEG motor imagery dataset for brain
  computer interface in acute stroke patients*, Scientific Data 11, 131,
  [DOI 10.1038/s41597-023-02787-8](https://doi.org/10.1038/s41597-023-02787-8).
- Aliases: **MOABB Liu2024**, **NEMAR nm000158**, and ETH-DISCO's misleadingly
  named **Liu2022 adapter**, which actually instantiates Liu2024.
- [Source lock](liu2024-source-lock.json) freezes version, file IDs, byte sizes,
  URLs and publisher MD5. Local receipts additionally retain SHA256.
- [Standalone downloader/converter](../tools/prepare_liu2024.py) uses loader evidence
  pinned to MOABB `bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`.

The author's **EDF derivative**, `edffile.zip` (462,843,633 bytes), was downloaded
with its small metadata and code files. The 1.87 GB alternative `sourcedata.zip`
and stimulus videos were not needed. Thus the actual selected download is about
463 MB, rather than the 2.34 GB sum of all advertised representations. Source
files, extracted EDFs and compressed per-recording NPZ intermediates are in
`D:/Data/EEGSources/Liu2024/`, outside Git.

## Release integrity exclusions

The release declares 50 participant IDs; the preparation retains **46**:

| Excluded release ID | Reason |
|---|---|
| 05 | Upstream identifies it as derived from 04; our calibrated 29-EEG numerical comparison independently confirms exact equality |
| 15 | Upstream identifies a reprocessed derivative of 11 |
| 49 | Upstream identifies a reprocessed derivative of 47 |
| 43 | Additional local exclusion: conflicting imagery-stage pulses prevent unique alignment of native events to the shared hand-label schedule |

The first three follow the pinned MOABB guard and its
[maintainer investigation](https://github.com/NeuroTechX/moabb/issues/1248).
These are statements about released data products, not claims that the declared
clinical patients are the same people. The original files are preserved. Pairwise
calibrated EEG hashes/correlations, and the detailed trigger evidence for 43, are
retained under `source_metadata/`. No marker sequence was guessed to retain 43.

## Cases and split

Every retained ID has one documented recording session/run with 40 trials:
20 left and 20 right. IDs remain strings, including leading zeros; the original
`sub-XX` token is also stored in every case row.

- Train: original IDs **01–37 excluding 05 and 15**: 35 IDs / 1400 cases.
- Test: original IDs **38–50 excluding 43 and 49**: 11 IDs / 440 cases.

The source supplies no fixed classification partition. This is our deterministic
subject-disjoint split; source partition is `unsplit`, and there is no archived
validation split. Cases follow source ID, then native event order, without shuffling.

Native stage codes mean instruction (1), imagery (2) and break (3), **not hand
side**. Hand labels 1=left and 2=right come from the shared author event table,
matched to complete native stage triplets in order. Imagery windows begin at
the observed stage-2 sample and contain 2000 samples. Every retained window ends
at or before the observed break, and no trial windows overlap.

The source event table uses milliseconds and an ideal schedule. Native markers
have timing jitter, so table onsets are preserved separately rather than substituted
for recorded samples. Some publisher EDF trigger segments contain fractional
values and held/extra tail markers; interpolation during processing is a possible
explanation, not a recovered conversion log. The converter accepts only
discrete 1/2/3 levels (within a `1e-6` code-unit tolerance), records the ignored
fractional spans/orphan pulses, and requires 40 complete unambiguous triplets.
Fractional values are not rounded into new events. Tests specifically guard
against extra markers shifting subsequent hand labels.

Start/end indices describe the **distributed EDF derivative**. Original clinical
recording/MAT offsets before publisher editing are not established. These are
not presented as independently recovered raw-acquisition offsets.

## Sensors, units and processing

The exact EEG array order is matched against the native EDF and author channel
table, with no EEG reordering:

`FP1, FP2, Fz, F3, F4, F7, F8, FCz, FC3, FC4, FT7, FT8, Cz, C3, C4, T3,
T4, CP3, CP4, TP7, TP8, Pz, P3, P4, T5, T6, Oz, O1, O2`.

The 33-channel EDF also has **CPz**, two EOG channels (**HEOL, HEOR**) and an
unnamed stage-trigger channel. CPz is the documented reference and is constant;
it is excluded as a reference channel. The EOG and trigger channels are excluded
as non-EEG. The supplied channel table calls the second EOG `VEOR`; its discrepancy
with native `HEOR` is retained, without renaming the EEG. No retained EEG sensor
was constant or effectively flat (`std <= 1e-7` microvolts), so no further global
sensor removal was necessary.

MNE-calibrated volts are multiplied by `1e6` in float64; header calibration and
original unit strings are preserved. The publisher documents mean removal and
0.5–40 Hz FIR preprocessing using EEGLAB. We apply no additional filtering,
baseline subtraction, referencing or resampling. Original and processed sampling
frequencies are both 500 Hz. Acquisition reference CPz and ground FPz come from
the author's metadata.

The author electrode/coordinate files are retained verbatim. They declare
`Other` / millimetres but contain approximately unit-radius coordinates. Their
physical scale is therefore not reinterpreted and no individual measured montage
is invented. Demographics, stroke side/location and clinical scores are retained
as supplied; for example, the participant table contains a left-handed entry
despite the release description's assertion that all participants were right-handed.

## Output and verification

The folder contains train/test `.ts` files, row-aligned case TSVs, ordered
`channels.tsv`, metadata, completeness and validation JSON, source evidence,
attribution, conversion code and a manifest with artifact hashes. The compact
intermediate format is one `numpy.savez_compressed` file per recording with numeric
float64 `X` in `(case, channel, time)` order; load with `allow_pickle=False`.

All cases passed exact float64 `.ts` readback against signal hashes and case-row
labels/indices. There are no within-partition or cross-partition duplicate cases,
shared subjects or cross-partition recording intervals. All retained values are
finite and every recording's EEG names/order agrees with the array selection.
Aeon loaded representative cases from both partitions, passed variance checks,
and completed a SummaryClassifier fit/predict check. This is format verification,
not a reported benchmark score. Fourteen adapter/shared safeguard tests passed.

Reproduce with `python -m tools.prepare_liu2024`; use `--download-only` to cache
sources, `--offline` for a verified local cache, and `--cache` / `--output` to
change locations. Existing prepared folders are never overwritten. The original
30 datasets/results are unchanged, and nothing was uploaded to Zenodo.
