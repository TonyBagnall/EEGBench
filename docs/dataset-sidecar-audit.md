# Dataset sidecar audit

This audit checked the dataset folders in `D:/Data/EEG/` for a channel-order
file, case-level subject IDs or rows, and dataset-level metadata. The legacy
30 benchmark datasets do not have a standardized `*_metadata.json` or case-row
sidecar. Their provenance and source descriptions are documented in
[Dataset provenance](dataset-provenance.md); some include the older
`*_id_TRAIN.txt` and `*_id_TEST.txt` subject-index files.

## Recovered channel lists

I added `channels.txt` to four legacy folders where the order was available
from a source record:

| Dataset | Recovered channel list | Evidence and limitation |
|---|---|---|
| EyesOpenShut | `AF3, F7, F3, FC5, T7, P7, O1, O2, P8, T8, FC6, F4, F8, AF4` | UCI EEG Eye State feature order; one continuous participant recording. The source roster has no participant ID. The list follows the original feature order used for the UEA reformulation. |
| FingerMovements | 28 named EEG channels | Exact ordered list is embedded in the local `.ts` source comments; it describes the 28 Berlin BCI channels. |
| SelfRegulationSCP1 | 6 EEG derivations | Exact dimension order is embedded in the local `.ts` comments. Names include mastoid-to-Cz derivations and locations described relative to C3/C4. |
| SelfRegulationSCP2 | 6 EEG derivations and `vEOG` | Exact dimension order is embedded in the local `.ts` comments. `vEOG` is an eye-movement channel, not an EEG electrode. |

The ordered filenames are `D:/Data/EEG/<dataset>/channels.txt`. The first three
lists are supported by the dataset/source dimension order; there is no separate
local conversion manifest to independently compare each `.ts` axis against the
source. The SCP lists are stated alongside the dimension definitions in the
distributed `.ts` comments.

## Folders still missing channel names

The following eight folders still have no `channels.txt`. Their source evidence
does not establish physical sensor names or the exact channel selection/order
used by the local array. No standard electrode names have been filled in by
guesswork.

| Dataset | Recoverable source facts | Still unavailable from the local export |
|---|---|---|
| Blink | Four EEG dimensions; 255 Hz; short/long blink labels. The source repository and local comments disagree on subject/sample totals. | Sensor names/order, participant roster for the exported cases, and case-to-person mapping. |
| EpilepticSeizures | One univariate dimension derived from Bonn EEG/UCI Epileptic Seizure Recognition; original collection has multiple source groups and includes scalp and intracranial recordings. | Which original channel/group each case came from, participant/recording identifiers, and a verified mapping to the 178-point representation. The benchmark's 178 Hz field differs from the source's reported 173.61 Hz. |
| FaceDetection | MEG; face versus scrambled-image task; source prose identifies 16 subjects split 10/6 and says 306 original channels. | Names/order of the 144 local dimensions, how they map to the original 306 sensors, and case-to-subject IDs. |
| FeedbackButton | Benchmark paper reports 57 participants, 61 EEG channels, 500 Hz, and 900 ms windows beginning 200 ms before the prompt and ending before a response. | Original acquisition accession, channel names/order, and case-to-participant IDs. The paper describes the task but does not identify a separate source release. |
| HandMovementDirection | BCI Competition IV dataset 3; two participants; 10 MEG channels above motor areas; four wrist/hand directions. | The ten sensor names/order in the local array and participant identity for each merged case. |
| MindReading | ICANN/PASCAL2 challenge; one participant, two consecutive-day sessions; 204 planar gradiometers at 200 Hz; five silent-film categories. | Individual sensor labels/order and per-case session/recording IDs in the randomized examples. |
| MotorImagery | BCI Competition III dataset I; one participant; 8 x 8 ECoG grid; imagined finger versus tongue movement, recorded on separate days. | A source-defined name/location for each grid contact and a local case-to-session manifest. The grid geometry alone is not enough to assign contact names safely. |
| Sleep | Sleep-EDF-derived classification data, traced through TF-C; one local dimension and 82 participants reported by the benchmark. | Which original EEG derivation and records correspond to each local case. The 178-sample/100 Hz export does not align with the cited TF-C window description, so channel/recording identity cannot be inferred from that source alone. |

## Subject and case metadata

The missing case-level subject mapping is not recoverable from channel names or
class labels. Some single-participant datasets can be described as one
participant, but their source participant IDs are not present. For the
multi-participant datasets above, the published participant counts do not give
the case-to-participant correspondence. In particular:

- Blink's source README reports ten people, while the local `.ts` description
  cites six; the exported cases have no participant IDs.
- FaceDetection has a subject-disjoint source split, but the exported case rows
  have no subject labels or per-subject boundaries.
- HandMovementDirection combines two subjects' trials; the local cases have no
  subject sidecar.
- MindReading cases are randomized one-second examples; only the broad
  first-day/train and second-day/test protocol is documented by the challenge.
- FeedbackButton gives an aggregate participant count but no local IDs.

For these folders, missing participant, session, run, trial and timestamp fields
remain unavailable. A blank or missing case identifier should not be replaced
with an inferred one.

## Source references

- [UCI EEG Eye State](https://archive.ics.uci.edu/dataset/264/eeg%2B) and the
  [UEA EyesOpenShut description](https://www.timeseriesclassification.com/description.php?Dataset=EyesOpenShut).
- [Berlin BCI Competition II FingerMovements](http://www.bbci.de/competition/ii/berlin_desc.html).
- [UEA SelfRegulationSCP1](https://www.timeseriesclassification.com/description.php?Dataset=SelfRegulationSCP1)
  and [SelfRegulationSCP2](https://www.timeseriesclassification.com/description.php?Dataset=SelfRegulationSCP2).
- [Bonn/UCI/TF-C EpilepticSeizures and Sleep trace](dataset-provenance.md#epilepticseizures).
- [Kaggle/UEA FaceDetection trace](dataset-provenance.md#facedetection).
- [BCI Competition IV dataset 3](https://bbci.de/competition/iv/download/).
- [ICANN/PASCAL2 Mind Reading challenge](https://www.cis.hut.fi/icann2011/mindreading.php).
- The EEG benchmark paper, particularly its dataset descriptions and
  [FeedbackButton section](https://openreview.net/pdf?id=oPQpQlsfD0).

## Subsequent local corrections

Alzheimers and FingerMovements now have dataset metadata and manifests documenting
their verified local lengths and sampling-frequency evidence. MatchWords has
156 retained axes and VideoEmotions has 25, with updated channel tables and
case hashes. Historical source rosters remain available. See
[Local data corrections](local-data-corrections.md).
