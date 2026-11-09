"""Tests for the archive lists and metadata."""

import pytest

from eegbench.datasets import (
    DOMAINS,
    by_domain,
    eegbench,
    eegbench_open,
    eegbench_paper,
    local_only,
    metadata,
    restricted,
)
from eegbench.estimators import ESTIMATORS, FAMILIES, PAPER_ESTIMATORS


def test_archive_lists():
    """All 82 problems, with published and local subsets explicitly identified."""
    assert len(eegbench) == len(set(eegbench)) == 82
    assert eegbench == sorted(eegbench)
    assert len(eegbench_paper) == 30 and len(local_only) == 52
    assert set(eegbench_paper).isdisjoint(local_only)
    assert len(eegbench_open) == 28
    assert set(eegbench) - set(eegbench_open) == set(restricted) | set(local_only)
    assert {'ImaginedHandFeetTongue', 'ClinicalSleepStages', 'VideoEmotions', 'ImaginedLeftRightHand', 'ImaginedRightHandFeet'} <= set(eegbench)
    assert not {'BCIIV2a', 'ISRUCSleep', 'FACED', 'Weibo2014', 'AlexMI'} & set(eegbench)


def test_domains_partition_the_archive():
    """Every dataset is in exactly one domain."""
    split = [name for domain in DOMAINS for name in by_domain(domain)]
    assert sorted(split) == sorted(eegbench)
    assert "FibroUEA" in by_domain("Med")
    assert "FibroUEA" not in by_domain("Med", open_only=True)
    with pytest.raises(ValueError):
        by_domain("Sleep")


def test_metadata():
    """The table describes the current local versions, including corrections."""
    frame = metadata()
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
    assert list(frame.index) == eegbench
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
    assert frame['frequency'].isna().loc['NBackAudioCondition']
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
    import eegbench.datasets as datasets
    monkeypatch.setattr(datasets, '_TABLE', datasets._TABLE + [('FractionalRateExample', 2, 2, 32, 2, 4, 2, 62.5, 'Psy')])
    assert datasets.metadata().loc['FractionalRateExample', 'frequency'] == 62.5
    markdown = datasets.metadata_markdown()
    assert '| 62.5 |' in markdown
    assert '| 500.0 |' not in markdown
