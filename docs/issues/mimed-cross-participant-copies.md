# Local issue draft: MIMED v3 cross-participant waveform copies

Not submitted to any external service. Original data:
https://data.mendeley.com/datasets/zs25xxjkm9/3, imagery-only `Motor Imagery.zip`,
19,526,072 bytes, MD5 `82726a38955c7ca8041018010fd33a30`.

The native MATLAB `joined_data` arrays contain cross-ID copies:

- All three scenario files and all four complete cell arrays of P17/P24,
  P18/P25, P19/P26, P20/P27, P21/P28, P22/P29 and P23/P30 are numerically
  identical in the downloaded version. Native `subject` fields carry their
  different IDs. This affects84 selected four-second window pairs.
- Stand/sit P05 cell0 and right-hand P06 cell1 have identical selected imagery
  samples384:896 across all14 channels, despite different task labels and
  participant IDs. Their complete cells have different lengths2432/1152; no claim
  is made that these two whole cells are identical.
- None of the360 selected cases has a constant channel. The conflicting-label
  pair's minimum channel standard deviation is approximately10.07 in the native
  numeric scale; this is not a flatline coincidence.

Minimal local reproduction after downloading and extracting the original ZIP:

```python
from scipy.io import loadmat
import numpy as np
from pathlib import Path
root = Path('Motor Imagery')
a = loadmat(root / 'Stand Up-Down Imagine/P05.mat', simplify_cells=True)
b = loadmat(root / 'Right Hand Up-Down Imagine/P06.mat', simplify_cells=True)
print(np.array_equal(a['joined_data'][0][384:896],
                     b['joined_data'][1][384:896]))  # True
for folder in ['Left Hand Up-Down Imagine', 'Right Hand Up-Down Imagine',
               'Stand Up-Down Imagine']:
    a = loadmat(root / folder / 'P17.mat', simplify_cells=True)
    b = loadmat(root / folder / 'P24.mat', simplify_cells=True)
    print([np.array_equal(x, y) for x, y in
           zip(a['joined_data'], b['joined_data'])])  # four True values
```

Full evidence: [mimed-native-quality-audit.json](../mimed-native-quality-audit.json).
Reproduce with `tools/audit_mimed.py`; source files and byte/MD5/SHA256 pins are
in the source lock. We have not guessed which participant/task owns these copies
or corrected any labels. The complete30-participant export is stopped. A reduced
cohort would change the task definition and needs an explicit, documented choice.
