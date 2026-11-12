"""The Neuroverse classification archive: dataset lists and metadata.

The archive includes the 30 problems published by Rushbrooke et al. (2026)
and 61 additional local preparations. Use the supplied fixed train/test splits;
some protocols intentionally share subjects and some older identity mappings
remain incomplete. See docs/dataset-provenance.md for dataset-specific evidence.

The lists here are plain lists of dataset names, so they can be passed directly
to the experiment and leaderboard code::

    from neuroverse.datasets import neuroverse_study, by_type

    leaderboard(datasets=by_type("MI"), estimators=["HC2-500-pc", "MRHydra"])

Published open files are downloaded with ``aeon.datasets.load_classification``;
the newer preparations are loaded from local .ts files. The list is
held here rather than read from ``aeon.datasets.tsc_datasets.eeg2026`` so that
the leaderboard has the metadata beside the names and does not change when aeon
does.
"""

__all__ = [
    "neuroverse",
    "neuroverse_study",
    "neuroverse_82",
    "neuroverse_77",
    "neuroverse_76",
    "neuroverse_open",
    "neuroverse_paper",
    "excluded_archive",
    "local_only",
    "restricted",
    "DOMAINS",
    "PROBLEM_FAMILIES",
    "BCI_TYPES",
    "PROBLEM_TYPE_TABS",
    "STUDY_TAXONOMY",
    "metadata",
    "by_domain",
    "by_type",
    "metadata_markdown",
]

import pandas as pd

#: The three application areas the archive covers, as labelled in Table 1.
DOMAINS = {
    "Med": "Medical",
    "BCI": "Brain-computer interface",
    "Psy": "Psychology",
}

#: Top-level problem families for the 82-problem scalp EEG study.
PROBLEM_FAMILIES = {
    "BCI": "Brain-computer interface",
    "Clinical": "Clinical and physiological",
    "Cognitive": "Cognitive and affective",
}

#: Sub-paradigms within the BCI family.
BCI_TYPES = {
    "MI": "Motor imagery",
    "ME": "Motor execution and movement intention",
    "ERP": "Event-related potentials (P300 / SCP)",
    "VEP": "Visual evoked potentials (SSVEP / c-VEP)",
    "Speech": "Decoded and imagined speech",
}

#: Ordered problem-type tabs used on the interactive leaderboard.
PROBLEM_TYPE_TABS = {
    "All": "All Scalp EEG",
    "BCI": "BCI (All)",
    "MI": "Motor Imagery",
    "ME": "Motor Execution",
    "ERP": "ERP / P300",
    "VEP": "VEP / SSVEP",
    "Speech": "Speech BCI",
    "Clinical": "Clinical",
    "Cognitive": "Cognitive",
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
neuroverse_paper = [row[0] for row in _TABLE]

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
    ("NBackAudioCondition", 16, 12, 600, 23, 11520, 5040, 200, "Psy"),
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

_TABLE += [('ImaginedHandsHaptics', 32, 2, 2495, 20, 3083, 1034, 500, 'BCI')]

_TABLE += [('ImaginedAnkleRest', 28, 2, 1000, 6, 264, 132, 250, 'BCI')]

_TABLE += [('ImaginedHandsFeedback', 16, 2, 1250, 55, 6560, 2240, 250, 'BCI')]

_TABLE += [('ImaginedHandsOnline', 28, 2, 1000, 10, 2123, 1519, 250, 'BCI'), ('ImaginedHandsCrossSession', 28, 2, 1000, 14, 2400, 960, 250, 'BCI'), ('ImaginedHandPupils', 32, 2, 3072, 30, 1150, 400, 512, 'BCI'), ('ImaginedHandsPhysiology', 64, 2, 1536, 52, 7880, 2640, 512, 'BCI'), ('ImaginedHandMusicTempo', 19, 2, 20000, 18, 1698, 643, 1000, 'BCI')]

_TABLE += [('AlzheimersAuditory', 19, 3, 1000, 33, 2020, 1000, 250, 'Med')]

_TABLE += [('ParkinsonsRestIowa', 60, 2, 2000, 149, 4598, 1306, 500, 'Med')]

_TABLE += [('ParkinsonsRestUCSD', 32, 2, 2048, 31, 1126, 380, 512, 'Med')]

_TABLE += [('ImaginedFingers', 60, 5, 3072, 20, 4481, 1500, 512, 'BCI')]

_TABLE += [
    ("MigraineRest", 128, 2, 2048, 33, 1920, 750, 512, "Med"),
    ("ParkinsonsWalking", 53, 2, 1000, 133, 6493, 2100, 250, "Med"),
    ("PsychosisRestFirst", 61, 2, 4000, 82, 4657, 1601, 1000, "Med"),
    ("PsychosisRestSecond", 61, 2, 4000, 61, 3472, 1239, 1000, "Med"),
    ("TBIAuditoryOddball", 61, 3, 500, 87, 4848, 1748, 500, "Med"),
]

_TABLE.sort(key=lambda row: row[0])

#: Prepared locally; not registered for aeon's automatic archive downloads.
local_only = [row[0] for row in _TABLE if row[0] not in neuroverse_paper]

#: Datasets that are not fully open access, so are not on Zenodo and cannot be
#: loaded through aeon. Results for them are still reported.
restricted = ["FibroLiverpool", "FibroUEA"]

#: All 91 prepared classification problems used by this repository.
neuroverse = [row[0] for row in _TABLE]

#: The 28 problems anyone can download, the same list as aeon's ``eeg2026``.
neuroverse_open = [name for name in neuroverse_paper if name not in restricted]

#: Problem-type assignment ``(family, bci_type)`` for the 82 selected scalp EEG
#: classification problems. Strict scalp-EEG motor imagery (``MI``) has 30
#: problems, ``Clinical`` has 20 problems, and the 6 executed/movement-intention
#: motor tasks sit in ``ME``. MEG (FaceDetection, HandMovementDirection,
#: MatchWords, MindReading), ECoG (MotorImagery), and the four older excluded
#: problems (Blink, ButtonPress, EpilepticSeizures, Sleep) remain in the
#: 91-item archive registry above.
STUDY_TAXONOMY: dict[str, tuple[str, str]] = {
    "ALSAttention": ("BCI", "ERP"),
    "Alzheimers": ("Clinical", ""),
    "AlzheimersAuditory": ("Clinical", ""),
    "ArmCoordination": ("BCI", "ME"),
    "ArmMovements": ("BCI", "ME"),
    "ChildhoodSeizures": ("Clinical", ""),
    "ClinicalSleepStages": ("Clinical", ""),
    "CodedFlickerTargets": ("BCI", "VEP"),
    "CodedSymbols": ("BCI", "VEP"),
    "CovidSurvivors": ("Clinical", ""),
    "EyesOpenShut": ("Cognitive", ""),
    "FeedbackButton": ("Cognitive", ""),
    "FeetHands": ("BCI", "ME"),
    "FibroLiverpool": ("Clinical", ""),
    "FibroUEA": ("Clinical", ""),
    "FingerMovements": ("BCI", "ME"),
    "FlickerAttention": ("BCI", "VEP"),
    "FlickerSymbols": ("BCI", "VEP"),
    "FlickerTargets": ("BCI", "VEP"),
    "GameTargets": ("BCI", "ERP"),
    "ImaginedAnkleRest": ("BCI", "MI"),
    "ImaginedArmMovements": ("BCI", "MI"),
    "ImaginedArmTasks": ("BCI", "MI"),
    "ImaginedCommands": ("BCI", "Speech"),
    "ImaginedFeetHands": ("BCI", "MI"),
    "ImaginedFingers": ("BCI", "MI"),
    "ImaginedGrasps": ("BCI", "MI"),
    "ImaginedGripForce": ("BCI", "MI"),
    "ImaginedHandFeetTongue": ("BCI", "MI"),
    "ImaginedHandFootActions": ("BCI", "MI"),
    "ImaginedHandGestures": ("BCI", "MI"),
    "ImaginedHandMusicTempo": ("BCI", "MI"),
    "ImaginedHandPupils": ("BCI", "MI"),
    "ImaginedHandSides": ("BCI", "MI"),
    "ImaginedHandTraining": ("BCI", "MI"),
    "ImaginedHandsCrossSession": ("BCI", "MI"),
    "ImaginedHandsEmbodiment": ("BCI", "MI"),
    "ImaginedHandsFeedback": ("BCI", "MI"),
    "ImaginedHandsFeet": ("BCI", "MI"),
    "ImaginedHandsHaptics": ("BCI", "MI"),
    "ImaginedHandsOnline": ("BCI", "MI"),
    "ImaginedHandsPhysiology": ("BCI", "MI"),
    "ImaginedHandsRobot": ("BCI", "MI"),
    "ImaginedHandsStroke": ("BCI", "MI"),
    "ImaginedLeftRightHand": ("BCI", "MI"),
    "ImaginedLeftRightHandRest": ("BCI", "MI"),
    "ImaginedOpenCloseFist": ("BCI", "MI"),
    "ImaginedRightHandFeet": ("BCI", "MI"),
    "ImaginedRightHandFeetRest": ("BCI", "MI"),
    "InnerSpeech": ("BCI", "Speech"),
    "LongIntervalTask": ("Clinical", ""),
    "LowCost": ("BCI", "MI"),
    "MatchingPennies": ("BCI", "ME"),
    "MentalArithmetic": ("Cognitive", ""),
    "MigraineRest": ("Clinical", ""),
    "NBackAudioCondition": ("Cognitive", ""),
    "ObsessiveCompulsiveSymptoms": ("Clinical", ""),
    "OpenCloseFist": ("BCI", "ME"),
    "ParkinsonsPedalling": ("Clinical", ""),
    "ParkinsonsRest": ("Clinical", ""),
    "ParkinsonsRestIowa": ("Clinical", ""),
    "ParkinsonsRestUCSD": ("Clinical", ""),
    "ParkinsonsWalking": ("Clinical", ""),
    "PhotoStimulation": ("Clinical", ""),
    "PronouncedSpeech": ("BCI", "Speech"),
    "PsychosisRestFirst": ("Clinical", ""),
    "PsychosisRestSecond": ("Clinical", ""),
    "RestingEyeState": ("Cognitive", ""),
    "SelfRegulationSCP1": ("BCI", "ERP"),
    "SelfRegulationSCP2": ("BCI", "ERP"),
    "ShortIntervalTask": ("Clinical", ""),
    "SitStand": ("BCI", "MI"),
    "SongFamiliarity": ("Cognitive", ""),
    "SpellerFlashes": ("BCI", "ERP"),
    "SymbolAttention": ("BCI", "ERP"),
    "TBIAuditoryOddball": ("Clinical", ""),
    "VideoEmotions": ("Cognitive", ""),
    "VisualSpeech": ("BCI", "Speech"),
    "VisualSubjects": ("BCI", "ERP"),
    "WalkingTargets": ("BCI", "ERP"),
    "WirelessFlicker": ("BCI", "VEP"),
    "WordRelatedness": ("Cognitive", ""),
}

#: The 82 selected scalp EEG classification problems in the extended benchmark.
neuroverse_study = sorted(STUDY_TAXONOMY)
neuroverse_82 = neuroverse_study
neuroverse_77 = neuroverse_study  # backwards-compatible alias
neuroverse_76 = neuroverse_study  # backwards-compatible alias

#: Registered archive problems excluded from the 82-problem scalp EEG study.
excluded_archive = [name for name in neuroverse if name not in STUDY_TAXONOMY]


def metadata() -> pd.DataFrame:
    """Return the archive metadata, one row per dataset.

    Returns
    -------
    pd.DataFrame
        Indexed by dataset name, with the columns of Table 1, availability
        flags, and the 82-problem study taxonomy (``family``, ``bci_type``,
        ``problem_type``, ``study_selected``).
    """
    frame = pd.DataFrame(_TABLE, columns=_COLUMNS).set_index("dataset")
    frame["subjects"] = frame["subjects"].astype("Int64")
    frequency = frame["frequency"].astype("Float64")
    frame["frequency"] = frequency.astype("Int64") if (frequency.dropna() % 1 == 0).all() else frequency
    frame["open"] = frame.index.isin(neuroverse_open)
    frame["published_benchmark"] = frame.index.isin(neuroverse_paper)
    frame["availability"] = [
        "local" if n in local_only else "restricted" if n in restricted else "aeon/Zenodo"
        for n in frame.index
    ]
    frame["study_selected"] = frame.index.isin(STUDY_TAXONOMY)
    frame["study_76"] = frame["study_selected"]
    frame["family"] = [STUDY_TAXONOMY.get(n, ("", ""))[0] for n in frame.index]
    frame["bci_type"] = [STUDY_TAXONOMY.get(n, ("", ""))[1] for n in frame.index]
    frame["problem_type"] = [
        bci if bci else (fam if fam else "Excluded")
        for fam, bci in (STUDY_TAXONOMY.get(n, ("", "")) for n in frame.index)
    ]
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
        if row[-1] == domain and (not open_only or row[0] in neuroverse_open)
    ]


def by_type(problem_type: str = "All") -> list[str]:
    """Return datasets from the 82-problem scalp EEG study by problem type.

    Parameters
    ----------
    problem_type : str, default="All"
        One of ``"All"`` (82), a top-level family (``"BCI"``, ``"Clinical"``,
        ``"Cognitive"``), or a BCI sub-type (``"MI"``, ``"ME"``, ``"ERP"``,
        ``"VEP"``, ``"Speech"``).

    Returns
    -------
    list of str
        Dataset names in alphabetical order.
    """
    if problem_type == "All":
        return list(neuroverse_study)
    if problem_type in PROBLEM_FAMILIES:
        return [
            name for name in neuroverse_study if STUDY_TAXONOMY[name][0] == problem_type
        ]
    if problem_type in BCI_TYPES:
        return [
            name for name in neuroverse_study if STUDY_TAXONOMY[name][1] == problem_type
        ]
    valid = ", ".join(PROBLEM_TYPE_TABS)
    raise ValueError(f"problem_type must be one of {valid}, not {problem_type!r}")


def metadata_markdown() -> str:
    """Return the archive metadata as a Markdown table, for the documentation."""
    header = [
        "Dataset", "Domain", "Study type", "Channels", "Length", "Classes",
        "Subjects", "Train", "Test", "Hz", "Availability",
    ]
    rows = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for name, row in metadata().iterrows():
        study_type = "&mdash;" if row["problem_type"] == "Excluded" else row["problem_type"]
        cells = [
            name,
            row["domain"],
            study_type,
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


# Backwards-compatible aliases for scripts written before the Neuroverse rename.
eegbench = neuroverse
eegbench_76 = neuroverse_study
eegbench_open = neuroverse_open
eegbench_paper = neuroverse_paper
