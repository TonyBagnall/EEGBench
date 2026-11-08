# Local data corrections, 5 November 2026

These corrections apply to the files in `D:/Data/EEG/`. The collection still
contains 47 problems. Published benchmark results and historical source
dimensions are unchanged.

| Problem | Current train shape | Current test shape | Correction |
|---|---|---|---|
| Alzheimers | 45 × 19 × 15000 | 43 × 19 × 15000 | Correct length from 30000 to 15000 in the registry and sidecars; signal files unchanged. |
| FingerMovements | 316 × 28 × 50 | 100 × 28 × 50 | Correct length from 400 to 50 and frequency from 128 to 100 Hz; signal files unchanged. |
| MatchWords | 360 × 156 × 1500 | 360 × 156 × 1500 | Remove constant original axis 55; multiply retained values by 1e15, converting T to fT. |
| VideoEmotions | 15629 × 25 × 2000 | 3588 × 25 × 2000 | Remove F8, original axis 6, from every case; retain the existing microvolt numeric scale. |

Alzheimers is the local `Alzheimers_short` variant. Both headers and all case
lengths confirm 15000 points. Its reported 500 Hz is retained as unverified;
the available local evidence does not establish whether the shorter variant
was cropped or resampled. FingerMovements' embedded source comments establish
500 ms epochs at 100 Hz, downsampled from 1000 Hz. Neither correction changes
the signal files or performs resampling.

MatchWords is MEG. Original axis 55 is exactly constant in all 720 cases. The
source-order correspondence is `MEG 056`, marked bad in the original source.
The inherited physical array-to-sensor correspondence remains unverified;
the sidecars retain this limitation. The conversion uses float64 arithmetic
and 17 significant decimal digits for exact float64 readback. Participant
IDs missing from the inherited export remain unknown.

VideoEmotions F8 is effectively flat in 156 training windows from participant
`030`, recording `recording_30`. It is removed globally to maintain a common
channel set. Every retained numeric token is preserved verbatim. The upstream
microvolt scaling had already been applied, so no gain is added. Historical
MNE voltage tags are retained separately from the current numeric units.

Case order, labels, split membership and identifiers are preserved. Sidecars
record the original and retained channel indices, units, gain, precision,
source hashes and prior metadata. Case tables contain updated signal hashes.
Full float64 readback verifies shapes, label order, case hashes, finite values,
channel selection and zero tiny varying or exact-constant channel pairs in
the two transformed problems. Cross-split duplicate checks and bounded aeon
load/fit/predict checks also pass.

Original MatchWords signal backups were subsequently losslessly compressed to
`.ts.gz` to make space for the next dataset. Every decompressed SHA256 was
verified against the original source hashes before removing the uncompressed
backup copies; `BACKUP_FORMAT.txt` records how to restore them.

Original folders are backed up outside the active archive in
`D:/Data/EEG_Backups/`; exact paths are recorded in the manifests. Metadata-only
corrections retain prior registry metadata there as well. Machine-readable
results are in [metadata corrections](metadata-corrections-results.json) and
[signal corrections](signal-cleanup-results.json). The reusable tools are
`tools/correct_local_metadata.py` and `tools/transform_local_signals.py`;
both require `--apply` to make changes.

The [signal audit](signal-scale-audit.md) remains a historical baseline.
Its other 21 suggested rescalings and the proposed retirements have not been
applied. Blink's nine exact-constant case/channel pairs remain in the archive.
