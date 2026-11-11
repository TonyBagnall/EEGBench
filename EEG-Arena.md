# EEG-Arena (EEG.FM) benchmark review

Reviewed 10 November 2026. Entry point:
[overall performance](https://eeg.fm/benchmarks/overall-performance/).

The [introduction](https://eeg.fm/benchmarks/) describes 30 EEG foundation
models and 25 supervised baselines evaluated across 57 tasks from 23 datasets,
using five experimental protocols. This is a benchmark to compare with our
TSC bake-off, as well as a potential source-discovery resource.

The overall-performance page compares pretrained models with task-specific
supervised baselines. It separates bipolar and non-bipolar configurations and
excludes flagged pretraining-data overlaps from rankings. The numeric matrices
load dynamically and were not recovered in this initial review; no model
ranking or performance conclusion has been independently checked.

The [dataset catalogue](https://eeg.fm/benchmarks/datasets/) reports 17 datasets
and 47 tasks distributed through ModelScope, with six further datasets available
only from their original providers because of redistribution restrictions.
Examples include PhysioNet-MI, Kaya Large-MI, SHU-MI, Stroke-MI, OpenBMI, HGD,
EEGMat and FACED. Their catalogue names and task variants must be mapped to
original recording sources before counting additions to our collection.

Next review: inspect executable splits, preprocessing, metrics and supervised
baselines; map all source accessions to our provenance records; check original
data licences individually. Catalogue availability is not redistribution
permission. No EEG data were downloaded and no archive problems were changed.
