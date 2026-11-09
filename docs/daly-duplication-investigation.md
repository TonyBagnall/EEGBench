# Daly / ds002720 cross-subject duplication

Investigated 9 November 2026. Original source: [OpenNeuro ds002720 v1.0.1](https://openneuro.org/datasets/ds002720/versions/1.0.1),
Git commit `f704b13bed4383af66b6aef93faa18aeb336c0ca`.

## Finding

These original recordings are byte-identical, not merely similar task epochs:

| Original file | Bytes | SHA256 |
|---|---:|---|
| `sub-09/eeg/sub-09_task-run10_eeg.edf` | 15015120 | `a25412b552cfff794a32d052c5d5b3b00a2cdcae24574db603ff05dc26845312` |
| `sub-15/eeg/sub-15_task-run10_eeg.edf` | 15015120 | `a25412b552cfff794a32d052c5d5b3b00a2cdcae24574db603ff05dc26845312` |

Their original Git-annex pointers are identical and identify the same
`MD5E-s15015120--649d09cd77643965d3feddb2b1f0ded1.edf` object. The downloaded
originals previously passed that MD5 and produced the SHA256 above. The conversion
independently detected identical calibrated task cases across these subjects.

The original run-10 event TSVs are also identical: 18 labelled 20-second events
with exactly the same onsets and classes. Both EDF headers specify 19 channels,
1000 Hz and 395 seconds, with patient field `X X X X X`. The header provides no
usable subject identifier. The last event, onset 376.370 s, exceeds the recording
end; the other 17 events are complete. Consequently this is 17 pairs of complete
duplicate cases, plus one incomplete event under each attribution.

The archive split puts subject09 in TRAIN and subject15 in TEST: retaining both
would create cross-partition leakage. There is no recovered evidence establishing
whether09 or15 is the correct owner. This is not evidence that their other
recordings are identical, or that both people should be removed.

## Existing references checked

- [Original README](https://github.com/OpenNeuroDatasets/ds002720/blob/master/README):
  describes nine runs, without discussing duplicate recordings.
- [Original CHANGES](https://github.com/OpenNeuroDatasets/ds002720/blob/master/CHANGES):
  v1.0.1 changes the title; no duplicate correction is documented. File history
  attributes the run-10 path to the original added-content commit.
- The public OpenNeuro `Dataset.comments` API returned an empty list on this date.
  Its public version list contains only1.0.0 and1.0.1; latest remains1.0.1, so no
  newer published correction was found.
- GitHub searches for `ds002720` and `Daly2020` in MOABB, and `ds002720` in
  OpenNeuro's platform tracker, found no report explaining this particular pair.
- [MOABB introduction PR1189](https://github.com/NeuroTechX/moabb/pull/1189) mentions
  rejecting duplicate task/run *identifiers*. That is different from identical
  data under two distinct subject IDs; no explanation of09/15run10 was found there.
- [Pinned MOABB loader](https://github.com/NeuroTechX/moabb/blob/bed9f0fa1b9c4d3f71c7f2ddb22e4e44383211b5/moabb/datasets/daly2020.py)
  documents nine runs and its direct-download loop requests1..9. Thus the direct
  path does not fetch run10. Its reader enumerates available BIDS files; this
  should not be described as a documented waveform-deduplication policy.

These are bounded search findings, not proof that nobody has reported the issue
elsewhere. Small retrieved evidence is under
[`source-evidence/daly-duplication-review/`](source-evidence/daly-duplication-review/).

## Where to report it

First use the **comments section on the
[OpenNeuro dataset page](https://openneuro.org/datasets/ds002720/versions/1.0.1)**.
This addresses the original data owners. OpenNeuro documents dataset comments in
its [user guide](https://docs.openneuro.org/user_guide.html). The dataset lists
Ian Daly and Nicoletta Nicolaou among its authors/creators.

The [GitHub dataset mirror](https://github.com/OpenNeuroDatasets/ds002720) has
`has_issues=false`; do not direct users to an unavailable mirror issue tracker.
For downstream loader handling, use
[MOABB's issue tracker](https://github.com/NeuroTechX/moabb/issues/new/choose).
For help reaching the owner, OpenNeuro's user guide also documents its SUPPORT
facility. No message or issue has been posted by this agent.

A ready-to-paste report is in
[`daly-duplication-issue-draft.md`](daly-duplication-issue-draft.md).

## Conversion decision

Exclude **both** run-10 copies from the derived classification problem until an
author establishes correct ownership. Retain all other eligible runs of both
participants, including unique run10 data from other participants. This removes
34 otherwise complete case occurrences without assigning an ambiguous recording
to either subject. Keep the original source objects and checksums unchanged.

The adapter verifies the reviewed path pair, byte length and exact SHA256 before
excluding it. Unexpected new file copies or changed source content stop the
conversion. The strict all-case duplicate check remains enabled for the retained
data; it is not bypassed to admit this dataset.

Dataset metadata and manifest retain the exclusion policy, both original paths,
participant IDs, hashes, and every excluded native event. Complete-subject
membership, class counts and arrays must be recomputed and fully validated after
this exclusion; final results are recorded separately when conversion succeeds.
