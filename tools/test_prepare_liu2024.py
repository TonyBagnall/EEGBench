"""Native Liu2024 stage/label alignment and explicit sensor selection."""
import numpy as np
import pytest

from tools.prepare_liu2024 import eeg_indices,imagery_events


def fixture_events():
    signal=np.zeros(160000,dtype=np.float64);schedule=[]
    for trial in range(40):
        for i,(offset,duration) in enumerate([(0,2000),(1000+trial%3,4000),(3000+trial%4,2000)]):
            signal[trial*4000+offset]=(i+1)*1e-6
            schedule.append(dict(value=str(i+1),trial_type=str(trial%2+1),
                onset=str(trial*8000+[1,2001,6001][i]),duration=str(duration)))
    return signal,schedule


def test_observed_marker_samples_override_ideal_millisecond_schedule():
    signal,schedule=fixture_events();events=imagery_events(signal,schedule)
    assert len(events)==40
    assert events[0][:4]==(0,1,1000,3000)
    assert events[1][:4]==(1,4,5001,7001)
    assert [e[-1]['trial_type'] for e in events[:4]]==['1','2','1','2']


def test_missing_stage_and_wrong_trigger_scale_are_rejected():
    signal,schedule=fixture_events();signal[1000]=0
    with pytest.raises(ValueError,match='triplets'):imagery_events(signal,schedule)
    signal,schedule=fixture_events()
    with pytest.raises(ValueError):imagery_events(signal*1e6,schedule)


def test_source_label_conflict_is_not_silently_encoded():
    signal,schedule=fixture_events();schedule[1]['trial_type']='2'
    with pytest.raises(ValueError,match='trial labels'):imagery_events(signal,schedule)


def test_extra_nontrial_markers_do_not_shift_hand_labels():
    signal,schedule=fixture_events()
    signal[1500]=1e-6  # Spurious instruction inside the first imagery period.
    signal[-20]=1e-6;signal[-19:]=2e-6  # Unfinished held tail, not trial 41.
    events,audit=imagery_events(signal,schedule,return_audit=True)
    assert len(events)==40 and events[-1][-1]['trial_type']=='2'
    assert len(audit['ignored_stage_pulses'])==3


def test_genuinely_ambiguous_imagery_pulses_fail_before_labels_are_assigned():
    signal,schedule=fixture_events();signal[1500]=2e-6
    with pytest.raises(ValueError,match='Ambiguous'):imagery_events(signal,schedule)


def test_fractional_interpolated_trigger_values_do_not_create_events():
    signal,schedule=fixture_events();signal[-10:]=np.linspace(0.2,2.8,10)*1e-6
    events,audit=imagery_events(signal,schedule,return_audit=True)
    assert len(events)==40 and audit['noninteger_trigger_samples_ignored']==10


def test_reference_and_eog_are_excluded_without_reordering_eeg():
    names=[f'EEG{i:02d}' for i in range(29)]
    table=[dict(name=n,type='EEG') for n in names]
    native=names[:17]+['CPz']+names[17:]+['HEOL','HEOR','']
    keep,retained=eeg_indices(native,table)
    assert [native[i] for i in keep]==retained==names and 17 not in keep
    native[0],native[1]=native[1],native[0]
    with pytest.raises(ValueError,match='channel order'):eeg_indices(native,table)
