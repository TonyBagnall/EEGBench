# ds002720: identical run-10 EEG and events under subjects 09 and 15

Suggested destination: comments on
https://openneuro.org/datasets/ds002720/versions/1.0.1

While preparing a subject-disjoint classification dataset, I found that these
files in ds002720 v1.0.1 are identical:

- `sub-09/eeg/sub-09_task-run10_eeg.edf`
- `sub-15/eeg/sub-15_task-run10_eeg.edf`

Both are 15,015,120 bytes, with SHA256
`a25412b552cfff794a32d052c5d5b3b00a2cdcae24574db603ff05dc26845312`.
Their original Git-annex pointers refer to the same object,
`MD5E-s15015120--649d09cd77643965d3feddb2b1f0ded1.edf`.
The run-10 event TSVs are identical too. Their EDF headers do not identify the
participant (`X X X X X`).

This can be reproduced without downloading EEG:

```python
from urllib.request import urlopen

base = "https://raw.githubusercontent.com/OpenNeuroDatasets/ds002720/"
base += "f704b13bed4383af66b6aef93faa18aeb336c0ca/"
pointers = [
    urlopen(base + f"sub-{s}/eeg/sub-{s}_task-run10_eeg.edf").read()
    for s in ("09", "15")
]
print(pointers[0].decode())
print(pointers[0] == pointers[1])  # True: identical original annex pointer
```

Could you clarify which participant this recording belongs to, and whether the
other path should contain a different recording or be removed? The README
describes nine runs, while these are labelled run 10; are these additional or
replacement runs? I could not find an explanation in the README or CHANGES.

For now our derived dataset excludes both ambiguous run-10 copies, retaining
the other recordings of both subjects. Keeping both would allow identical EEG
to enter both sides of a subject-disjoint train/test split. We would prefer to
restore any correctly attributed unique recording once this is clarified.
