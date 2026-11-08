# Local issue draft: MILimbEEG v2 copied rest epochs

Not submitted externally. Original release:
https://data.mendeley.com/datasets/x8psbz3f6x/2 (CC BY4.0).

All31 native imagery-rest files I8 for S1 and S2 are identical between the two
participant IDs, including their publisher SHA256s. The rest of the selected
imagery/baseline epochs have no other exact waveform duplicates in our full
3719case audit. No conflicting class labels were found. These copied rest signals
are nonflat; the first pair's minimum channel standard deviation is about51.84uV.
Their correct original participant cannot be determined from distributed fields.

Local reproduction after retrieving original per-file CSVs:

```python
from pathlib import Path
import hashlib
root = Path('D:/Data/EEGSources/MILimbEEG')
a = root / 'S1/S1R1I8_1_1.csv'
b = root / 'S2/S2R1I8_1_1.csv'
print(a.read_bytes() == b.read_bytes())  # True
print(hashlib.sha256(a.read_bytes()).hexdigest())
# 829cc185dc3138d59b0166aa42320dc47cb32eab9c412adf08c60bd6171bb2af
```

Full native evidence: [quality audit](../milimb-native-quality-audit.json),
[publisher source lock](../milimb-source-lock.json). Reproduce with
`tools/audit_milimb.py`. Original files remain unchanged. Our classification
preparation excludes both members of all31pairs, without choosing a true owner.
S1/S2 retain their unambiguous baseline/imagery epochs but no class8rest. A separate
source listing issue is the missing S22R1I2_5.csv; no case/label was fabricated.

Two CSV schema variants label only the sample-index header cell differently
(empty versus NaN); all16 numeric sensor headers and0..499sample indices agree.
That is documented reader handling, not a missing numeric sample repair.
