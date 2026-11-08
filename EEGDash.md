# EEGDash review

Reviewed 8 November 2026. EEGDash is useful both for finding additional recording
collections and for recovering metadata or locating public mirrors of known
sources. It is not a list of independent, labelled classification problems.

Our existing [clinical candidate survey](docs/clinical-candidates.md) was compiled
in aeon-neuro on 5 November and moved here on 6 November. It examined participant
metadata and clinical contrasts, with evidence under
[docs/source-evidence/eegdash-clinical-survey/](docs/source-evidence/eegdash-clinical-survey/).
Its historical counts and candidate statuses need checking against current
[provenance](docs/dataset-provenance.md) before assimilation. In particular, the
Mumtaz depression source remains excluded because of known copied waveforms.

## What EEGDash provides

The [Python library and catalogue](https://github.com/eegdash/EEGDash) index public
neurophysiology datasets. The [quick start](https://eegdash.org/quickstart.html)
documents metadata-only queries through `EEGDash.find()` and materialisation of
selected recordings through `EEGDashDataset`. This supports source inspection
before downloading signals. The catalogue includes modalities other than scalp
EEG, so modality and task labels must be verified rather than counted wholesale.

The [AWS registry entry](https://registry.opendata.aws/eegdash/) identifies three
public stores: `eegdash`, `nemar` and `nmdatasets`. The latter holds competition
adaptations. OpenNeuro, NEMAR, EEGDash and a benchmark adaptation can expose
different views of the same recordings. An additional repository ID is not
evidence of an additional independent dataset.

## Converted corpus versus raw source collections

The separately published [EEGDash Corpus v0](https://eegdash.org/corpus/v0.html)
reports 77 converted datasets as of 3 November 2026. Its converted Hugging Face
store requires accepted access terms. It contains ten-second, 200 Hz float32
microvolt windows with specified band-pass filtering and per-session statistics;
it is not automatically an equivalent replacement for native classification
epochs, labels or the fixed partitions in our archive.

The corpus keeps dataset-specific licences rather than assigning one blanket
data licence. Its documentation distinguishes the raw-download route from the
converted store. Exact channel sets are represented separately, which matters
when checking whether one dataset has multiple sensor layouts. We should inspect
the source and conversion metadata before selecting either form.

## Assimilation procedure

1. Match the original DOI/accession and release to our existing provenance.
   Compare OpenNeuro `ds...`, NEMAR `on...`/`nm...` and original publisher IDs.
2. Recover original label definitions and actual participant/session/run IDs.
   Catalogue tags and broad paradigm descriptions are candidate-finding aids.
3. Verify the actual data grant and redistribution conditions for the chosen
   files. A hosting page or software licence does not replace source terms.
4. Pin the source revision and file checksums. For a mirror, preserve the
   original accession plus the mirror's file identities and transformations.
5. Check native channel names/order/types, units, geometry and preprocessing.
   Retain uncertainty; do not invent a standard montage or assume all inputs EEG.
6. Pilot the classification conversion, then audit the complete cohort for
   duplicates, flat sensors, split leakage and metadata alignment. Use the
   existing [conversion handover](DATASET_CONVERSION_HANDOVER.md).

For the current motor imagery additions, EEGDash/NEMAR are possible alternative
access routes for the Harvard-hosted candidates. That is an access investigation,
not evidence that Pan2023 and Pan2025 contain independent recordings. Their
overlap check remains necessary before both could count towards the MI target.

No EEGDash corpus download or additional dataset admission was performed merely
to write this review. Current prepared counts and active work remain in
[assimilation-progress.json](docs/assimilation-progress.json).
