"""Event pulse interpretation, native offsets and leakage detection."""
import numpy as np
import pytest
from tools.prepare_small_moabb import pulse_onsets,slice_window,overlapping_intervals,case_row,select_channels,mamem_trials


def test_pulse_onsets_do_not_repeat_samples_and_keep_changed_codes():
    assert pulse_onsets([0,1,1,0,2,2,3,3,0,1]).tolist()==[1,4,6,9]
    assert pulse_onsets([2,2,0]).tolist()==[0]


def test_native_window_is_half_open_and_preserves_channel_order():
    x=np.arange(60,dtype=np.float64).reshape(20,3)
    result,start,end=slice_window(x,4,3,5)
    np.testing.assert_array_equal(result,x[7:12].T)
    assert (start,end)==(7,12) and result.dtype==np.float64
    with pytest.raises(ValueError,match='Incomplete'):slice_window(x,19,0,5)


def test_cross_split_interval_overlap_respects_recording_identity():
    train={'same':[(0,5),(10,15)],'other':[(0,20)]}
    assert overlapping_intervals(train,{'same':[(5,10),(15,20)]})==0
    assert overlapping_intervals(train,{'same':[(4,11)]})==2
    assert overlapping_intervals(train,{'different':[(0,20)]})==0


def test_participant_ids_remain_strings_and_original_partition_is_retained():
    row=case_row('speller',1,'0','train','s1.mat',5,2,'train')
    assert row['participant_id']=='01' and row['session_id']=='0'
    assert row['original_partition']=='train' and row['label_description']=='Target'


def test_global_channel_selection_retains_original_axis_mapping():
    x=np.arange(15,dtype=np.float64).reshape(3,5)
    result,names,keep=select_channels(x,['Fp1','Fp2','Cz'],[1])
    assert names==['Fp1','Cz'] and keep==[0,2]
    np.testing.assert_array_equal(result,x[[0,2]])
    with pytest.raises(ValueError):select_channels(x,['Fp1','Fp2','Cz'],[3])


def test_mamem_trials_use_exact_markers_and_one_based_positions():
    eeg=np.zeros((15,1000));eeg[-1,10]=33028;eeg[-1,138]=32779;eeg[-1,778]=32780
    events=np.array([[1,33028,11,1],[2,32779,139,2],[3,32780,779,3]])
    assert list(mamem_trials(eeg,events))==[(33028,138,778,0,1,2)]
    events[2,2]=778
    with pytest.raises(ValueError):list(mamem_trials(eeg,events))
