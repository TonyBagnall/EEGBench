# Local issue draft: S1 duplicate waveforms with incompatible labels

Not submitted. Original source: Stanford Digital Repository bq914sc3730, S1.mat, README v2.0.0. Publisher MD5 `228e34461abcb3b1631671742fc142e5`; downloaded SHA256 `595c381f23b6f78fe0008406d5354201f730c4a7daa70264895945f200e07a26`.

The distributed file contains T=5188. Four adjacent pairs have byte-identical124x32 waveforms. All four pairs differ in exemplar label; one also differs in category label. The equivalent X_2D representation matches X_3D exactly, so this is present in the distributed source arrays before conversion.

Minimal reproduction after downloading the original S1.mat:

```python
import numpy as np
from scipy.io import loadmat

d = loadmat("S1.mat", simplify_cells=True)
a, b = 3262, 3263  # zero-based native epoch indices
print(np.array_equal(d["X_3D"][:, :, a], d["X_3D"][:, :, b]))  # True
print(d["categoryLabels"][[a, b]])  # [1, 6]: Human Body / Inanimate Object
print(d["exemplarLabels"][[a, b]])  # [2, 66]
```

All duplicate pairs and exact waveform hashes are in [the audit](../visual-categories-s1-duplicates.json). S10 has5184 epochs and no exact duplicates; no claim is made about the other eight uninspected files. The source correspondence cannot establish which category/exemplar is correct for an ambiguous pair. Source clarification or a corrected file is needed before using those epochs. No label repair has been applied.
