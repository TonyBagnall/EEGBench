"""Reviewed source pins and splits from OpenEEGBench, never mutable HF branches."""

OPENEEGBENCH_REVISION = "3e4d034ae3e009deeda9c987d05a37e18fd87e15"
CONFIG_URL = (
    "https://github.com/braindecode/OpenEEGBench/blob/"
    + OPENEEGBENCH_REVISION
    + "/open_eeg_bench/default_configs/datasets.py"
)


def spec(name, revision, classes, key, train, val, test, **extra):
    return dict(
        name=name, hf_id="braindecode/" + name, revision=revision,
        classes=classes, split_key=key,
        partitions=dict(train=train, validation=val, test=test), **extra,
    )


EXCLUDED_DATASETS = {
    "mdd_mumtaz2016": "Removed: exact source signals repeat across fixed train/test partitions; see docs/issues/mdd-duplicate-windows.md",
}

DATASETS = {
    "bcic2a": spec(
        "bcic2a", "3585206f74463e787688a0f4afd12605c9be700c", 4,
        "subject", [1, 2, 3], [4, 5, 6], [7, 8, 9],
        licence="CC-BY-ND-4.0", licence_url="https://creativecommons.org/licenses/by-nd/4.0/",
        licence_evidence="https://bnci-horizon-2020.eu/database/data-sets",
        source="https://bnci-horizon-2020.eu/database/data-sets", doi="10.3389/fnins.2012.00055",
        reference="BCI Competition IV dataset 2a, Graz; Tangermann et al. (2012), Review of the BCI Competition IV.",
        reference_url="https://doi.org/10.3389/fnins.2012.00055",
        original_frequency_publication=[250.0], local_preparation_only=True,
        notes=["Local research preparation authorized by the user; redistribution of the upstream adapted signals requires separate review under CC BY-ND 4.0."]
    ),
    "isruc-sleep": spec(
        "isruc-sleep", "beda68130bc3a84c8e6abf11c527d7c5ff941616", 5,
        "subject", [f"I{i:03d}" for i in range(11, 81) if i not in (12, 15, 16, 18, 22, 24, 26, 40)],
        [f"I{i:03d}" for i in range(81, 91)], [f"I{i:03d}" for i in range(91, 101)],
        licence="Research access; redistribution unverified", licence_url="https://sleeptight.isr.uc.pt/",
        licence_evidence="https://sleeptight.isr.uc.pt/index.html%40p%3D48.html",
        source="https://sleeptight.isr.uc.pt/", doi="10.1016/j.cmpb.2015.10.013",
        reference="Khalighi et al. (2016), ISRUC-Sleep: A comprehensive public dataset for sleep researchers.",
        reference_url="https://doi.org/10.1016/j.cmpb.2015.10.013",
        original_frequency_publication=[200.0], local_preparation_only=True,
        excluded_values=[f"II{i:03d}" for i in range(1, 9)],
        notes=["Local research preparation authorized by the user; original data redistribution permission remains unverified.",
               "Distributed O1/O2/AF8/P8/PO10/PO9 names are artificial renamings; sensors.source_derivation recovers C3-M2/C4-M1/F3-M2/F4-M1/O1-M2/O2-M1 in unchanged array order."]
    ),
    "arithmetic_zyma2019": spec(
        "arithmetic_zyma2019", "8359206e7e1b3d1f068033348e291d6677be1920", 2,
        "subject", [f"{i:02d}" for i in range(28)],
        [f"{i:02d}" for i in range(28, 32)], [f"{i:02d}" for i in range(32, 36)],
        licence="ODC-By-1.0", licence_url="https://opendatacommons.org/licenses/by/1-0/",
        licence_evidence="https://physionet.org/content/eegmat/view-license/1.0.0/",
        source="https://physionet.org/content/eegmat/1.0.0/", doi="10.13026/C2JQ1P",
        reference="Zyma et al. (2019), Electroencephalograms during Mental Arithmetic Task Performance, Data 4(1):14.",
        reference_url="https://doi.org/10.3390/data4010014",
        bids_repo="nm000109", bids_revision="1b2780029b61be9a649937fa231dab8c9f4f14db",
        original_frequency_publication=[500.0],
        notes=["The HF card declares licence unknown; the PhysioNet data licence applies to the source database.",
               "Original reference: interconnected ear electrodes, as reported by the source publication."],
    ),
    "bcic2020-3": spec(
        "bcic2020-3", "8e2addefed44280be79b0c29bb09cc4c723cf18d", 5,
        "run", ["00"], ["01"], ["02"],
        licence="CC-BY-4.0", licence_url="https://creativecommons.org/licenses/by/4.0/",
        licence_evidence="https://api.osf.io/v2/nodes/pq7vb/",
        source="https://osf.io/pq7vb/", doi="10.82901/nemar.nm000113",
        reference="Jeong et al. (2022), 2020 International brain-computer interface competition: A review, Frontiers in Human Neuroscience 16:898300 (Data Set-C).",
        reference_url="https://doi.org/10.3389/fnhum.2022.898300",
        bids_repo="nm000113", bids_revision="6ad046e628cc502f25afe4059b886c00447b06c7",
        original_frequency_publication=[256.0],
        notes=["Intentional within-subject run split; subject overlap with test is expected.",
               "BIDS conversion concatenated original epoched MATLAB trials; BIDS sample coordinates are not original acquisition timestamps."],
    ),
    "chbmit": spec(
        "chbmit", "3c7fc5537fb22686b2aafa8eb1a30d292c4464ab", 2,
        "subject", [f"chb{i:02d}" for i in range(1, 20)],
        ["chb20", "chb21"], ["chb22", "chb23"],
        licence="ODC-By-1.0", licence_url="https://opendatacommons.org/licenses/by/1-0/",
        licence_evidence="https://physionet.org/content/chbmit/view-license/1.0.0/",
        source="https://physionet.org/content/chbmit/1.0.0/", doi="10.13026/C2K01R",
        reference="Shoeb (2009), Application of Machine Learning to Epileptic Seizure Onset Detection and Treatment, MIT PhD thesis; CHB-MIT Scalp EEG Database.",
        reference_url="https://physionet.org/content/chbmit/1.0.0/",
        original_frequency_publication=[256.0],
        excluded_values=["chb24"],
        notes=["chb01 and chb21 are the same participant recorded 1.5 years apart; both are in merged training.",
               "The pinned HF release includes chb24, which OpenEEGBench's fixed masks leave out; it is inspected but not converted.",
               "Distributed electrode-like names are renamed bipolar derivations; retain the inverse mapping and do not assign monopolar positions.",
               "drop_last_window=false can produce overlapping final windows even when the nominal stride equals window size."],
    ),
    "faced": spec(
        "faced", "18c73355fc71c055e92828384da85bb49bc6e3c0", 9,
        "subject", [f"{i:03d}" for i in range(80)],
        [f"{i:03d}" for i in range(80, 100)], [f"{i:03d}" for i in range(100, 123)],
        licence="CC-BY-4.0", licence_url="https://creativecommons.org/licenses/by/4.0/",
        licence_evidence="https://raw.githubusercontent.com/nemarDatasets/nm000112/2577b0bbc089b49e828cd98d80445133634b6d34/dataset_description.json",
        source="https://www.synapse.org/Synapse:syn50614194", doi="10.7303/syn50614194",
        reference="Chen et al. (2023), A Large Finer-grained Affective Computing EEG Dataset, Scientific Data 10:740.",
        reference_url="https://doi.org/10.1038/s41597-023-02650-w",
        bids_repo="nm000112", bids_revision="2577b0bbc089b49e828cd98d80445133634b6d34",
        original_frequency_publication=[250.0, 1000.0],
        local_preparation_only=True, observed_class_values=[0, 1, 2, 3, 5, 6, 7, 8],
        notes=["Prepared locally following user authorization. CC-BY-4.0 is corroborated for FACED data in Shen et al. (2024), doi:10.1016/j.neuroimage.2024.120890; original Synapse terms remain a release-review item.",
               "Only eight observed classes: Neutral (source label 4) is absent. Original numeric labels 0,1,2,3,5,6,7,8 are preserved.",
               "Import only EEG and metadata, not film/video stimuli, which have separate rights."],
    ),
    "mdd_mumtaz2016": spec(
        "mdd_mumtaz2016", "53cd9de1af5f09209d8a0f4fe20aa325c6a5fedb", 2,
        "subject",
        ["HS1", "HS10", "HS11", "HS12", "HS13", "HS14", "HS15", "HS16",
         "HS17", "HS18", "HS19", "HS2", "HS20", "HS21", "HS22",
         "MDDS1", "MDDS10", "MDDS11", "MDDS12", "MDDS13", "MDDS14",
         "MDDS15", "MDDS16", "MDDS17", "MDDS18", "MDDS19", "MDDS2", "MDDS20", "MDDS21"],
        ["HS23", "HS24", "HS25", "MDDS22", "MDDS23", "MDDS24", "MDDS25"],
        ["HS26", "HS27", "HS28", "HS29", "HS3", "HS30", "HS4", "HS5",
         "HS6", "HS7", "HS8", "HS9", "MDDS26", "MDDS27", "MDDS28", "MDDS29",
         "MDDS3", "MDDS30", "MDDS31", "MDDS32", "MDDS33", "MDDS34", "MDDS4",
         "MDDS5", "MDDS6", "MDDS7", "MDDS8", "MDDS9"],
        licence="CC-BY-4.0", licence_url="https://creativecommons.org/licenses/by/4.0/",
        licence_evidence="https://api.figshare.com/v2/articles/4244171/versions/2",
        source="https://doi.org/10.6084/m9.figshare.4244171.v2", doi="10.6084/m9.figshare.4244171.v2",
        reference="Mumtaz et al. (2017), Electroencephalogram (EEG)-based computer-aided technique to diagnose major depressive disorder (MDD), Biomedical Signal Processing and Control 31:108-115.",
        reference_url="https://doi.org/10.1016/j.bspc.2016.07.006",
        bids_repo="nm000114", bids_revision="4453b9d59d3cc1d932a52ce9dd0c523d99de2635",
        original_frequency_publication=[256.0], notes=[],
    ),
}
