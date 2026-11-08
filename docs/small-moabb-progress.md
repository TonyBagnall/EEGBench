# Compact MOABB assimilation ? complete

All six datasets are validated in `D:/Data/EEG/`. The registry contains 54
problems; the selected `eeg.txt` contains exactly 50, preserving exclusions of
Blink, ButtonPress, EpilepticSeizures and Sleep. Original 30 problems/results
were not changed by this assimilation.

| Name | Train | Test | Channels | Points | Hz | GB |
|---|---:|---:|---:|---:|---:|---:|
| ALSAttention | 14400 | 19200 | 8 | 256 | 256 | 1.316 |
| FlickerTargets | 1440 | 360 | 8 | 1114 | 256 | 0.174 |
| ImaginedHandSides | 3680 | 2840 | 3 | 1125 | 250 | 0.423 |
| ImaginedHandsFeet | 1365 | 435 | 13 | 1250 | 250 | 0.559 |
| SpellerFlashes | 12600 | 12600 | 8 | 205 | 256 | 0.795 |
| WirelessFlicker | 1000 | 375 | 14 | 640 | 128 | 0.224 |

All cases have string subject IDs and aligned metadata rows. Exact float64
readback, labels/counts, channel order, finite values, zero constant/tiny pairs,
zero within/cross-split duplicates and zero cross-split overlapping recording
intervals passed. Every dataset passed bounded aeon load/fit/predict checks.
The full repository/preparation suite passed **84 tests**.

ImaginedHandsFeet removes Fp2 globally (original index 1), leaving 13 channels:
three subject-04 test epochs were constant at the EDF physical saturation limits.
All 1800 cases and original 14-channel source files are retained. Other sources
received no channel removal. All arrays use microvolt numeric scale; Zhou was
converted from MNE-calibrated volts ?1e6 in float64.

Case splits preserve original protocols for BCI IV2b (sessions), SpellerFlashes
(runs), ALSAttention (calibration/feedback). Their shared subjects are intentional.
FlickerTargets, ImaginedHandsFeet and WirelessFlicker are subject-disjoint.
No archived validation sets. MAMEM3 uses five source a?e blocks/subsessions with
both i/ii halves, excluding adaptation x; these are not asserted as five visits.

Sources are retained under `D:/Data/EEGSources/SmallMOABB/`. Source URLs,
versions, per-file SHA256/publisher checksums are in
`docs/small-moabb-source-lock.json`. Actual results are in
`docs/small-moabb-local-results.json`. Source/metadata completeness and references:
`docs/small-moabb-preparations.md`; provenance and main dataset pages updated.

Implementation: `tools/prepare_small_moabb.py`,
`tools/small_moabb_source_notes.json`, `tools/test_prepare_small_moabb.py`.
Adapters refuse existing destinations; do not blindly rerun completed exports.
Runtime uses isolated scientific packages in `.openeegbench/nback-aeon-1.5.0`,
`kalunga-runtime`, `ofner-runtime`. D writes require escalation.

Nakanishi author revision: `2d4e281a430b4676f75c9270db839e963f172da5`.
MOABB commit: `bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5`.
Zhou EDF/BIDS: Zenodo 16534752, CC BY 4.0; original Figshare 2061654 v2
separately declares CC0 (metadata verified, original zip not used for signals).
MAMEM3: original Figshare 3413851 v3, CC BY 4.0. BNCI IV2b: CC BY-ND;
P300 datasets: CC BY-NC-ND; Nakanishi licence unspecified. Local preparation
is not a public redistribution approval. No commits or uploads performed.
