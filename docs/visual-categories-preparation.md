# VisualCategories / Kaneshiro2015

Deferred after native source inspection, 6 November 2026. Original Stanford Digital Repository bq914sc3730, original data licence CC BY 3.0, verified in the repository rights XML rather than inferred from the paper/software. Original files are pinned by publisher MD5/SHA1 and sizes in the source inspection; downloading also records SHA256. See [source inventory](next-candidate-source-inspection.json) and [captured original rights metadata](source-evidence/kaneshiro-stanford.xml).

Task: six viewed image categories, Human Body, Human Face, Animal Body, Animal Face, Fruit Vegetable, Inanimate Object. Ten participants each completed six recording blocks over two sessions; the distributed MAT combines these. Native variables and available per-case session identifiers must be checked before conversion. EEG data have already been processed by the authors; no new filtering, averaging or synthetic continuous reconstruction is intended.

The original README v2.0.0 explicitly maps both X_2D blocks and the X_3D electrode dimension to EGI HydroCel128 electrodes1-124 in order. Names E1-E124 therefore have documented physical identity; they are not guessed from array length. The processed source has32 samples at62.5Hz. Retain the fractional sampling frequency accurately. The source README documents equivalent2D and3D representations of the same trials; these must not be counted as separate datasets.

Reference: Kaneshiro et al.(2015), A Representational Similarity Analysis of the Dynamics of Object Processing Using Single-Trial EEG Classification, PLOS ONE10(8)e0135697, [DOI](https://doi.org/10.1371/journal.pone.0135697). [Original data](https://purl.stanford.edu/bq914sc3730), [README](https://stacks.stanford.edu/file/bq914sc3730/Kaneshiro_etAl_objectCategoryEEG_README.pdf).


## Native data blocker

S1.mat has native T=5188 (nominal protocol5184). X_2D and X_3D agree exactly, but four pairs of adjacent native epochs have identical full124x32 float64 waveforms. Every pair has conflicting exemplar labels; the pair at zero-based indices3262/3263 also has conflicting category labels1(Human Body)/6(Inanimate Object). Details and waveform hashes are in [the duplicate audit](visual-categories-s1-duplicates.json); [native variables and scale](visual-categories-pilot-inspection.json) were independently inspected.

No flat channels were found in S1. The issue is duplicate waveforms and incompatible labels, not flat signals. No automatic label repair or duplicate selection is justified by the distributed arrays. No classification arrays have been published, registered or added to eeg.txt for this source. Further full-cohort download/conversion is deferred pending trustworthy source clarification. Only the already-started two-participant source inspection is retained locally; no issue has been sent to the authors.


The second already-downloaded pilot, S10, has5184 native epochs and no exact duplicate waveforms. This narrows the demonstrated problem to S1; it does not establish that the other eight uninspected subjects are affected or unaffected. See [S10 inspection](visual-categories-s10-inspection.json). A future explicitly documented clean-subject subset is possible after a full source audit, but no subset has been prepared in this run.
