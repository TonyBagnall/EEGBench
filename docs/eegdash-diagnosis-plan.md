# EEGDash diagnosis assimilation

Started 9 November 2026. Target:20 additional classification problems with
diagnostic participant labels, beyond the82 registered/78 selected preparations.
This is an admission target, not a claim that20 suitable independent sources
have already passed review. Work stays local on `dataset-assimilation`.

Confirmed9November2026: start with diagnosed groups only and establish how many
qualify. Screening/symptom-only groups are outside this initial batch. Prognosis, patient-only
BCI tasks, interventions and event detection do not silently fill this target.
Separate tasks can use different recordings from a shared cohort, but cohort
sharing must be documented; relabelled/resampled copies do not add problems.

The catalogue refreshed from the public API contains954entries. Full response is
kept outside Git at `.openeegbench/eegdash-diagnosis/all-datasets.json`; SHA256
`82c133145573ade74df23809b8f0bfe6732896c2c1c0c887f87e3050f32cbbfd`.
The historical [clinical survey](clinical-candidates.md) remains a discovery aid.
Verify labels and licence against original sources, not machine-generated tags.

## First candidates

| Source | Proposed problem | Scope under investigation | Source size | Initial evidence |
|---|---|---|---:|---|
| ds005048 / on005048 | AlzheimersAuditory | Normal vs MCI vs AD during40Hz auditory stimulation | 0.373GB | Original v1.0.1 CC0; participant Group labels.33known-group people;2unknown excluded. Mild/moderate AD merged as AD, no invented MMSE thresholds. |
| ds002778 / on002778 | ParkinsonsRestUCSD | Parkinson's OFF-medication versus healthy controls at rest | 0.572GB | Original v1.0.5 CC0, paper/reference and participant-prefix meaning to verify; preserve ON/OFF source sessions, don't mix them silently. |

AlzheimersAuditory is fully validated and registered (2020TRAIN/1000TEST,33people).
UCSD is explicitly authorised despite the original authors caution about
small-cohort diagnostic machine learning; preserve that caution in sidecars.
Iowa resting-state pilot passed (137TRAIN/66TEST,4people,60channels); full source
download is underway. First-source protocol: retain source Stimulus
events (40seconds), split into non-overlapping4second cases at native250Hz,
without extra DSP. Labels are participant diagnosis, not Rest/Stimulus event codes.
Retain all complete eligible stimulus windows; rest intervals are not another
classification label. Fixed class-stratified whole-subject TRAIN/TEST, no
validation export; membership recorded explicitly. Pilot spans all3classes and
both partitions. Original channel/SET/FDT metadata and unit uncertainty retained.

## Exclusions and overlap checks

- Alzheimers, PhotoStimulation and CovidSurvivors already exist. Do not add their
  EEGDash mirrors or newer source releases as independent problems.
- ds004579 is already the source of LongIntervalTask/ShortIntervalTask.
- Mumtaz MDD remains excluded because of known cross-ID copied waveforms.
- ds003800 appears related to ds005048; treat it as a possible earlier release,
  not an additional independent dementia problem without recording comparison.
- Check FEP ds003944/ds003947 shared subjects/recordings; inspect TBI and Iowa PD
  cohort families before counting separately. Check Cavanagh recordings against
  the existing PRED+CT preparations.
- I-CARE and Parkinson's mortality are prognosis, not diagnosis, and remain out
  of the current strict target.

## Preparation requirements

Pin original source revisions and file digests. Pilot before bulk download.
Use native channels/order/frequency, float64 physical calibration, source-derived
windows and unchanged labels with an explicit encoding. Preserve subject IDs as
strings, original sessions/events/sample indices and per-case metadata alignment.
Archive standard `.ts` TRAIN/TEST plus full source/channel/protocol/exclusion
sidecars under `D:/Data/EEG`. Keep originals separate under configurable
`D:/Data/EEGSources/EEGDash`.

Apply strict complete-case readback, source/case duplicate and overlap checks,
subject separation, channel checks, finite/flat review and aeon compatibility.
The archive's global sensor removal rule remains std<=1e-7in microvolt-valued
retained cases. Never infer units just from amplitude. Report metadata unknowns.
No uploads or experiment submission are part of this preparation.

## Authorised mixed-rate handling

The user authorised anti-alias resampling of both psychosis cohorts to1000Hz
on9November2026, retaining all participants. Original1000Hz arrays stay unchanged.
For3000.00030000003Hz recordings, cast/calibrate float64 then resample the whole
continuous recording with MNE FFT (spectral anti-alias truncation, npad=auto,
window=auto, pad=reflect_limited, n_jobs=1) before4second windowing. Use the exact
recorded frequency. Retain native rate/sample bounds and processed indices in
every case, and distinguish nominal time intervals from whole-recording filter
support. Pilot both rates before full admission. Seven focused tests passed,
including preservation of20Hz amplitude and rejection of800Hz alias energy.

Queue: `tools/run_eegdash_diagnosis.py`; local state/logs under
`.openeegbench/eegdash-diagnosis/`. Stops on any validation error.

## Initial diagnosed-group count

After removing existing archive sources, known exclusions and six deferred
scope/overlap cases, the historical survey leaves **20candidate source rows**
for this initial diagnosed-group review (including the completed auditory AD
problem). This is not20validated problems or20independent studies. Several
PD and TBI tasks share cohorts; keep only distinct recordings, document shared
participants, and reject resampled/relabelled copies. No guarantee all20pass.

Deferred initially: hazardous drinking (clinical AUD criteria unverified),
BDI-selected depression (full-cohort diagnoses unavailable), two obesity
problems (diagnostic definition unverified), phantom-limb pain (amputee status
is not pain diagnosis), and expanded Iowa rest (possible recording overlap).
These are deferrals for evidence review, not findings that such conditions
cannot be clinical diagnoses. Machine-readable reasons and the20rows are in
`eegdash-diagnosis-candidates.json`.
