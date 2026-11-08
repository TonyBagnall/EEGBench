# Archive signal scale and flat-channel audit

Audited **5 November 2026**, before changes. The measurements below are the
historical baseline. Selected MatchWords/VideoEmotions signal corrections and
Alzheimers/FingerMovements metadata corrections were subsequently applied;
see [Local data corrections](local-data-corrections.md). Other rescalings and
the three retirements remain proposals. Benchmark results are unchanged.

The complete scan covers **47 problems, 94 train/test files, 149.684 GB,
348,585 cases and 8,993,595 case/channel pairs**. There are **no NaN or infinite
values**. All case counts and channel counts agree with the registry. Two temporal
lengths disagree with it, detailed below. Before/after file sizes and modification
times agree for all 94 input files.

Machine-readable outputs:

- [Full results and proposed changes](signal-scale-audit.json).
- [All-problem summary](signal-scale-audit-summary.csv).
- [Per-channel, per-split counts](signal-scale-audit-channels.csv).
- [Channel-removal candidates](signal-scale-audit-removal-candidates.csv).

Detailed case/channel metric arrays remain locally in
`.openeegbench/signal-audit/`, outside the data archive and ignored by Git.

## What the tests mean

The installed aeon 1.5.0 implementation of
[`check_collection_variance`](https://github.com/aeon-toolkit/aeon/blob/v1.5.0/aeon/utils/validation/collection.py)
flags **nonconstant** case/channel pairs whose temporal population standard
deviation is **at most `1e-7`**. It explicitly excludes pairs with zero range.
This tests numerical compatibility with absolute tolerances; it does not identify
the physical unit and does not establish that a signal has no variation.

This audit separately counts:

- **Exact constants:** every finite sample in that case/channel has the same value.
- **Aeon tiny-value warnings:** `std <= 1e-7` and nonzero range, matching aeon's rule.
- **Effectively flat relative to other channels:** nonconstant standard deviation
  below one millionth of the median varying-channel standard deviation in that
  same case. This is a diagnostic candidate rule, used with sensor/unit evidence;
  it is not a reason to remove an entire small-unit modality such as MEG.

Metrics were computed by parsing the stored decimal samples into **float64**.
There are **729 exact-constant pairs** and **112,476 aeon tiny-value warnings**.
Only MatchWords and VideoEmotions have the latter warnings. Only VideoEmotions
has nonconstant traces meeting the relative-flat candidate rule. The four focused
auditor tests pass, including preservation of input bytes/timestamps and separation
of tiny varying signals from exact constants.

## Proposed archive retirements

The user proposed removing **Blink**, **EpilepticSeizures** and **Sleep**.
EpilepticSeizures and Sleep are the archive's two single-channel problems.
Retiring these three would leave **44 active problems**. Retirement is a scope
choice: EpilepticSeizures and Sleep have no flat/tiny warnings in this scan.
Existing results should remain identifiable as historical results, rather than
being silently attributed to changed data or deleted.

Blink has nine exactly flat case/channel pairs in TEST: index **1** in rows
108 and 133, and index **2** in rows 301, 304, 307, 308, 324, 344 and 349.
Their constant values are respectively approximately 25.7875 and 1650. Dropping
every affected axis globally would reduce Blink from four to two channels, but
this is unnecessary if the whole problem is retired. No physical sensor names
are assigned to these unlabelled legacy axes.

## Required repairs among the retained problems

All channel indices below are **zero-based**. The proposed removal is global
within that problem: remove the same axis from every TRAIN and TEST case, keeping
a consistent sensor ordering. It does not remove that index from other problems.

| Problem | Finding | Proposed action | Resulting shape per case |
|---|---|---|---|
| MatchWords | Index **55** is exactly constant in all **720 cases**, at approximately `-1.5e-11`; the other 156 channels vary at MEG scale | Remove index 55; convert **T to fT with `×10^15`** | 156 × 1500 |
| VideoEmotions | Index **6 / F8** is effectively flat in **156 TRAIN cases**, all subject **030**, rows **4684–4839** | Remove F8 globally; retain the existing microvolt scale | 25 × 2000 |

### MatchWords: tesla, not volts

MatchWords is **MEG**, not scalp EEG. The original version-1.0.0
[BIDS channel table](https://github.com/OpenNeuroDatasets/ds004276/blob/1.0.0/sub-001/meg/sub-001_task-words_channels.tsv)
specifies **T**, with MEG 056 marked bad. Local axis 55 corresponds to that name
under the source channel order; the earlier sidecars correctly note that the
legacy export's complete physical-name-to-array correspondence has not been
independently reconstructed. The numerical observation that axis 55 is constant
does not depend on resolving that correspondence.

Its 156 varying channels have median standard deviations of **1.355e-13 T** in
TRAIN and **1.319e-13 T** in TEST. Aeon flags **56,160 pairs in each split**;
the constant channel is excluded from that count. Default `np.allclose` would
also misclassify all of these tiny but varying traces as constant.

The requested generic **`×10^6` would leave 11,520 TRAIN and 13,694 TEST pairs
below aeon's threshold**: **25,214 warnings remain**. For tesla this would be a
conversion to microtesla, not microvolts. The proposed exception **`×10^15` to
femtotesla** clears all warnings in the varying channels while preserving their
relative amplitudes. Removing the globally constant axis deals with the separate
flat-channel issue.

### VideoEmotions: an effectively dead channel, not a global unit problem

The 156 F8 traces are **not mathematically constant**. Their standard deviations
are **1.64e-10 to 1.96e-10 in the already-microvolt-scaled stored values**, and
their extrema are approximately ±8.6e-10. The rest of the dataset has a typical
standard deviation around 11–12 microvolts. All affected traces belong to
`recording_30`, subject `030`, covering that subject's whole local preparation.

The preserved upstream preprocessing records a **`1e6` gain already applied**;
the remaining MNE voltage unit tags are historical source metadata, not a reason
to multiply this problem again. See the existing
[source preparation report](openeegbench-local-preparations.md). A further gain
would make these near-zero traces pass the threshold without restoring EEG
variation. Numerical residuals after processing are a plausible explanation;
the original cause has not been independently established.

Removing F8 globally preserves the common array axes and all existing cases and
labels, but also removes valid F8 data from the other participants. This tradeoff
is explicit in the proposal. Removing it only from affected cases would create
inconsistent sensor sets; another scientifically defensible alternative is a
separately versioned exclusion of subject 030, which is not the proposed operation.

## Optional voltage-unit standardisation

**None of these 21 problems currently fails aeon's tiny-value check.** This list
is for the broader option of standardising voltage-like EEG to a microvolt-sized
numeric scale, not a claim that 21 additional datasets are defective.

Four have explicit voltage declarations in the current preparation metadata:
**CodedSymbols, CovidSurvivors, ImaginedLeftRightHand and ImaginedRightHandFeet**.
For these, `×10^6` is the documented V-to-microvolt conversion. Seventeen others
have similarly small EEG amplitudes but no verified unit/scaling manifest for
the local export. Their voltage interpretation is **inferred**, not established
by small numbers alone. Before calling their output physically calibrated
microvolts, verify the exporter/source convention; otherwise record only an
explicit numerical gain with unknown original physical units.

<!-- VOLTAGE-CANDIDATES:START -->
| Problem | Gain | Unit evidence |
|---|---|---|
| Alzheimers | ?10? | V-like; physical unit unverified |
| ButtonPress | ?10? | V-like; physical unit unverified |
| CodedSymbols | ?10? | Documented V |
| CovidSurvivors | ?10? | Documented V |
| FeetHands | ?10? | V-like; physical unit unverified |
| FibroLiverpool | ?10? | V-like; physical unit unverified |
| FibroUEA | ?10? | V-like; physical unit unverified |
| ImaginedFeetHands | ?10? | V-like; physical unit unverified |
| ImaginedLeftRightHand | ?10? | Documented V |
| ImaginedOpenCloseFist | ?10? | V-like; physical unit unverified |
| ImaginedRightHandFeet | ?10? | Documented V |
| InnerSpeech | ?10? | V-like; physical unit unverified |
| LongIntervalTask | ?10? | V-like; physical unit unverified |
| MatchingPennies | ?10? | V-like; physical unit unverified |
| OpenCloseFist | ?10? | V-like; physical unit unverified |
| PhotoStimulation | ?10? | V-like; physical unit unverified |
| PronouncedSpeech | ?10? | V-like; physical unit unverified |
| ShortIntervalTask | ?10? | V-like; physical unit unverified |
| SitStand | ?10? | V-like; physical unit unverified |
| SongFamiliarity | ?10? | V-like; physical unit unverified |
| VisualSpeech | ?10? | V-like; physical unit unverified |
<!-- VOLTAGE-CANDIDATES:END -->

The preparations already documented on a microvolt numeric scale should not be
multiplied again: ChildhoodSeizures, ClinicalSleepStages, ImaginedCommands,
ImaginedHandFeetTongue, MentalArithmetic, VideoEmotions, VisualSubjects and
WordRelatedness. ArmMovements/ImaginedArmMovements retain native numbers that
upstream interprets as microvolts, with ambiguous GDF dimension tags.
FlickerAttention's physical calibration remains unresolved; leave its numeric
scale alone pending that investigation. No other MEG problem has a tiny-value
warning, and this audit does not infer a new magnetic unit for their legacy exports.

## Additional metadata discrepancies

| Problem | Actual TRAIN and TEST lengths | Registry length | Recommendation |
|---|---|---|---|
| Alzheimers | **15000** | 30000 | The local headers explicitly identify a short variant and `@seriesLength 15000`; confirm the intended variant, then align registry/sidecars with the actual files. Do not invent a resampling operation or window duration from length alone. |
| FingerMovements | **50** | 400 | Correct the local metadata to 50. The distributed source comments explicitly describe 500 ms at **100 Hz**, also conflicting with the registry's 128 Hz. Preserve the published paper's figures separately as historical metadata. |

No crop, interpolation or resampling is proposed to force files to match these
old registry numbers. The audit parsed the actual number of numeric fields and
confirmed the `.ts` header lengths; these are not truncated parser reads.

## Precision and sidecar plan for an approved rewrite

Use **float64 for parsing, multiplication and validation**, and **17 significant
digits** when writing newly scaled values. Casting cannot recover precision
already lost in source float32/earlier exports, but avoids adding float32
rounding during the new operation. For removal-only changes, retained decimal
tokens can be preserved exactly.

For each changed problem, record in sidecars:

1. Source and new file SHA256 values/byte sizes, transformation date and revision.
2. Multiplicative gain, original/output units and confidence; distinguish physical
   conversion from a numerical gain applied to unverified units.
3. Original numeric precision, computation dtype and output formatting precision.
4. Removed original indices/names/reasons, and the ordered mapping of kept source
   axes to new array axes. Preserve original source sensor information separately.
5. Before/after shapes and validation counts; preserve every retained case's
   subject/session/trial/sample/label/split identity and order.
6. Updated case signal hashes with an explicit hash dtype, retaining original
   source hashes; update channel lists, sensor tables and manifests consistently.
7. Versioned change history, plus the matching registry/documentation dimensions.

Existing benchmark scores must remain associated with the previous data revision;
they should not be silently presented as evaluations of altered channel sets or
scale-sensitive numerical behavior.

## All 47 audited problems

`SD` is the median temporal standard deviation over nonconstant case/channel
pairs in that split, in the stored numeric units. `Exact` and `Tiny` are combined
TRAIN+TEST pair counts. A small SD is not, by itself, a physical-unit declaration.

<!-- AUDIT-TABLE:START -->
| Problem | Channels | Actual length | TRAIN SD | TEST SD | Exact | Tiny | Proposed status |
|---|---:|---:|---:|---:|---:|---:|---|
| Alzheimers | 19 | 15000 | 6.96e-05 | 7.38e-05 | 0 | 0 | retain |
| ArmMovements | 61 | 1536 | 13.6 | 13.3 | 0 | 0 | retain |
| Blink | 4 | 510 | 57.4 | 43.5 | 9 | 0 | retire |
| ButtonPress | 32 | 1000 | 9.22e-06 | 9.04e-06 | 0 | 0 | retain |
| ChildhoodSeizures | 17 | 2000 | 35.2 | 31.8 | 0 | 0 | retain |
| ClinicalSleepStages | 6 | 6000 | 14.8 | 13.4 | 0 | 0 | retain |
| CodedSymbols | 8 | 16128 | 4.23e-05 | 3.35e-05 | 0 | 0 | retain |
| CovidSurvivors | 19 | 400 | 6.64e-06 | 7e-06 | 0 | 0 | retain |
| EpilepticSeizures | 1 | 178 | 0.0523 | 0.0471 | 0 | 0 | retire |
| EyesOpenShut | 14 | 128 | 8.68 | 8.72 | 0 | 0 | retain |
| FaceDetection | 144 | 62 | 0.867 | 0.871 | 0 | 0 | retain |
| FeedbackButton | 61 | 450 | 5.71 | 5.96 | 0 | 0 | retain |
| FeetHands | 64 | 640 | 3.72e-05 | 5.09e-05 | 0 | 0 | retain |
| FibroLiverpool | 64 | 15360 | 3.62e-05 | 3.14e-05 | 0 | 0 | retain |
| FibroUEA | 64 | 15000 | 1.09e-05 | 9.89e-06 | 0 | 0 | retain |
| FingerMovements | 28 | 50 | 13.9 | 13.7 | 0 | 0 | retain |
| FlickerAttention | 8 | 512 | 0.00726 | 0.00674 | 0 | 0 | retain |
| HandMovementDirection | 10 | 400 | 163 | 161 | 0 | 0 | retain |
| ImaginedArmMovements | 61 | 1536 | 12.7 | 13 | 0 | 0 | retain |
| ImaginedCommands | 64 | 600 | 17.7 | 17.9 | 0 | 0 | retain |
| ImaginedFeetHands | 64 | 640 | 3.76e-05 | 4.01e-05 | 0 | 0 | retain |
| ImaginedHandFeetTongue | 22 | 800 | 9.9 | 11.5 | 0 | 0 | retain |
| ImaginedLeftRightHand | 60 | 800 | 2.24e-05 | 1.33e-05 | 0 | 0 | retain |
| ImaginedOpenCloseFist | 64 | 640 | 3.63e-05 | 4.22e-05 | 0 | 0 | retain |
| ImaginedRightHandFeet | 16 | 1536 | 6.29e-06 | 5.19e-06 | 0 | 0 | retain |
| InnerSpeech | 128 | 3584 | 9.97e-06 | 1.22e-05 | 0 | 0 | retain |
| LongIntervalTask | 63 | 4750 | 1.6e-05 | 1.43e-05 | 0 | 0 | retain |
| LowCost | 15 | 375 | 26.8 | 37 | 0 | 0 | retain |
| MatchWords | 157 | 1500 | 1.35e-13 | 1.32e-13 | 720 | 112320 | retain |
| MatchingPennies | 10 | 10000 | 1e-05 | 1.06e-05 | 0 | 0 | retain |
| MentalArithmetic | 19 | 1000 | 9.8 | 9.72 | 0 | 0 | retain |
| MindReading | 204 | 200 | 0.0464 | 0.0439 | 0 | 0 | retain |
| MotorImagery | 64 | 3000 | 6.42 | 10.8 | 0 | 0 | retain |
| NBackAudioCondition | 16 | 600 | 8.72 | 10.4 | 0 | 0 | retain |
| OpenCloseFist | 64 | 640 | 4.4e-05 | 3.51e-05 | 0 | 0 | retain |
| PhotoStimulation | 19 | 9000 | 6.47e-05 | 5.87e-05 | 0 | 0 | retain |
| PronouncedSpeech | 128 | 3584 | 1.18e-05 | 1.46e-05 | 0 | 0 | retain |
| SelfRegulationSCP1 | 6 | 896 | 9.75 | 9.71 | 0 | 0 | retain |
| SelfRegulationSCP2 | 7 | 1152 | 7.9 | 7.53 | 0 | 0 | retain |
| ShortIntervalTask | 63 | 2750 | 1.36e-05 | 1.39e-05 | 0 | 0 | retain |
| SitStand | 17 | 1250 | 1.55e-05 | 1.52e-05 | 0 | 0 | retain |
| Sleep | 1 | 178 | 12.6 | 10.8 | 0 | 0 | retire |
| SongFamiliarity | 32 | 3000 | 9.84e-06 | 9.94e-06 | 0 | 0 | retain |
| VideoEmotions | 26 | 2000 | 12.4 | 11.4 | 0 | 156 | retain |
| VisualSpeech | 128 | 3584 | 1.03e-05 | 1.15e-05 | 0 | 0 | retain |
| VisualSubjects | 16 | 512 | 103 | 206 | 0 | 0 | retain |
| WordRelatedness | 30 | 1024 | 9.59 | 10.8 | 0 | 0 | retain |
<!-- AUDIT-TABLE:END -->

Reproduce the read-only scan with:

```powershell
python -m tools.audit_signal_scale --root D:/Data/EEG --output .openeegbench/signal-audit --workers 4 --resume
python -m tools.summarize_signal_audit
```

The output directory must be separate from the dataset archive. The audit checks
whole case/channel traces; it does not constitute an exhaustive search for short
flat segments, clipping, physiological artifacts or duplicated recordings.
