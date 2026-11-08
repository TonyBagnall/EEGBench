# Cached open MOABB conversions

The four follow-on source caches from the [download batch](open-moabb-downloads.md)
are converted by [prepare_open_moabb.py](../tools/prepare_open_moabb.py), using
native files rather than MOABB's default filtering or baseline correction.
All outputs use `D:/Data/EEG/Name/Name_TRAIN.ts` / `Name_TEST.ts`, ordered case TSVs,
sensor information, provenance, attribution, validation and artifact manifests.
Sources and per-recording compressed NPZ intermediates remain under
`D:/Data/EEGSources/`, outside Git. No validation partition is archived.

Measured results are in [open-moabb-conversion-results.json](open-moabb-conversion-results.json).

<!-- RESULTS:START -->
| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| RestingEyeState | 140 | 50 | 19 | 16 | 5120 | 2 | 512 | 0.206 | CC-BY-4.0 |
| GameTargets | 20400 | 6000 | 22 | 8 | 225 | 2 | 250 | 0.907 | CC-BY-4.0 |
| CodedFlickerTargets | 2160 | 720 | 12 | 28 | 1100 | 4 | 500 | 1.469 | CC-BY-4.0 |
| ImaginedHandTraining | 5568 | 1588 | 18 | 22 | 2560 | 2 | 512 | 6.873 | CC-BY-4.0 |
<!-- RESULTS:END -->

## RestingEyeState — Rodrigues2017

Predict **eyes closed versus eyes open** from ten-second resting EEG blocks.
This is the Grenoble Alpha Waves study, distinct from the UCI EEG Eye State
recordings underlying EyesOpenShut. Original source:
[Zenodo 2605110](https://doi.org/10.5281/zenodo.2605110), a pinned version returned
by the collection's concept record. Reference: Cattan, Rodrigues and Congedo,
[*EEG Alpha Waves Dataset*](https://hal.science/hal-02086581).
The original data licence is **CC BY 4.0**, recorded in the download receipt.

Nineteen participants, one session and one recording each, five blocks per class.
Original IDs are `01`–`06`, `08`–`20`. Train uses the first 14 of these IDs
(`01`–`06`, `08`–`15`); test uses `16`–`20`. No official split is supplied.
The original author loader and MOABB both exclude participant 07. Independently,
three of 07's nominal ten-second windows cross the next opposite-state onset;
no such overlap exists in the other 19 recordings. The author's reason for
excluding 07 is not established by that observation.

Native MAT `header.mat` supplies this exact EEG order:
`Fp1, Fp2, Fc5, Fz, Fc6, T7, Cz, T8, P7, P3, Pz, P4, P8, O1, Oz, O2`.
The native spelling is preserved. Source columns 1–16 (zero-based) hold EEG;
column 0 is a timestamp and 17/18 contain the closed/open onset markers. Start
samples come directly from those markers. Each case contains 5120 samples at
512 Hz. Native numerical microvolt values are kept in float64. Native demographics
are retained. Right-earlobe reference, AFz ground and absence of digital filtering
are documented acquisition properties, not fields recovered from the MAT header.
Individual sensor coordinates are unavailable.

## GameTargets — BrainForm / RomaniBF2025ERP

Classify **calibration target flashes versus other flashes** in a visual game
and spelling system. Source: [Zenodo 17225966](https://doi.org/10.5281/zenodo.17225966),
`BIDS.zip`, **CC BY 4.0**. Reference: Romani et al. (2025),
[*BrainForm: a Serious Game for BCI Training and Data Collection*](https://arxiv.org/abs/2510.10169).

Use the first 600 calibration events in each of two main recordings, preserving
the pinned MOABB view: native `T1` is encoded 1 (target), `T2`–`T10` encode 2
(non-target). These binary labels follow the loader's mapping; BIDS contains
stimulus identity rather than an independently recorded attended-target field.
All 26,400 selected event codes and sample indices were independently checked
against the EDF's native STI channel, allowing EDF numerical quantisation by
rounding to the original integer trigger code.

The BIDS archive contains 23 participant folders. P18 has no recording folder;
P15 has only one main recording. Requiring both main recordings leaves **22**
participants, consistent with the reported completer count, without assigning
unavailable completion flags. Optional Extra recordings and inference gameplay
are excluded. Session labels such as `0grain` and `1cb` identify within-visit
order and visual texture, not separate-day visits. Cases preserve those labels.
First 17 eligible participant IDs train; the remaining five test. Exact memberships
are stored in the dataset metadata.

Native BIDS/EDF sensor order is `Fz, C3, Cz, C4, Pz, PO7, Oz, PO8`, followed by
STI, which is a trigger channel and excluded from X. Each window is 225 samples
(0.9 seconds) at 250 Hz. Flash intervals are approximately 0.1 seconds, so windows
overlap within a recording; subject-disjoint splits prevent cross-partition
recording overlap. MNE-calibrated volts are multiplied by `1e6` in float64.
EDF physical units/calibration and BIDS declarations are retained separately.
Native electrode and coordinate sidecars are preserved; unknown references and
acquisition filters are not invented. The publication's online filtering pipeline
is not applied locally or assumed to describe all distributed numerical values.

## CodedFlickerTargets — Castillos2023

Predict **which of four coded visual targets is attended** over the full 2.2-second
stimulation. This is one problem combining four separately recorded conditions:
burst versus m-sequence code, each at 40% or 100% contrast. The condition is retained
for every case. It is distinct from a binary code-bit-state prediction view.
Source: [Zenodo 8255618](https://doi.org/10.5281/zenodo.8255618), **CC BY 4.0**.
Reference: Cabrera Castillos et al. (2023), NeuroImage,
[DOI 10.1016/j.neuroimage.2023.120446](https://doi.org/10.1016/j.neuroimage.2023.120446).

Twelve release-folder participants, four recording conditions and 60 trials per
condition give 2880 trials. Source target suffixes 1–4 are preserved, with 15
trials per target per condition. Train uses release participants 01–09 and test
10–12. Original archive paths and stale internal file references are retained,
so folder IDs do not conceal the release's internal naming discrepancies.

Two native 32-electrode layouts have different channel identities and ordering.
The converter explicitly selects and orders the **28 shared, native-labelled
electrodes**, never substitutes one peripheral electrode for another:

`Fp1, Fz, F3, F7, FC5, FC1, C3, T7, CP5, CP1, Pz, P3, P7, O1, Oz, O2,
P8, P4, CP2, CP6, T8, C4, Cz, FC2, FC6, F8, F4, Fp2`.

The excluded layout-only sets are `F9/P9/P10/F10` and `FT9/TP9/TP10/FT10`.
Each recording stores its original names, selected original indices and native
chanlocs. SET files are distributed both as top-level fields and as an EEG struct.
Some contain obsolete internal FDT names; the actual paired archive directory/stem
and exact sample byte count establish the signal file. Both file hashes are kept.
One-based native event latencies become zero-based starts, with 1100 samples at
500 Hz. Source float32 microvolt samples cast losslessly to float64; no baseline
subtraction is applied. Native reference fields are kept alongside the source's
documented FCz acquisition reference, without silently resolving differences.

## ImaginedHandTraining — Kumar2024

Predict **imagined left versus right hand** during longitudinal bar-feedback
training. Source: [Zenodo 10694880](https://doi.org/10.5281/zenodo.10694880),
**CC BY 4.0**. Reference: Kumar et al. (2024),
[*Transfer learning promotes acquisition of individual BCI skills*](https://doi.org/10.1093/pnasnexus/pgae076).

The original IDs are `01`–`09` and `11`–`19`, not MOABB's consecutive renumbering.
There are 18 participants, six session days each and 360 Offline/Online bar-task
recordings. Racing recordings are excluded. Each bar recording contains twenty
cue annotations (ten per class), giving 7200 source trials before incomplete-window
exclusions. Native 769/770 annotations define five-second windows, matching the
pinned loader's source-event interval. No padding or shortened variable-length
cases are introduced. Every excluded window is recorded with its original ID,
label, source sample and available length in the recording metadata.

The split preserves both training groups: original IDs `01`–`07` and `11`–`17`
train; `08, 09, 18, 19` test. IDs, original filename tokens, session/run strings,
group and source phase are retained. All sessions of a participant stay together.

The first 22 channels are EEG, in native order:
`F7, F3, FZ, F4, F8, FC5, FC1, FC2, FC6, C3, CZ, C4, CP5, CP1, CP2, CP6,
P7, P3, PZ, P4, P8, POZ`.
The three `sens` channels are documented EOG and Status is a trigger channel;
these are excluded from classification arrays. Native uppercase labels remain.
GDF physical/digital limits are malformed float32 extremes with unit multipliers
of one. The numerical EEG samples are interpreted as microvolts following the
pinned loader/source documentation; this is a documented interpretation, not a
valid volts assertion from the malformed header. Full header calibration evidence
is retained. No additional `1e6` scaling is applied. Native values are preserved
in float64, 2560 samples per case at 512 Hz, with no further filtering/resampling.

## Validation and reproducibility

For every output, full `.ts` readback checks exact float64 case hashes, shapes,
labels and ordered case-table correspondence. Checks also cover finite values,
class counts, subject overlap, duplicate signals and cross-partition recording
interval overlap. Sensor order is checked across recordings; the Castillos named
intersection is the only deliberate harmonisation. Constant or effectively flat
sensors (`std <= 1e-7` microvolts in any valid case) are globally removed if present,
with explicit original indices and counts in the metadata.

Aeon loads and checks variance on three cases per class per partition, then fits
and predicts with SummaryClassifier. This is format verification, not a reported
benchmark result. Full signal/metadata readback covers every case independently.
Adapter tests cover crop boundaries, source pulse events, named sensor matching,
main-session membership, native header JSON and group-preserving subject splits.

The code is independent of leaderboard/experiment machinery. Pinning comes from
the original versioned source receipts/checksums and MOABB commit
`bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`. No new recordings are fetched during
conversion. Use `python -m tools.prepare_open_moabb --datasets rodrigues brainform
castillos kumar` from the repository root, with scientific dependencies installed.
Existing final output folders are never overwritten. No Zenodo upload is made.

All four conversions passed validation. No constant/effectively flat sensors were
found, so no additional sensor removals were necessary. Kumar retains 7156 of
7200 native trials; 44 truncated five-second windows are excluded with case-level
reasons in the recording metadata. That batch brought the registry to 59 prepared
problems and `eeg.txt` to 55 selected problems. Seven new adapter tests passed.
The subsequent [ImaginedHandsStroke preparation](imagined-hands-stroke-preparation.md)
raises the current counts to 60 registered and 56 selected problems; its results
also appear in the shared results JSON and have their own source report.
