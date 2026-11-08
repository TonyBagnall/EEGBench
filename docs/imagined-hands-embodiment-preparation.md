# ImaginedHandsEmbodiment / Vagaja2023

Full conversion completed and validated8November2026.
Original [Zenodo8086086 v1](https://doi.org/10.5281/zenodo.8086086),
*Electrophysiological Signals of Embodiment and MI-BCI Training in VR*,
Katarina Vagaja and Athanasios Vourvopoulos(2023). Original data CC BY4.0,
verified in the version-specific original record, independent of MOABB software.
Aliases Vagaja2023, NEMAR nm000292. No separate publication DOI established;
the record describes a VU Amsterdam thesis and links original experiment software.

Classify imagined left/right hand in VR after Embodied or Control priming.
26participants,13pergroup, one visit each; three source runs/person: resting,
embodiment priming and MI. Only the26MIrecordings supply class labels. Native
SUB identifiers and original group folders retained, not renumbered1..26.
The release describes10male/16female, all right-handed and3priorBCI users;
individual demographics/questionnaire mappings are not distributed.

The [native header audit](vagaja-native-header-audit.json) covers all26MI
recordings and1040class cues,20/class/person. All38-channel orders agree,
including32EEG followed by EMGL,EMGR,Temp,x_dir,y_dir,z_dir. Only the32EEG
are candidates for classification; auxiliaries retain their exact names/types
and calibration in metadata. Native500Hz, float32 multiplexed BrainVision
values; cast to float64 before multiplying per-channel microvolt resolution.
Independent MNE physical-volts decoding passed. No added filtering,
resampling, reference or baseline. All832 EEG filter-table rows across26 native MI headers report hardware DC/131Hz, notch Off; all26 report software filters Disabled. Structured per-recording tables and original text are retained. These are direct header fields, independent of a generic MOABB description.

Native coordinates come from CLA-32.bvef acquisition template and are retained
verbatim, not claimed as measured individual electrode locations. Reference-name
fields are empty; reference/ground identities remain unknown. Header SUB31 still
points to pre-rename files; explicitly use deposited same-stem EEG/VMRK, preserving
both declared and actual references.

Native S7/S8 cues label left/right. Each has one subsequent S10 end marker,
with spacings4997..5001samples, rather than an exact uniform10seconds. Use the
common4997sample(9.994second) window, never crossing a recorded trial end.
Two trials cross original lost-sample New Segment markers: SUB18trial ordinal38
and SUB23ordinal33 (zero-based). Exclude these entire trials without filling
samples or reconstructing time; all marker tables and excluded intervals retained.
Other lost-sample markers outside imagery windows are recorded without excluding
unaffected trials. Sample bounds refer to the stored file; seconds are index/500,
not reconstructed wall-clock elapsed time across lost-sample gaps. Verified1038retained cases from1040native cues.

No official partition exists. Assign TRAIN to first10numeric IDs within each
original group, TEST remaining3/group. Embodied TRAIN03,05,06,07,08,09,10,12,14,15;
TEST16,29,31. Control TRAIN17-26; TEST27,28,30. Fixed whole-subject split, no
archived validation. Verified798TRAIN/240TEST. Participant order numeric then
native marker order, no shuffle. Native recording dates/timestamps retained,
timezone unknown; session date grouping documented separately from missing original
visit/trial IDs. Pilot03/30 passed exact .ts readback/metadata/sensor checks and aeon fit/predict before full conversion.

Source ZIP2,177,915,815bytes; publisherMD5e89017e33a730ffa37f5a1a02acfc74f.
All original files/checksums pinned separately; classification NPZ intermediates
compressed per recording with separate pilot/full caches. Final output
D:/Data/EEG/ImaginedHandsEmbodiment; originals/intermediatesD:/Data/EEGSources/Vagaja2023.
No upload.

Same laboratory/hardware as Batista2022 does not establish identical recordings.
Different release/protocol/cohort are documented, but future Batista assimilation
must compare native IDs, dates and waveforms before counting it independently.


Final TRAIN `(798,32,4997)`, TEST `(240,32,4997)`,500Hz. Every case passed exact
float64 .ts readback, metadata/label/hash alignment and finite/flat checks. No
within-/cross-split exact duplicate cases, subject overlap or overlapping source
intervals. Actual native sensor order agrees across all26MIrecordings. Aeon
loaded both splits and fit/predict passed on3cases/class/split. No EEG sensors
removed. TRAIN398left/400right, TEST120/class: both excluded trials are left-hand
imagery in the training cohort. Final local size about2.28GB.
