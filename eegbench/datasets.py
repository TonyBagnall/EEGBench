"""The EEG classification archive: dataset lists and metadata.

The archive includes the 30 problems published by Rushbrooke et al. (2026)
and 44 additional local preparations. Use the supplied fixed train/test splits;
some protocols intentionally share subjects and some older identity mappings
remain incomplete. See docs/dataset-provenance.md for dataset-specific evidence.

The lists here are plain lists of dataset names, so they can be passed directly
to the experiment and leaderboard code::

    from eegbench.datasets import eegbench, by_domain

    leaderboard(datasets=by_domain("Med"), estimators=["HC2", "MRHydra"])

Published open files are downloaded with ``aeon.datasets.load_classification``;
the newer preparations are loaded from local .ts files. The list is
held here rather than read from ``aeon.datasets.tsc_datasets.eeg2026`` so that
the leaderboard has the metadata beside the names and does not change when aeon
does.
"""

__all__ = [
    "eegbench",
    "eegbench_open",
    "eegbench_paper",
    "local_only",
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

# Original benchmark problems, with documented local corrections to the paper's
# Alzheimers/FingerMovements lengths and FingerMovements sampling rate.
# Subjects is None where unavailable; several problems are MEG rather than EEG.
_TABLE = [
    ("Alzheimers", 19, 3, 15000, 88, 45, 43, 500, "Med"),
    ("Blink", 4, 2, 510, None, 500, 450, 255, "BCI"),
    ("ButtonPress", 32, 2, 1000, 1, 120, 120, 1000, "BCI"),
    ("EpilepticSeizures", 1, 2, 178, None, 80, 11420, 178, "Med"),
    ("EyesOpenShut", 14, 2, 128, None, 56, 42, 128, "BCI"),
    ("FaceDetection", 144, 2, 62, None, 5890, 3524, 250, "Psy"),
    ("FeedbackButton", 61, 2, 450, 57, 1700, 1150, 500, "Psy"),
    ("FeetHands", 64, 2, 640, 105, 2835, 1890, 160, "BCI"),
    ("FibroLiverpool", 64, 2, 15360, 36, 15, 21, 512, "Med"),
    ("FibroUEA", 64, 2, 15000, 41, 17, 23, 500, "Med"),
    ("FingerMovements", 28, 2, 50, None, 316, 100, 100, "BCI"),
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

#: Original published benchmark subset, retained for reproducing the paper.
eegbench_paper = [row[0] for row in _TABLE]

_TABLE += [
    ("ImaginedHandsStroke", 29, 2, 2000, 46, 1400, 440, 500, "BCI"),
    ("RestingEyeState", 16, 2, 5120, 19, 140, 50, 512, "BCI"),
    ("GameTargets", 8, 2, 225, 22, 20400, 6000, 250, "BCI"),
    ("CodedFlickerTargets", 28, 4, 1100, 12, 2160, 720, 500, "BCI"),
    ("ImaginedHandTraining", 22, 2, 2560, 18, 5568, 1588, 512, "BCI"),
    ("ALSAttention", 8, 2, 256, 8, 14400, 19200, 256, "BCI"),
    ("ArmMovements", 61, 7, 1536, 15, 4620, 1680, 512, "BCI"),
    ("CodedSymbols", 8, 20, 16128, 30, 2200, 800, 512, "BCI"),
    ("FlickerAttention", 8, 4, 512, 12, 576, 352, 256, "BCI"),
    ("FlickerSymbols", 64, 40, 1500, 35, 6240, 2160, 250, "BCI"),
    ("FlickerTargets", 8, 12, 1114, 10, 1440, 360, 256, "BCI"),
    ("ImaginedGripForce", 14, 3, 640, 10, 240, 60, 128, "BCI"),
    ("ImaginedHandSides", 3, 2, 1125, 9, 3680, 2840, 250, "BCI"),
    ("ImaginedHandsFeet", 13, 3, 1250, 4, 1365, 435, 250, "BCI"),
    ("SpellerFlashes", 8, 2, 205, 10, 12600, 12600, 256, "BCI"),
    ("WirelessFlicker", 14, 5, 640, 11, 1000, 375, 128, "BCI"),
    ("ImaginedRightHandFeet", 16, 2, 1536, 8, 240, 80, 512, "BCI"),
    ("ImaginedArmMovements", 61, 7, 1536, 15, 4620, 1680, 512, "BCI"),
    ("ChildhoodSeizures", 17, 2, 2000, 22, 34045, 2140, 200, "Med"),
    ("ClinicalSleepStages", 6, 5, 6000, 82, 64889, 8803, 200, "Med"),
    ("CovidSurvivors", 19, 2, 400, 172, 25319, 11216, 200, "Med"),
    ("ImaginedCommands", 64, 5, 600, 15, 5250, 750, 200, "BCI"),
    ("ImaginedHandFeetTongue", 22, 4, 800, 9, 3456, 1728, 200, "BCI"),
    ("ImaginedLeftRightHand", 60, 2, 800, 10, 1260, 320, 200, "BCI"),
    ("MatchWords", 156, 2, 1500, None, 360, 360, 1000, "Psy"),
    ("MentalArithmetic", 19, 2, 1000, 36, 1515, 192, 200, "BCI"),
    ("NBackAudioCondition", 16, 12, 600, 23, 11520, 5040, None, "Psy"),
    ("VideoEmotions", 25, 8, 2000, 123, 15629, 3588, 200, "Psy"),
    ("VisualSubjects", 16, 2, 512, 64, 42189, 18826, 512, "BCI"),
    ("WordRelatedness", 30, 2, 1024, 40, 3600, 1200, 1024, "Psy"),
]

_TABLE += [
    ("ParkinsonsPedalling", 63, 2, 2000, 39, 2123, 842, 500, "Med"),
    ("ParkinsonsRest", 63, 2, 2000, 55, 1216, 420, 500, "Med"),
]

_TABLE += [
    ("ObsessiveCompulsiveSymptoms", 52, 2, 2000, 35, 7754, 2660, 500, "Med"),
]

_TABLE += [("WalkingTargets", 42, 2, 100, 15, 3600, 900, 100, "BCI")]


_TABLE += [
    ('SymbolAttention', 8, 2, 256, 19, 521259, 175180, 256, "BCI"),
    ('ArmCoordination', 64, 2, 1500, 8, 1498, 505, 500, "BCI"),
]

_TABLE += [
    ("ImaginedHandGestures", 17, 4, 3000, 11, 382, 143, 500, "BCI"),
    ("ImaginedArmTasks", 17, 10, 3960, 12, 3240, 1080, 1000, "BCI"),
]

_TABLE += [
    ("ImaginedRightHandFeetRest", 24, 3, 750, 1, 150, 40, 250, "BCI"),
    ("ImaginedLeftRightHandRest", 24, 3, 750, 1, 480, 240, 250, "BCI"),
    ("ImaginedHandFootActions", 11, 8, 500, 60, 2727, 930, 125, "BCI"),
]

_TABLE += [("ImaginedHandsRobot", 32, 2, 1000, 12, 2880, 2880, 250, "BCI")]

_TABLE += [('ImaginedGrasps', 60, 3, 1000, 15, 4500, 2250, 250, 'BCI')]

_TABLE += [('ImaginedHandsEmbodiment', 32, 2, 4997, 26, 798, 240, 500, 'BCI')]

_TABLE.sort(key=lambda row: row[0])

#: Prepared locally; not registered for aeon's automatic archive downloads.
local_only = [row[0] for row in _TABLE if row[0] not in eegbench_paper]

#: Datasets that are not fully open access, so are not on Zenodo and cannot be
#: loaded through aeon. Results for them are still reported.
restricted = ["FibroLiverpool", "FibroUEA"]

#: All 74 prepared classification problems used by this repository.
eegbench = [row[0] for row in _TABLE]

#: The 28 problems anyone can download, the same list as aeon's ``eeg2026``.
eegbench_open = [name for name in eegbench_paper if name not in restricted]


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
    frequency = frame["frequency"].astype("Float64")
    frame["frequency"] = frequency.astype("Int64") if (frequency.dropna() % 1 == 0).all() else frequency
    frame["open"] = frame.index.isin(eegbench_open)
    frame["published_benchmark"] = frame.index.isin(eegbench_paper)
    frame["availability"] = ["local" if n in local_only else "restricted" if n in restricted else "aeon/Zenodo" for n in frame.index]
    return frame


def by_domain(domain: str, open_only: bool = False) -> list[str]:
    """Return the datasets from one application area.

    Parameters
    ----------
    domain : str
        One of the keys of :data:`DOMAINS`: ``"Med"``, ``"BCI"`` or ``"Psy"``.
    open_only : bool, default=False
        Select only datasets registered for automatic aeon/Zenodo downloads.

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
        if row[-1] == domain and (not open_only or row[0] in eegbench_open)
    ]


def metadata_markdown() -> str:
    """Return the archive metadata as a Markdown table, for the documentation."""
    header = [
        "Dataset", "Domain", "Channels", "Length", "Classes", "Subjects",
        "Train", "Test", "Hz", "Availability",
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
            "&mdash;" if pd.isna(row["frequency"]) else f'{row["frequency"]:g}',
            row["availability"],
        ]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)
