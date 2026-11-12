"""Unit tests for ParkinsonsWalking, TBIAuditoryOddball and MigraineRest clinical adapters."""
import numpy as np
import pytest

from tools.prepare_chamanzar2020 import migraine_participant_plan, resting_fixation_blocks
from tools.prepare_eegdash_pd_walk import walk_continuous_segments, walk_participant_plan
from tools.prepare_eegdash_tbi import oddball_epochs, tbi_participant_plan


def test_walk_participant_plan_excludes_rest_only_subjects_and_stratifies_groups():
    hc_walk = ['002', '003', '004', '006']
    pd_walk = ['029', '030', '031', '032']
    rest_only = [('001', 'HC0001', 'HC'), ('036', 'PD0008', 'PD')]
    participants = [
        dict(participant_id=f'sub-{p}', subject_id=f'HC{p}', group='HC') for p in hc_walk
    ] + [
        dict(participant_id=f'sub-{p}', subject_id=f'PD{p}', group='PD') for p in pd_walk
    ] + [
        dict(participant_id=f'sub-{p}', subject_id=sid, group=g) for p, sid, g in rest_only
    ]
    lookup, train, excluded = walk_participant_plan(participants, hc_walk + pd_walk)
    assert set(lookup) == set(hc_walk + pd_walk)
    assert train == {'002', '003', '004', '029', '030', '031'}
    assert {e['participant_id'] for e in excluded} == {p for p, _, _ in rest_only}


def test_walk_continuous_segments_exclude_break_cnt_span_and_ignore_initial_boundary():
    n_channels = 3
    seg_one_end = 2500
    break_len = 200
    total_samples = 5000
    rng = np.random.default_rng(11)
    eeg = rng.standard_normal((n_channels, total_samples))
    events = [
        dict(type='boundary', latency=1.0, duration=500.5),
        dict(type='bgin', latency=589.0, duration=1.0),
        dict(type='break cnt', latency=float(seg_one_end + 1), duration=float(break_len)),
    ]
    segments, audit = walk_continuous_segments(events, eeg)
    assert segments == [(0, seg_one_end), (seg_one_end + break_len, total_samples)]
    assert len(audit['discontinuity_events']) == 1


def test_tbi_participant_plan_removes_cross_cohort_and_duplicate_identities():
    rows = [
        dict(participant_id='sub-001', Original_ID='3005', URSI='M1', Group='1'),
        dict(participant_id='sub-002', Original_ID='3006', URSI='M2', Group='1'),
        dict(participant_id='sub-027', Original_ID='3013', URSI='M38342', Group='1'),
        dict(participant_id='sub-028', Original_ID='3013', URSI='M38432', Group='1'),
        dict(participant_id='sub-009', Original_ID='3007', URSI='M9', Group='1'),
        dict(participant_id='sub-010', Original_ID='3010', URSI='M10', Group='0'),
        dict(participant_id='sub-011', Original_ID='3011', URSI='M11', Group='0'),
        dict(participant_id='sub-021', Original_ID='3032', URSI='M30454', Group='0'),
        dict(participant_id='sub-030', Original_ID='3033', URSI='M30', Group='0'),
        dict(participant_id='sub-081', Original_ID='35957', URSI='M35957', Group='2'),
        dict(participant_id='sub-071', Original_ID='10001', URSI='Q1', Group='2'),
        dict(participant_id='sub-072', Original_ID='10002', URSI='Q2', Group='2'),
        dict(participant_id='sub-073', Original_ID='10003', URSI='Q3', Group='2'),
        dict(participant_id='sub-074', Original_ID='10004', URSI='Q4', Group='2'),
    ]
    lookup, train, excluded = tbi_participant_plan(rows)
    assert '028' not in lookup and '081' not in lookup
    assert {e['participant_id'] for e in excluded} == {'028', '081'}
    assert len(train) == 9


def test_oddball_epochs_extract_deviant_windows_and_skip_boundary_crossings():
    hz = 500
    pre_samples = 100
    post_samples = 400
    epoch_len = pre_samples + post_samples
    n_samples = 4000
    events = [
        dict(onset='0.0', value='boundary', trial_type='STATUS'),
        dict(onset='1.0', value='S201', trial_type='Standard Tone'),
        dict(onset='2.0', value='S200', trial_type='Target Tone'),
        dict(onset='3.9', value='boundary', trial_type='STATUS'),
        dict(onset='4.0', value='S202', trial_type='Novel Tone'),
        dict(onset='6.0', value='S202', trial_type='Novel Tone'),
    ]
    native_events = [
        dict(type='boundary', latency=1.0),
        dict(type='S201', latency=501.0),
        dict(type='S200', latency=1001.0),
        dict(type='boundary', latency=1951.0),
        dict(type='S202', latency=2001.0),
        dict(type='S202', latency=3001.0),
    ]
    retained, skipped, boundaries = oddball_epochs(
        events, native_events, hz, n_samples, pre_samples=pre_samples, post_samples=post_samples
    )
    assert boundaries == [1950]
    assert len(retained) == 2
    assert retained[0]['start_sample'] == 1000 - pre_samples
    assert retained[0]['end_sample'] - retained[0]['start_sample'] == epoch_len
    assert retained[1]['start_sample'] == 3000 - pre_samples
    assert len(skipped) == 1 and 'boundary' in skipped[0]['reason']


def test_migraine_plan_and_fixation_blocks_cap_duration_and_exclude_medicated():
    demo = [
        {'P#': p, 'Gender': 'Female', 'Age': '25', 'Aura?': '', 'Medication before the recording session?': ''}
        for p in ['C1', 'C3', 'C4', 'C5']
    ] + [
        {'P#': p, 'Gender': 'Female', 'Age': '25', 'Aura?': 'Yes', 'Medication before the recording session?': 'No'}
        for p in ['M1', 'M3', 'M4', 'M5']
    ] + [
        {'P#': 'M2', 'Gender': 'Female', 'Age': '23', 'Aura?': 'Yes', 'Medication before the recording session?': 'Yes'},
    ]
    files = [dict(name=f'{p}.zip') for p in ['C1', 'C2', 'C3', 'C4', 'C5', 'M1', 'M2', 'M3', 'M4', 'M5']]
    eligible, train, excluded = migraine_participant_plan(demo, files)
    assert set(eligible) == {'C1', 'C3', 'C4', 'C5', 'M1', 'M3', 'M4', 'M5'}
    assert {e['participant_id'] for e in excluded} == {'C2', 'M2'}
    assert train == {'C1', 'C3', 'C4', 'M1', 'M3', 'M4'}

    hz = 512
    window_points = 2048
    windows_per_block = 30
    block_points = window_points * windows_per_block
    max_blocks = 3
    low2_events = []
    cursor = 1000
    for _ in range(5):
        low2_events.extend([(cursor, 1), (cursor + block_points + 25, 2)])
        cursor += block_points + 5000
    retained, detected = resting_fixation_blocks(
        low2_events, cursor, hz=hz, window_points=window_points, windows_per_block=windows_per_block, max_blocks=max_blocks
    )
    assert len(detected) == 5
    assert len(retained) == max_blocks
    assert all(b['retained_end_sample'] - b['start_sample'] == block_points for b in retained)
