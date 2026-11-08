# Completed motor imagery batch,8November2026

The two pending preparations are finished and registered, followed by the next
candidate Vagaja2023 as ImaginedHandsEmbodiment. Final `.ts` files and sidecars
are under D:/Data/EEG/Name; sources/intermediates remain separately under
D:/Data/EEGSources. No upload. Collection74registered/70selected;22motor imagery
problems including21scalp EEG and the original one ECoG entry. Original30paper
problems/results unchanged.

| dataset | train_cases | test_cases | subjects | channels | timepoints | classes | frequency | size_GB | licence |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ImaginedHandsRobot | 2880 | 2880 | 12 | 32 | 1000 | 2 | 250 | 3.509 | CC-BY-4.0 |
| ImaginedGrasps | 4500 | 2250 | 15 | 60 | 1000 | 3 | 250 | 7.688 | CC-BY-4.0 |
| ImaginedHandsEmbodiment | 798 | 240 | 26 | 32 | 4997 | 2 | 500 | 2.277 | CC-BY-4.0 |

Every final numeric case passed exact float64 .ts readback, label/hash/metadata
alignment and finite/flat checks. Native sensor names/order checked across all
source recordings. No exact duplicates within or across train/test, no EEG
sensor removals. Aeon loaded each final and fit/predict passed on3cases/class/split;
this is a compatibility smoke test, not full classifier training. Final manifest
artifact byte counts and SHA256 were all verified after sidecar refresh.

## Protocol and metadata completeness

| Field | ImaginedHandsRobot | ImaginedGrasps | ImaginedHandsEmbodiment |
|---|---|---|---|
| Native subject IDs | 01-12, strings | 01-15, strings | Native SUB03 etc and numeric tokens, strings |
| Sessions/runs | 36sessions,144MIrecordings; native folders/dates/phase | 45participant-days/recordings; day1-3 mapped from official folders; native run/calendar unknown | 26visits/MIrecordings documented; native recording dates and MI run token; original visit ID unknown |
| Case identity/timing | Native cue/trial-start event ordinals, file/sample indices | Native epoch indices and epo.t; original continuous offsets unavailable | Cue ordinal/marker key/line, stored-file bounds/end markers, timestamps; original trial ID absent |
| Original partition | Training/online phases preserved | Training+validation TRAIN, test unchanged | Unsplit source; assigned stratified whole-subject split |
| EEG identities/order | Native generic GDF labels plus original indexed chanlocs | Native epo/mnt and organiser numbered table | Native38channel headers;32EEG selected by original documented roles |
| Units | Explicit GDF calibration; calibrated volts to float64 microvolts | Native float64 numbers unchanged; microvolt interpretation inferred | Explicit native microvolt resolution; float32 counts calibrated in float64 |
| Positions/reference | Original polar layout; reference/ground unknown | Native mnt x/y/3D, units/frame unknown; FCz reference/Fpz ground documented | Embedded CLA-32.bvef template, not individual measurements; reference/ground identities unknown |
| Demographics | Published handedness,05ambidextrous; age/sex absent | Individual demographics unavailable | Cohort10male/16female/all right-handed; no individual age/sex/experience mapping |
| Missing-data/quality decisions | No excluded cues or flat EEG removal | Zeroed test-cue data avoided; imagery only; no exclusions/removals | Two left-hand imagery trials cross lost-sample markers and are excluded; common4997sample crop inside every native end marker; no EEG removals |

Robot intentionally shares all12people/sessions and pools training/online phases
across days: not unseen-person or strict global chronological evaluation. Grasps
intentionally shares all15people across official days; continuous interval overlap
cannot be recovered from epoched sources. Embodiment has20TRAIN/6TEST people,
10/3perpriming group; no shared people or overlapping source intervals.

Detailed recovery, provenance, source inconsistencies and exact class counts:
[Robot](imagined-hands-robot-preparation.md), [Grasps](imagined-grasps-preparation.md),
[Embodiment](imagined-hands-embodiment-preparation.md). Each has a corresponding
`*-conversion-result.json` and `*-metadata-completeness.json`. Source revisions,
original data-licence evidence, code snapshots, full validation and artifact
manifests accompany the D-drive output. Read IDs as strings.

Next candidate in the roadmap is Batista2022. It has not been downloaded here.
Before admitting it independently, compare its native identities/dates/waveforms
with ImaginedHandsEmbodiment; common laboratory/hardware alone proves neither
shared nor independent recordings. See [roadmap](motor-imagery-road-to-30.md).
