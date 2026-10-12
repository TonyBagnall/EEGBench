"""The EEG classification archive: dataset lists and metadata.

The archive is the 30 problems of Table 1 in Rushbrooke, Sami, Middlehurst and
Bagnall, "Time Series Machine Learning for Classifying Electroencephalograms",
Journal of Data-centric Machine Learning Research, 2026. Every dataset has a
default train/test split in which no subject appears on both sides, or, for a
single subject dataset, no recording session does.

The lists here are plain lists of dataset names, so they can be passed directly
to the experiment and leaderboard code::

    from eegbench.datasets import eegbench, by_domain

    leaderboard(datasets=by_domain("Med"), estimators=["HC2", "MRHydra"])

The files are downloaded with ``aeon.datasets.load_classification``. The list is
held here rather than read from ``aeon.datasets.tsc_datasets.eeg2026`` so that
the leaderboard has the metadata beside the names and does not change when aeon
does.
"""

__all__ = [
    "eegbench",
    "eegbench_open",
    "restricted",
    "DOMAINS",
    "metadata",
    "by_domain",
    "metadata_markdown",
]

import pandas as pd

#: The three application areas the archive covers, as labelled in Table 1.
DOMAINS = {
    "Med": "Medical",
    "BCI": "Brain-computer interface",
    "Psy": "Psychology",
}

_COLUMNS = [
    "dataset",
    "channels",
    "classes",
    "length",
    "subjects",
    "train_size",
    "test_size",
    "frequency",
    "domain",
]

# Table 1 of the paper. Subjects is None where the source data does not record
# it. MindReading is MEG rather than EEG.
_TABLE = [
    ("Alzheimers", 19, 3, 30000, 88, 45, 43, 500, "Med"),
    ("Blink", 4, 2, 510, None, 500, 450, 255, "BCI"),
    ("ButtonPress", 32, 2, 1000, 1, 120, 120, 1000, "BCI"),
    ("EpilepticSeizures", 1, 2, 178, None, 80, 11420, 178, "Med"),
    ("EyesOpenShut", 14, 2, 128, None, 56, 42, 128, "BCI"),
    ("FaceDetection", 144, 2, 62, None, 5890, 3524, 250, "Psy"),
    ("FeedbackButton", 61, 2, 450, 57, 1700, 1150, 500, "Psy"),
    ("FeetHands", 64, 2, 640, 105, 2835, 1890, 160, "BCI"),
    ("FibroLiverpool", 64, 2, 15360, 36, 15, 21, 512, "Med"),
    ("FibroUEA", 64, 2, 15000, 41, 17, 23, 500, "Med"),
    ("FingerMovements", 28, 2, 400, None, 316, 100, 128, "BCI"),
    ("HandMovementDirection", 10, 4, 400, None, 160, 74, 400, "BCI"),
    ("ImaginedFeetHands", 64, 2, 640, 105, 2835, 1935, 160, "BCI"),
    ("ImaginedOpenCloseFist", 64, 2, 640, 105, 2835, 1890, 160, "BCI"),
    ("InnerSpeech", 128, 4, 3584, 9, 250, 200, 1024, "BCI"),
    ("LongIntervalTask", 63, 2, 4750, 139, 1660, 1120, 500, "Med"),
    ("LowCost", 15, 2, 375, 10, 600, 600, 125, "BCI"),
    ("MatchingPennies", 10, 2, 10000, 7, 700, 700, 5000, "Psy"),
    ("MindReading", 204, 5, 200, None, 727, 653, 200, "BCI"),
    ("MotorImagery", 64, 2, 3000, None, 278, 100, 1000, "BCI"),
    ("OpenCloseFist", 64, 2, 640, 105, 2835, 1890, 160, "BCI"),
    ("PhotoStimulation", 19, 3, 9000, 73, 37, 36, 500, "Med"),
    ("PronouncedSpeech", 128, 4, 3584, 9, 250, 200, 1024, "BCI"),
    ("SelfRegulationSCP1", 6, 2, 896, None, 268, 293, 256, "BCI"),
    ("SelfRegulationSCP2", 7, 2, 1152, None, 200, 180, 256, "BCI"),
    ("ShortIntervalTask", 63, 2, 2750, 139, 1660, 1120, 500, "Med"),
    ("SitStand", 17, 4, 1250, 32, 3200, 3200, 250, "BCI"),
    ("Sleep", 1, 5, 178, 82, 2394, 1205, 100, "Psy"),
    ("SongFamiliarity", 32, 2, 3000, 29, 700, 750, 1000, "Psy"),
    ("VisualSpeech", 128, 4, 3584, 9, 250, 200, 1024, "BCI"),
]

#: Datasets that are not fully open access, so are not on Zenodo and cannot be
#: loaded through aeon. Results for them are still reported.
restricted = ["FibroLiverpool", "FibroUEA"]

#: All 30 problems in the archive.
eegbench = [row[0] for row in _TABLE]

#: The 28 problems anyone can download, the same list as aeon's ``eeg2026``.
eegbench_open = [name for name in eegbench if name not in restricted]


def metadata() -> pd.DataFrame:
    """Return the archive metadata, one row per dataset.

    Returns
    -------
    pd.DataFrame
        Indexed by dataset name, with the columns of Table 1 and an ``open``
        column saying whether the dataset can be downloaded.
    """
    frame = pd.DataFrame(_TABLE, columns=_COLUMNS).set_index("dataset")
    frame["subjects"] = frame["subjects"].astype("Int64")
    frame["open"] = ~frame.index.isin(restricted)
    return frame


def by_domain(domain: str, open_only: bool = False) -> list[str]:
    """Return the datasets from one application area.

    Parameters
    ----------
    domain : str
        One of the keys of :data:`DOMAINS`: ``"Med"``, ``"BCI"`` or ``"Psy"``.
    open_only : bool, default=False
        Leave out the datasets in :data:`restricted`.

    Returns
    -------
    list of str
        Dataset names, in archive order.
    """
    if domain not in DOMAINS:
        raise ValueError(f"domain must be one of {', '.join(DOMAINS)}, not {domain!r}")
    return [
        row[0]
        for row in _TABLE
        if row[-1] == domain and not (open_only and row[0] in restricted)
    ]


def metadata_markdown() -> str:
    """Return the archive metadata as a Markdown table, for the documentation."""
    header = [
        "Dataset", "Domain", "Channels", "Length", "Classes", "Subjects",
        "Train", "Test", "Hz", "Open",
    ]
    rows = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for name, row in metadata().iterrows():
        cells = [
            name,
            row["domain"],
            str(row["channels"]),
            str(row["length"]),
            str(row["classes"]),
            "&mdash;" if pd.isna(row["subjects"]) else str(row["subjects"]),
            str(row["train_size"]),
            str(row["test_size"]),
            str(row["frequency"]),
            "yes" if row["open"] else "no",
        ]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)
