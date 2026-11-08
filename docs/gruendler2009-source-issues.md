# Gruendler2009 processed CNT decoding notes

Observed with MNE 1.13.2, explicit `data_format='int32'`, using pinned mirror
`jalauer/Gruendler2009@a2fa8aa7a39f668058b715d58b049353eea4f9e7`.
Original PRED+CT accession d008, licence PDDL-1.0.

The 35 nominal raw files decode consistently with the original author's int32
import script. The 11 `_ready.cnt` files are Neuroscan-processed derivatives,
with uncertain interpolation/reference history according to ORIGINAL_README.rtf.
Some omit EKG; their 64 EEG labels remain identifiable in the same order.

Five processed files (946,950,956,957,958) yield roughly 133 million samples in
MNE's header interpretation, far beyond the physical size of the distributed
files. **This is an unresolved reader/header compatibility problem, not proof
that the original signals are corrupt.** No repair, guessed truncation or
magnitude-based scaling was applied. All 11 processed files are deferred from
the archive conversion, including 10 high/1 low symptom participants, to avoid
mixing uncertain processing with the nominal raw subset (12 high/23 low).

Minimal header-only reproduction (do not preload):

```python
from pathlib import Path
from huggingface_hub import hf_hub_download
import mne

path = Path(hf_hub_download(
    repo_id="jalauer/Gruendler2009", repo_type="dataset",
    revision="a2fa8aa7a39f668058b715d58b049353eea4f9e7",
    filename="data/946flankers_ready.cnt",
))
raw = mne.io.read_raw_cnt(path, data_format="int32", preload=False)
minimum_data_bytes = raw.n_times * len(raw.ch_names) * 4
print(raw.n_times, len(raw.ch_names), path.stat().st_size, minimum_data_bytes)
print(minimum_data_bytes > path.stat().st_size)  # True
```

The [complete header audit](gruendler2009-header-audit.json) records file sizes,
interpreted sample counts, layouts and physical-byte bounds for all 46 files.
Further work needs the processed Neuroscan storage specification or an
independent reader/viewer to establish encoding, genuine length, calibration,
reference and bad-section semantics. This note is local; no upstream issue or
message has been sent.
