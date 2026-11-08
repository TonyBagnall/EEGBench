# OpenEEGBench collection review

Review of the [upstream dataset configurations](https://github.com/braindecode/OpenEEGBench/blob/main/open_eeg_bench/default_configs/datasets.py), compared with the local archive. This is a recovery and redistribution assessment; new EEG arrays have not been exported by this review. Original training and validation are merged in the proposed counts below. Test membership is retained.

## Coverage of all twelve configured datasets

| Upstream dataset | Local coverage / decision |
|---|---|
| arithmetic_zyma2019 | Prepared as MentalArithmetic. Same source as removed EEGMAT alternative preparation. |
| bcic2020_3 | Prepared as ImaginedCommands. |
| chbmit | Prepared as ChildhoodSeizures. |
| bcic2a | New source collection for this archive; recoverable signals and metadata. CC BY-ND requires care with redistribution of the upstream preprocessing. |
| isruc_sleep | New source collection; recoverable signals and metadata. Original redistribution grant remains unverified. |
| faced | Metadata inspected; new evidence supports CC BY 4.0, but the pinned preparation omits Neutral and has eight observed classes. |
| physionet | Same eegmmidb recordings underlying OpenCloseFist, ImaginedOpenCloseFist, FeetHands and ImaginedFeetHands. A four-class view would add a task preparation, not a distinct study. |
| mdd_mumtaz2016 | Excluded because identical signals cross the source train/test split; diagnostic evidence retained. |
| seed_v | Excluded under the user's redistribution restriction. |
| seed_vig | Vigilance regression, not a classification task in the upstream configuration; separate SEED access terms also require review. |
| tuab | Distinct abnormal/normal clinical classification task, but original Temple terms prohibit redistribution. |
| tuev | Distinct six-class event task from the TUH source collection; original Temple terms prohibit redistribution. |

Thus we have not exhausted the technically recoverable datasets, but the remaining entries are not all eligible for the intended public classification archive.

## Three requested candidates

Counts and sensor information for bcic2a and ISRUC were recovered directly from the pinned HF Zarr metadata, including every recording's serialized MNE Info, array shape and case table. No EEG chunks were downloaded. Full inspection reports and original distributed metadata are cached under `.openeegbench/inspection/` and `.openeegbench/review-source/` (ignored by Git).

| Dataset | HF revision | Merged train | Test | Retained subjects | Channels | Points | Hz | Observed classes |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| bcic2a | `3585206f74463e787688a0f4afd12605c9be700c` | 3456 | 1728 | 9 | 22 | 800 | 200 | 4 |
| isruc-sleep | `beda68130bc3a84c8e6abf11c527d7c5ff941616` | 64889 | 8803 | 82 | 6 | 6000 | 200 | 5 |
| faced | `18c73355fc71c055e92828384da85bb49bc6e3c0` | 15629 | 3588 | 123 | 26 | 2000 | 200 | 8 |

These are metadata counts, not newly validated signal arrays. Compressed signal chunks for the complete HF bcic2a store total about 0.339 GB; the complete ISRUC store totals about 13.099 GB and includes excluded records. These are download sizes, not estimates of `.ts` output sizes.

### BCI Competition IV 2a

- Original source: Graz BCI Competition IV dataset 2a, also BNCI2014_001 / BNCI 001-2014. Four imagined movements: left hand, right hand, both feet and tongue. Nine participants, two sessions each; 22 EEG channels and three EOG channels in the original data.
- Upstream split is by person: subjects 1–3 train, 4–6 validation, 7–9 test. Our merged train would use subjects 1–6, test 7–9. Both original acquisition sessions occur within each subject's assigned partition.
- The pinned store contains 108 run-level groups and 5,184 cases, balanced at 1,296 cases per class overall. Every recording has the same 22 names and order: Fz, FC3, FC1, FCz, FC2, FC4, C5, C3, C1, Cz, C2, C4, C6, CP3, CP1, CPz, CP2, CP4, P1, Pz, P2, POz. All are EEG; EOG is excluded.
- Labels: feet=0, left_hand=1, right_hand=2, tongue=3. Four-second windows; original 250 Hz data were resampled to 200 Hz, scaled from V to microvolts, and high-pass filtered at 0.1 Hz by the distributed pipeline.
- Subject, session (`0train`/`1test`) and run are preserved in group descriptions. Case tables retain window/trial indices and processed-recording sample bounds. These are not original acquisition timestamps or globally unique original trial IDs.
- The [original BNCI publisher](https://bnci-horizon-2020.eu/database/data-sets) explicitly specifies **CC BY-ND 4.0**. [Creative Commons](https://creativecommons.org/licenses/by-nd/4.0/) permits format changes, but restricts sharing adapted material. Consequently `.ts` conversion alone is not the issue; redistributing the already cropped, resampled and filtered HF preparation needs a documented basis or permission. It should not be described as a permissively licensed archive addition.

### ISRUC-Sleep

- Original source: [ISRUC-Sleep](https://sleeptight.isr.uc.pt/), Khalighi et al., *ISRUC-Sleep: A comprehensive public dataset for sleep researchers*, DOI [10.1016/j.cmpb.2015.10.013](https://doi.org/10.1016/j.cmpb.2015.10.013). This is a separate recording collection from the existing Sleep-EDF-derived Sleep problem.
- The pinned HF store has 110 recording groups, 90 distinct subject strings and 98,480 cases in total. The fixed masks retain 82 cohort-I participants and 73,692 cases. Cohort-II IDs are excluded by those masks: 28 groups / 24,788 cases. Several excluded groups repeat the same source description; this is not proof of signal identity and does not affect the retained fixed masks.
- Training and validation merge to 72 retained people; test comprises I091–I100. The upstream docstring's approximate subject count is not the retained count recovered from the files.
- Five labels: W=0, N1=1, N2=2, N3=3, REM=4. Each case is 30 seconds at 200 Hz. The stored window specification has a 6,000-sample window and 12,000-sample stride; actual case boundaries remain authoritative because staging annotations define separate events.
- **Channel warning:** stored names O1, O2, AF8, P8, PO10, PO9 are artificial renamings. The serialized preprocessing gives the exact original derivation order: **C3-M2, C4-M1, F3-M2, F4-M1, O1-M2, O2-M1**. They must be archived as derivations with this inverse mapping, rather than interpreted as monopolar sensor positions. All 110 groups have the same distributed name order.
- Subject/source path, epoch index and processed sample bounds are retained; second-scorer label columns are present. Cohort-I session/run fields are null. Original source paths contain subject/file identifiers but include an upstream machine path, which is provenance rather than a portable location.
- The [original download page](https://sleeptight.isr.uc.pt/index.html%40p%3D48.html) states research availability. The [NEMAR record](https://nemar.org/dataset/nm000111) reports no usable licence (`n/a`). No explicit permission to redistribute processed signals was established. Metadata recovery is feasible; public archive admission still needs original-source clarification.

### FACED

- Original source: Chen et al. (2023), [A Large Finer-grained Affective Computing EEG Dataset](https://doi.org/10.1038/s41597-023-02650-w), [Synapse syn50614194](https://doi.org/10.7303/syn50614194). The original study has 123 participants and nine emotion categories while watching 28 video clips.
- New licence evidence: the data-availability section of [Shen et al. (2024), NeuroImage](https://doi.org/10.1016/j.neuroimage.2024.120890), coauthored by original FACED researchers including Dan Zhang, explicitly identifies the **FACED data** as CC BY 4.0. This corroborates the NEMAR derivative's declaration and is stronger than relying on the data paper's article licence. The existing importer still has its earlier gate; this review has not silently changed that gate or represented the original Synapse access terms as fully retrieved.
- The pinned HF store contains labels 0,1,2,3,5,6,7,8. Its own mapping identifies the absent label 4 as **Neutral**. The remaining classes are Anger, Disgust, Fear, Sadness, Amusement, Inspiration, Joy and Tenderness. This release must be described as eight observed classes. A faithful nine-class preparation requires recovering the omitted neutral cases from the original/BIDS recordings and documenting a separate conversion.
- Retained subject IDs, video/trial identifiers, ordered sensor names/types and processed sample bounds have already been inspected. The 26-channel selection, 200 Hz resampling and 10-second windows are specific to the HF preparation, not the original full 32-channel dataset.
- Original movie clips have separate rights and are outside EEG recovery.

## Other source terms

The [Temple subscriber agreement](https://isip.piconepress.com/projects/nedc/forms/tuh_eeg.pdf) explicitly prohibits release to third parties or redistribution. TUAB/TUEV being readable on Hugging Face does not remove those original terms. Their inclusion would require separate permission or a download-at-use workflow rather than publishing their signals in this archive.

BCI IV 2a, ISRUC and FACED are distinct recording collections from the existing archive's other movement, Sleep-EDF and FaceDetection problems respectively. FACED is emotion recognition; it is unrelated to FaceDetection's face/scramble MEG task.
