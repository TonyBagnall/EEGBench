"""Tests for the archive lists and metadata."""

import pytest

from neuroverse.datasets import (
    DOMAINS,
    by_domain,
    local_only,
    metadata,
    neuroverse,
    neuroverse_open,
    neuroverse_paper,
    restricted,
)
from neuroverse.estimators import ESTIMATORS, FAMILIES, PAPER_ESTIMATORS


def test_archive_lists():
    """All 91 problems, with published and local subsets explicitly identified."""
    n_total = 91
    n_paper = 30
    n_local = n_total - n_paper
    n_open = 28
    assert len(neuroverse) == len(set(neuroverse)) == n_total
    assert neuroverse == sorted(neuroverse)
    assert len(neuroverse_paper) == n_paper and len(local_only) == n_local
    assert set(neuroverse_paper).isdisjoint(local_only)
    assert len(neuroverse_open) == n_open
    assert set(neuroverse) - set(neuroverse_open) == set(restricted) | set(local_only)
    assert {
        'ImaginedFingers',
        'MigraineRest',
        'ParkinsonsWalking',
        'PsychosisRestFirst',
        'PsychosisRestSecond',
        'TBIAuditoryOddball',
        'ImaginedHandFeetTongue',
        'ClinicalSleepStages',
        'VideoEmotions',
        'ImaginedLeftRightHand',
        'ImaginedRightHandFeet',
    } <= set(neuroverse)
    assert not {'BCIIV2a', 'ISRUCSleep', 'FACED', 'Weibo2014', 'AlexMI'} & set(neuroverse)


def test_domains_partition_the_archive():
    """Every dataset is in exactly one domain."""
    split = [name for domain in DOMAINS for name in by_domain(domain)]
    assert sorted(split) == sorted(neuroverse)
    assert "FibroUEA" in by_domain("Med")
    assert "FibroUEA" not in by_domain("Med", open_only=True)
    with pytest.raises(ValueError):
        by_domain("Sleep")


def test_metadata():
    """The table describes the current local versions, including corrections."""
    frame = metadata()
    assert frame.loc["MigraineRest", ["subjects", "channels", "classes", "length", "train_size", "test_size", "frequency"]].tolist() == [33, 128, 2, 2048, 1920, 750, 512]
    assert frame.loc["ParkinsonsWalking", ["subjects", "channels", "classes", "length", "train_size", "test_size", "frequency"]].tolist() == [133, 53, 2, 1000, 6493, 2100, 250]
    assert frame.loc["PsychosisRestFirst", ["subjects", "channels", "classes", "length", "train_size", "test_size", "frequency"]].tolist() == [82, 61, 2, 4000, 4657, 1601, 1000]
    assert frame.loc["PsychosisRestSecond", ["subjects", "channels", "classes", "length", "train_size", "test_size", "frequency"]].tolist() == [61, 61, 2, 4000, 3472, 1239, 1000]
    assert frame.loc["TBIAuditoryOddball", ["subjects", "channels", "classes", "length", "train_size", "test_size", "frequency"]].tolist() == [87, 61, 3, 500, 4848, 1748, 500]
    assert frame.loc["ImaginedFingers", ["subjects", "channels", "classes", "length", "train_size", "test_size", "frequency"]].tolist() == [20, 60, 5, 3072, 4481, 1500, 512]
    assert frame.loc["ImaginedRightHandFeetRest", ["subjects","channels","train_size","test_size","frequency"]].tolist() == [1,24,150,40,250]
    assert frame.loc["ImaginedLeftRightHandRest", ["subjects","channels","train_size","test_size","frequency"]].tolist() == [1,24,480,240,250]
    assert frame.loc["ImaginedHandFootActions", ["subjects","channels","train_size","test_size","frequency"]].tolist() == [60,11,2727,930,125]
    assert frame.loc["ImaginedHandGestures", ["subjects","channels","train_size","test_size","frequency"]].tolist() == [11,17,382,143,500]
    assert frame.loc["ImaginedArmTasks", ["subjects","channels","train_size","test_size","frequency"]].tolist() == [12,17,3240,1080,1000]
    assert frame.loc['SymbolAttention', ["subjects","channels","train_size","test_size","frequency"]].tolist() == [19,8,521259,175180,256]
    assert frame.loc['ArmCoordination', ["subjects","channels","train_size","test_size","frequency"]].tolist() == [8,64,1498,505,500]
    assert frame.loc["WalkingTargets", ["subjects","channels","train_size","test_size","frequency"]].tolist() == [15,42,3600,900,100]
    assert frame.loc['ObsessiveCompulsiveSymptoms', ['subjects','channels','train_size','test_size','frequency']].tolist() == [35,52,7754,2660,500]
    assert frame.loc['ParkinsonsPedalling', ['subjects','channels','train_size','test_size','frequency']].tolist() == [39,63,2123,842,500]
    assert frame.loc['ParkinsonsRest', ['subjects','channels','train_size','test_size','frequency']].tolist() == [55,63,1216,420,500]
    assert frame.loc['ImaginedHandsStroke', 'channels'] == 29
    assert frame.loc['ImaginedHandsStroke', 'classes'] == 2
    assert frame.loc['ImaginedHandsStroke', 'subjects'] == 46
    assert frame.loc['ImaginedHandsStroke', 'train_size'] == 1400
    assert frame.loc['ImaginedHandsStroke', 'test_size'] == 440
    assert frame.loc['ImaginedHandsStroke', 'frequency'] == 500
    assert frame.loc['RestingEyeState', 'channels'] == 16
    assert frame.loc['RestingEyeState', 'classes'] == 2
    assert frame.loc['RestingEyeState', 'subjects'] == 19
    assert frame.loc['RestingEyeState', 'train_size'] == 140
    assert frame.loc['RestingEyeState', 'test_size'] == 50
    assert frame.loc['GameTargets', 'channels'] == 8
    assert frame.loc['GameTargets', 'classes'] == 2
    assert frame.loc['GameTargets', 'subjects'] == 22
    assert frame.loc['GameTargets', 'train_size'] == 20400
    assert frame.loc['GameTargets', 'test_size'] == 6000
    assert frame.loc['CodedFlickerTargets', 'channels'] == 28
    assert frame.loc['CodedFlickerTargets', 'classes'] == 4
    assert frame.loc['CodedFlickerTargets', 'subjects'] == 12
    assert frame.loc['CodedFlickerTargets', 'train_size'] == 2160
    assert frame.loc['CodedFlickerTargets', 'test_size'] == 720
    assert frame.loc['ImaginedHandTraining', 'channels'] == 22
    assert frame.loc['ImaginedHandTraining', 'classes'] == 2
    assert frame.loc['ImaginedHandTraining', 'subjects'] == 18
    assert frame.loc['ImaginedHandTraining', 'train_size'] == 5568
    assert frame.loc['ImaginedHandTraining', 'test_size'] == 1588
    assert list(frame.index) == neuroverse
    assert frame.loc["Alzheimers", "length"] == 15000
    assert frame.loc['FingerMovements', 'length'] == 50
    assert frame.loc['FingerMovements', 'frequency'] == 100
    assert frame.loc["SitStand", "classes"] == 4
    assert frame["open"].sum() == 28
    assert frame.loc['VideoEmotions', 'classes'] == 8
    assert frame.loc['VideoEmotions', 'channels'] == 25
    assert frame.loc['MatchWords', 'channels'] == 156
    assert frame.loc['FlickerSymbols', 'channels'] == 64
    assert frame.loc['FlickerSymbols', 'classes'] == 40
    assert frame.loc['FlickerSymbols', 'train_size'] == 6240
    assert frame.loc['FlickerSymbols', 'test_size'] == 2160
    assert frame.loc['FlickerTargets', 'classes'] == 12
    assert frame.loc['ImaginedGripForce', 'channels'] == 14
    assert frame.loc['ImaginedGripForce', 'classes'] == 3
    assert frame.loc['ImaginedGripForce', 'subjects'] == 10
    assert frame.loc['ImaginedGripForce', 'train_size'] == 240
    assert frame.loc['ImaginedGripForce', 'test_size'] == 60
    assert frame.loc['ImaginedHandSides', 'channels'] == 3
    assert frame.loc['ImaginedHandsFeet', 'channels'] == 13
    assert frame.loc['ImaginedHandsFeet', 'train_size'] == 1365
    assert frame.loc['SpellerFlashes', 'train_size'] == 12600
    assert frame.loc['ALSAttention', 'test_size'] == 19200
    assert frame.loc['WirelessFlicker', 'classes'] == 5
    assert frame.loc['WirelessFlicker', 'channels'] == 14
    assert frame.loc['WirelessFlicker', 'length'] == 640
    assert frame.loc['ClinicalSleepStages', 'train_size'] == 64889
    assert frame.loc['ImaginedLeftRightHand', 'channels'] == 60
    assert frame.loc['ImaginedLeftRightHand', 'availability'] == 'local'
    assert frame.loc['NBackAudioCondition', 'classes'] == 12
    assert frame.loc['NBackAudioCondition', 'subjects'] == 23
    assert frame.loc['NBackAudioCondition', 'train_size'] == 11520
    assert frame.loc['NBackAudioCondition', 'test_size'] == 5040
    assert frame.loc['NBackAudioCondition', 'availability'] == 'local'
    assert frame.loc['NBackAudioCondition', 'frequency'] == 200
    assert frame.loc['VisualSubjects', 'classes'] == 2
    assert frame.loc['VisualSubjects', 'channels'] == 16
    assert frame.loc['VisualSubjects', 'subjects'] == 64
    assert frame.loc['VisualSubjects', 'length'] == 512
    assert frame.loc['VisualSubjects', 'train_size'] == 42189
    assert frame.loc['VisualSubjects', 'test_size'] == 18826
    assert frame.loc['VisualSubjects', 'availability'] == 'local'
    assert frame.loc['FlickerAttention', 'classes'] == 4
    assert frame.loc['FlickerAttention', 'subjects'] == 12
    assert frame.loc['FlickerAttention', 'train_size'] == 576
    assert frame.loc['FlickerAttention', 'test_size'] == 352
    assert frame.loc['WordRelatedness', 'channels'] == 30
    assert frame.loc['WordRelatedness', 'subjects'] == 40
    assert frame.loc['WordRelatedness', 'train_size'] == 3600
    assert frame.loc['WordRelatedness', 'test_size'] == 1200
    assert frame.loc['WordRelatedness', 'frequency'] == 1024
    assert frame.loc['CodedSymbols', 'classes'] == 20
    assert frame.loc['CodedSymbols', 'channels'] == 8
    assert frame.loc['CodedSymbols', 'subjects'] == 30
    assert frame.loc['CodedSymbols', 'length'] == 16128
    assert frame.loc['CodedSymbols', 'train_size'] == 2200
    assert frame.loc['CodedSymbols', 'test_size'] == 800
    assert frame.loc['CodedSymbols', 'frequency'] == 512
    for name in ['ArmMovements', 'ImaginedArmMovements']:
        assert frame.loc[name, 'classes'] == 7
        assert frame.loc[name, 'channels'] == 61
        assert frame.loc[name, 'length'] == 1536
        assert frame.loc[name, 'subjects'] == 15
        assert frame.loc[name, 'train_size'] == 4620
        assert frame.loc[name, 'test_size'] == 1680
        assert frame.loc[name, 'frequency'] == 512


def test_estimators():
    """Every estimator has a known family, and the paper's eight are listed."""
    assert {family for family, _, _ in ESTIMATORS.values()} <= set(FAMILIES)
    assert set(PAPER_ESTIMATORS) <= set(ESTIMATORS)


def test_fractional_sampling_frequency_is_preserved(monkeypatch):
    """Native rates such as 62.5 Hz must not be rounded to integer Hz."""
    import neuroverse.datasets as datasets
    monkeypatch.setattr(datasets, '_TABLE', datasets._TABLE + [('FractionalRateExample', 2, 2, 32, 2, 4, 2, 62.5, 'Psy')])
    assert datasets.metadata().loc['FractionalRateExample', 'frequency'] == 62.5
    markdown = datasets.metadata_markdown()
    assert '| 62.5 |' in markdown
    assert '| 500.0 |' not in markdown


def test_study_taxonomy_partitions_selected_problems():
    """The 82-problem scalp EEG taxonomy partitions families (30 MI, 20 Clinical, 8 Cognitive)."""
    from neuroverse.datasets import (
        BCI_TYPES,
        PROBLEM_FAMILIES,
        by_type,
        excluded_archive,
        neuroverse_76,
        neuroverse_77,
        neuroverse_82,
        neuroverse_study,
    )

    n_selected = 82
    n_mi = 30
    n_clinical = 20
    n_cognitive = 8
    expected_me = [
        "ArmCoordination",
        "ArmMovements",
        "FeetHands",
        "FingerMovements",
        "MatchingPennies",
        "OpenCloseFist",
    ]

    assert len(neuroverse_study) == n_selected
    assert neuroverse_82 == neuroverse_77 == neuroverse_76 == neuroverse_study
    assert by_type("All") == neuroverse_study
    assert len(by_type("MI")) == n_mi
    assert len(by_type("Clinical")) == n_clinical
    assert len(by_type("Cognitive")) == n_cognitive
    assert {
        "MigraineRest",
        "ParkinsonsWalking",
        "PsychosisRestFirst",
        "PsychosisRestSecond",
        "TBIAuditoryOddball",
    } <= set(by_type("Clinical"))
    assert "ImaginedFingers" in by_type("MI")
    assert by_type("ME") == expected_me
    assert set(by_type("MI")).isdisjoint(by_type("ME"))
    assert set(neuroverse_study).isdisjoint(excluded_archive)
    assert sorted(neuroverse_study + excluded_archive) == neuroverse

    family_parts = [by_type(fam) for fam in PROBLEM_FAMILIES]
    for idx, left in enumerate(family_parts):
        for right in family_parts[idx + 1 :]:
            assert set(left).isdisjoint(right)
    assert sorted(name for part in family_parts for name in part) == neuroverse_study

    bci_parts = [by_type(sub) for sub in BCI_TYPES]
    for idx, left in enumerate(bci_parts):
        for right in bci_parts[idx + 1 :]:
            assert set(left).isdisjoint(right)
    assert sorted(name for part in bci_parts for name in part) == by_type("BCI")

    frame = metadata()
    assert set(frame.index[frame["problem_type"] == "Excluded"]) == set(excluded_archive)
    with pytest.raises(ValueError, match="problem_type"):
        by_type("UnknownType")


def test_bakeoff_estimators_metadata_contract():
    """The 90 configurations partition into 72 distinct canonical classifiers and 18 variants."""
    from neuroverse.estimators import (
        BAKEOFF_ESTIMATORS,
        CANONICAL_ESTIMATORS,
        PARADIGMS,
        TSML_FAMILIES,
        VARIANT_ESTIMATORS,
        estimator_info,
        estimator_table,
    )

    active_table = estimator_table(active_only=True)
    assert sorted(active_table.index, key=str.lower) == BAKEOFF_ESTIMATORS
    assert set(active_table["paradigm"]) <= set(PARADIGMS)
    assert set(active_table["tsml_family"]) <= set(TSML_FAMILIES)

    assert len(CANONICAL_ESTIMATORS) + len(VARIANT_ESTIMATORS) == len(BAKEOFF_ESTIMATORS)
    assert set(CANONICAL_ESTIMATORS).isdisjoint(VARIANT_ESTIMATORS)
    canonical_bases = [estimator_info(name)["base_method"] for name in CANONICAL_ESTIMATORS]
    assert len(canonical_bases) == len(set(canonical_bases)) == 72
    assert set(active_table["base_method"]) == set(canonical_bases)

    for base_fm in ("CBraMod", "LaBraM"):
        assert estimator_info(base_fm)["is_canonical"]
        assert not estimator_info(base_fm)["is_ablation"]
        assert estimator_info(f"{base_fm}-random")["is_ablation"]
        assert not estimator_info(f"{base_fm}-random")["is_canonical"]
        assert estimator_info(base_fm)["base_method"] == estimator_info(f"{base_fm}-random")["base_method"]
