"""Verify diagnostic labels, participant grouping and native source windows."""
import numpy as np
import pytest
from tools.prepare_eegdash_diagnosis import diagnostic_subject_split,stimulus_windows
from tools.download_eegdash_diagnosis import blob_sha
from tools.prepare_eegdash_psychosis import group_split,harmonise_rate,nonzero_segments,vectorized_brainvision
from tools.prepare_eegdash_iowa import continuous_segments
from tools.prepare_eegdash_ucsd import clinical_split


def test_diagnosis_split_keeps_severity_with_ad_and_never_infers_unknown_mmse():
    participants=[]
    for group,ids in [('Normal',['01','03','08','09']),('MCI',['17','18','19','27']),('Mild AD',['02','04','05'])]:
        participants.extend(dict(participant_id='sub-'+p,Group=group,MMSE='30') for p in ids)
    participants.extend([dict(participant_id='sub-24',Group='Moderate AD',MMSE='23'),dict(participant_id='sub-06',Group='-',MMSE='10')])
    train,excluded=diagnostic_subject_split(participants)
    assert train=={'01','03','08','17','18','19','02','04','05'}
    assert excluded[0]['participant_id']=='06' and '06' not in train


def test_stimulus_windows_preserve_bids_sample_grid_and_native_discrepancy():
    events=[dict(onset='5',duration='40',sample='1251',value='2',trial_type='Stimulus'),dict(onset='45',duration='20',sample='11251',value='1',trial_type='Rest')]
    native=[dict(index=0,latency_1based=1250,code=2),dict(index=1,latency_1based=11250,code=1)]
    windows,audit=stimulus_windows(events,native,250,20000)
    assert len(windows)==10 and windows[0]['start_sample']==1250 and windows[-1]['end_sample']==11250
    assert all(w['end_sample']-w['start_sample']==1000 for w in windows)
    assert audit[0]['native_minus_bids_samples']==-1
    with pytest.raises(ValueError,match='Incomplete'):stimulus_windows(events,native,250,11000)
    native[0]['latency_1based']=1248
    with pytest.raises(ValueError,match='one sample'):stimulus_windows(events,native,250,20000)


def test_git_blob_identity_has_type_and_length_prefix():
    import hashlib
    assert blob_sha(b'abc')==hashlib.sha1(b'blob 3\0abc').hexdigest()


def test_vectorized_source_order_and_native_resolutions(tmp_path):
    x=np.array([[1,2,3],[10,20,30]],dtype='<f4');(tmp_path/'native.eeg').write_bytes(x.tobytes())
    p=tmp_path/'native.vhdr';p.write_text('Brain Vision Data Exchange Header File Version 1.0\n[Common Infos]\nDataFile=native.eeg\nDataFormat=BINARY\nDataOrientation=VECTORIZED\nNumberOfChannels=2\nDataPoints=3\nSamplingInterval=1000\n[Binary Infos]\nBinaryFormat=IEEE_FLOAT_32\n[Channel Infos]\nCh1=EEG001,, \nCh2=EEG002,,0.1,uV\n',encoding='utf-8')
    actual,info=vectorized_brainvision(p)
    assert np.array_equal(actual,x) and info['native_resolutions_uV']==[1,.1]
    assert info['native_channel_names']==['EEG001','EEG002']
    assert np.array_equal(actual.astype('<f8')*np.asarray(info['native_resolutions_uV'])[:,None],np.array([[1,2,3],[1,2,3]]))


def test_psychosis_split_preserves_alphanumeric_ids_and_rejects_unknown_labels():
    people=[dict(participant_id='sub-'+p,type=group) for group,prefix in [('Control','2'),('Psychosis','3')] for p in [prefix+'01A',prefix+'02A',prefix+'03A',prefix+'04A']]
    train=group_split(people)
    assert train=={'201A','202A','203A','301A','302A','303A'}
    people[0]['type']='unknown'
    with pytest.raises(ValueError,match='Unreviewed'):group_split(people)


def test_new_segment_at_first_sample_is_not_a_missing_sample():
    events=[dict(type='boundary',code='New Segment',latency=1),dict(type='boundary',latency=4500.5)]
    assert continuous_segments(events,10000)==[(0,4500),(4500,10000)]
    windows=[(start,start+2000) for a,b in continuous_segments(events,10000) for start in range(a,b-2000+1,2000)]
    assert windows==[(0,2000),(2000,4000),(4500,6500),(6500,8500)]


def test_rate_harmonisation_preserves_identity_and_rejects_aliasing():
    hz=1e6/333.3333  # Exact calculation in the distributed native header.
    t=np.arange(60000)/hz
    low=np.sin(2*np.pi*20*t)
    high=np.sin(2*np.pi*800*t)
    out=harmonise_rate(np.stack([low,high]),hz)
    assert out.shape==(2,20000)
    # Ignore edge padding transient: preserve EEG-band amplitude and suppress
    # above-new-Nyquist energy rather than allowing an aliased200Hz signal.
    assert np.std(out[0,1000:-1000])==pytest.approx(2**-.5,rel=.01)
    assert np.std(out[1,1000:-1000])<.002
    native=np.stack([low[:4000],high[:4000]])
    assert np.array_equal(harmonise_rate(native,1000),native)
    with pytest.raises(ValueError,match='Unreviewed'):harmonise_rate(native,2000)


def test_ucsd_split_uses_original_strings_within_clinical_groups():
    people=[{'participant_id':'sub-'+g+p} for g in ['hc','pd'] for p in ['01','02','03','04']]
    assert clinical_split(people)=={'hc01','hc02','hc03','pd01','pd02','pd03'}
    with pytest.raises(ValueError,match='Unreviewed'):clinical_split([{'participant_id':'sub-control1'}])


def test_nonzero_segments_exclude_all_channel_zero_dropouts_without_partial_window_leakage():
    n_channels=4;lead=2000;zero_len=5000;tail=9000;window_len=4000
    total=lead+zero_len+tail
    rng=np.random.default_rng(7)
    x=rng.standard_normal((n_channels,total))
    x[:,lead:lead+zero_len]=0.0
    x[:,lead+zero_len+500]=0.0  # Single-sample zero crossing must not split segment.
    segments,zero_runs=nonzero_segments(x,1000)
    assert zero_runs==[(lead,lead+zero_len)]
    assert segments==[(0,lead),(lead+zero_len,total)]
    windows=[(s,s+window_len) for a,b in segments for s in range(a,b-window_len+1,window_len)]
    assert windows==[(lead+zero_len,lead+zero_len+window_len),(lead+zero_len+window_len,lead+zero_len+2*window_len)]
    with pytest.raises(ValueError,match='anti-alias'):
        nonzero_segments(x,1e6/333.3333)

