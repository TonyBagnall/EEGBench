# Open MOABB source downloads

Started 5 November 2026, smallest transfers first, following the
[remaining-candidate survey](moabb-remaining-candidates.md). This is the first
batch of five original-host-verified CC BY 4.0 datasets, not the entire catalogue.

**Batch complete:** all five source collections have downloaded and passed their
publisher checksum checks. ImaginedGripForce is also converted; the other four
are also [converted and validated](open-moabb-conversions.md). The four follow-on downloads
total **5,227,440,520 bytes**, with per-file SHA256 receipts saved below.

**ImaginedGripForce / MartinezPeon2024 is prepared**, validated and added to the
archive: [preparation report](imagined-grip-force-preparation.md). It is in
`D:/Data/EEG/ImaginedGripForce/`; source files are in
`D:/Data/EEGSources/MartinezPeon2024/`.

The next four have a separate, reusable
[source downloader](../tools/download_open_moabb_batch.py) and
[pinned source lock](open-moabb-download-source-lock.json). Exact completed
downloads, SHA256 and publisher checksum receipts are in
[open-moabb-download-results.json](open-moabb-download-results.json).
Only completed datasets enter that receipt; an unfinished `.part` is not ready.

| Transfer order after MartinezPeon | Source | Selected original files | Bytes | Local source folder |
|---:|---|---|---:|---|
| 1 | RomaniBF2025ERP / BrainForm | BIDS.zip, excludes duplicate raw/pilot/failed archives | 63,636,817 | `D:/Data/EEGSources/RomaniBF2025ERP/` |
| 2 | Rodrigues2017 / Alpha Waves | All 20 subject MAT files, native headers and MAT demographics; no duplicate signal CSVs | 105,265,970 | `D:/Data/EEGSources/Rodrigues2017/` |
| 3 | Castillos2023 | 4Class-CVEP.zip, includes all four recorded conditions | 587,883,503 | `D:/Data/EEGSources/Castillos2023/` |
| 4 | Kumar2024 | Online_Offline_Race.zip | 4,470,654,230 | `D:/Data/EEGSources/Kumar2024/` |

Selecting one representation makes BrainForm's transfer smaller than Rodrigues,
despite the survey's order by estimated converted array size. These four source
caches now have prepared classification problems; see [conversion results](open-moabb-conversions.md). Together their selected
native downloads require 5.227 GB; extraction and classification exports need
extra space. The downloader checks pinned source identity, licence, file sizes
and publisher MD5, and records SHA256. It reuses complete valid cached files.

## Native metadata findings before conversion

See [inspection results](open-moabb-source-inspection.json). These are observations
from distributed files, not completed array/label validation:

- **Rodrigues:** native `header.mat` supplies all ordered column names, including
  EEG `Fc5` / `Fc6` spelling and the eyes-closed/open marker columns. Preserve
  native labels in sidecars. All 20 subject files have ten marker onsets with
  enough remaining samples for a 10-second crop. Participant 7 is present despite
  the MOABB loader's exclusion. Investigate signal quality and the reason for
  exclusion before deciding whether to use 19 or 20 participants.
- **BrainForm:** the BIDS ZIP has **23 participant folders**, whereas the original
  description reports **22 completers**. Folder IDs skip P18 and reach P24.
  Reconcile these with participants.tsv, sessions and success/completion flags
  before choosing membership. Native channels.tsv supplies eight EEG names
  (`Fz, C3, Cz, C4, Pz, PO7, Oz, PO8`) plus a separate trigger channel, and declares
  250 Hz / volts. Final units need checking against EDF calibration during import;
  use documented float64 V-to-microvolt conversion if confirmed.
- **Castillos:** the ZIP has 96 non-directory source files, 48 paired EEGLAB
  SET/FDT recordings across 12 participants and four conditions, approximately
  830.6 MB uncompressed. Original target/cue labels and sensors still need inspection.

Re-run from the repo root with the scientific dependencies installed:

```powershell
python -m tools.download_open_moabb_batch
```

`--datasets Rodrigues2017` limits the batch; `--output` changes the cache root.
No source archives or arrays are committed, and nothing is uploaded to Zenodo.
