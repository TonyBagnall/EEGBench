"""The estimators on the leaderboard, and where each comes from.

This is metadata only. EEGBench holds no classifier code: classifiers designed
for EEG are in aeon-neuro, ports of general multivariate classifiers are in
multiverse.classification, and the rest are in aeon.

An estimator's name here is the name of its results directory. The family is
the grouping used in the paper: general purpose time series classifiers, deep
learning, methods designed for EEG, and standard classifiers.
"""

__all__ = [
    "ESTIMATORS",
    "FAMILIES",
    "PAPER_ESTIMATORS",
    "family",
    "estimator_table",
    "estimator_markdown",
]

import pandas as pd

#: Family codes and what they mean.
FAMILIES = {
    "TSML": "General purpose time series classifier",
    "Deep": "Deep learning, not specific to EEG",
    "EEG": "Designed for EEG",
    "Standard": "Standard classifier, no EEG or time series specific step",
}

# name: (family, library, description)
ESTIMATORS = {
    "HC2": ("TSML", "aeon", "HIVE-COTE v2.0"),
    "MRHydra": ("TSML", "aeon", "MultiROCKET-Hydra"),
    "Arsenal": ("TSML", "aeon", "Ensemble of ROCKET classifiers, an HC2 component"),
    "DrCIF": ("TSML", "aeon", "Diverse Representation CIF, an HC2 component"),
    "STC": ("TSML", "aeon", "Shapelet Transform Classifier, an HC2 component"),
    "TDE": ("TSML", "aeon", "Temporal Dictionary Ensemble, an HC2 component"),
    "ROCKET": ("TSML", "aeon", "Random convolutional kernel transform"),
    "MiniROCKET": ("TSML", "aeon", "MiniROCKET"),
    "QUANT": ("TSML", "aeon", "Quantile interval features"),
    "FreshPRINCE": ("TSML", "aeon", "TSFresh features with a rotation forest"),
    "CNN": ("Deep", "aeon", "Time-CNN"),
    "IT": ("Deep", "aeon", "InceptionTime"),
    "EEGNet": ("EEG", "Braindecode", "EEGNet"),
    "DCN": ("EEG", "Braindecode", "DeepConvNet"),
    "CSP-SVM": ("EEG", "MNE + scikit-learn", "Common Spatial Patterns then an SVM"),
    "R-MDM": ("EEG", "pyriemann", "Riemannian minimum distance to mean"),
    "R-KNN": ("EEG", "pyriemann", "Riemannian nearest neighbour"),
    "SVM": ("Standard", "scikit-learn", "Support vector machine"),
    "RandomForest": ("Standard", "scikit-learn", "Random forest"),
    "LogisticRegression": ("Standard", "scikit-learn", "Logistic regression"),
}

#: The eight classifiers compared in the paper, in the order of its Table 2.
PAPER_ESTIMATORS = ["R-MDM", "CSP-SVM", "CNN", "IT", "EEGNet", "DCN", "HC2", "MRHydra"]


def family(name: str) -> str:
    """Return the family code of an estimator, or ``""`` if it is not listed."""
    return ESTIMATORS[name][0] if name in ESTIMATORS else ""


def estimator_table() -> pd.DataFrame:
    """Return the estimator metadata, one row per estimator."""
    frame = pd.DataFrame.from_dict(
        ESTIMATORS, orient="index", columns=["family", "library", "description"]
    )
    frame.index.name = "estimator"
    return frame


def estimator_markdown() -> str:
    """Return the estimator metadata as a Markdown table, for the documentation."""
    header = ["Estimator", "Family", "Library", "Description"]
    rows = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for name, (code, library, description) in ESTIMATORS.items():
        rows.append(f"| {name} | {code} | {library} | {description} |")
    return "\n".join(rows)
