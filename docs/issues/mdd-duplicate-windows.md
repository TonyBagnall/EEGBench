# Issue draft: exact MDD windows repeated across subject-disjoint splits

Suggested tracker: [OpenEEGBench GitHub issues](https://github.com/braindecode/OpenEEGBench/issues).
An issue has **not** been posted. No equivalent MDD duplication report was found
in the repository's current open/closed issue list when checked on 3 November 2026.

## Suggested title

`mdd_mumtaz2016: identical P300 arrays under different subject IDs cause train/test leakage`

## Draft body

While auditing the fixed MDD split for reuse in EEGBench, we found exact duplicate
signals across training and test under different healthy-control subject IDs.

- OpenEEGBench config commit: `3e4d034ae3e009deeda9c987d05a37e18fd87e15`.
- Processed dataset: [`braindecode/mdd_mumtaz2016`](https://huggingface.co/datasets/braindecode/mdd_mumtaz2016).
- Exact HF revision: `53cd9de1af5f09209d8a0f4fe20aa325c6a5fedb`.
- Original data reference: [Mumtaz, Figshare v2](https://doi.org/10.6084/m9.figshare.4244171.v2).

Using the fixed subject partitions, 121 distinct five-second EEG windows occur
on both sides of the split. They affect 726 training cases and 484 test cases,
producing 2904 matching train/test pairs. All are healthy-control P300 recordings.
The six training IDs are `HS1`, `HS10`, `HS11`, `HS12`, `HS17`, `HS2`; the four
test IDs are `HS29`, `HS3`, `HS4`, `HS7`. Appending validation to training does not
cause the problem: the affected training IDs already belong to original training.

We independently downloaded the pinned source chunks for `recording_0` (HS1,
P300, training) and `recording_59` (HS29, P300, test). Their entire decoded arrays
have shape `(121, 19, 1000)` and are numerically identical, with maximum absolute
difference zero, before any local conversion, normalization or classifier fit.
Their compressed bytes have different hashes, so checking compressed-file hashes
alone would not detect this.

### Minimal reproduction

Requires only `huggingface_hub`. Downloads two compressed source chunks from the
pinned processed release and compares their decompressed bytes directly. It does
not require NumPy, Braindecode, MNE, our conversion code, or the original raw
dataset.

```python
from huggingface_hub import hf_hub_download
import gzip

repo = "braindecode/mdd_mumtaz2016"
revision = "53cd9de1af5f09209d8a0f4fe20aa325c6a5fedb"
chunks = []
for recording in (0, 59):
    filename = (
        "sourcedata/braindecode/dataset.zarr/"
        f"recording_{recording}/data/c/0/0/0"
    )
    path = hf_hub_download(
        repo_id=repo, repo_type="dataset", revision=revision, filename=filename
    )
    with gzip.open(path, "rb") as chunk:
        chunks.append(chunk.read())

assert len(chunks[0]) == len(chunks[1]) == 121 * 19 * 1000 * 4
assert chunks[0] == chunks[1]
print("The two decoded (121, 19, 1000) float32 arrays are identical.")
```

The recording identity can be checked in each `recording_N/zarr.json`:
`attributes.description.subject`, `task` and `path`. The corresponding source
`metadata.tsv` supplies window indices and numeric targets.

### Expected behaviour and question

A subject-disjoint split should not contain identical EEG signals under distinct
subject IDs in both training and test. This could inflate apparent performance on
unseen subjects. We have excluded this candidate from our archive rather than
silently deleting duplicates or changing the evaluation split.

Could you audit the original-to-BIDS and BIDS-to-HF preparation to identify where
these P300 arrays were replicated? We have not established the stage responsible,
or whether the original Figshare data contains the same issue. If the processed
data is corrected, a new HF revision and updated benchmark pin would make the
change reproducible.

## Retained local evidence

The case-pair report and independent source verification are kept in
`.openeegbench/diagnostics/mdd_mumtaz2016/`. Prepared signal arrays and the local
`.ts` candidate are removed at the user's request. These diagnostic files are
ignored by Git and have not been uploaded or attached to an issue.
