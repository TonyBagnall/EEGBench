"""Native sensor, calibration and repeated-marker safeguards."""
import numpy as np
import pytest
from tools.prepare_kueper import EEG,AUX,read_header,read_markers,physical_eeg,context


def test_repeated_marker_keys_keep_unique_source_ordinals():
    text="Mk1=New Segment,,1,1,0,20211220100000000000\nMk2=Stimulus,S 99,100,1,0\nMk2=Stimulus,S100,200,1,0\nMk2=Stimulus,S 22,205,1,0"
    events=read_markers(text)
    assert len(events)==4 and [e['marker_key'] for e in events[1:]]==['Mk2']*3
    assert [e['marker_ordinal'] for e in events]==[0,1,2,3]
    assert events[2]['position_1based']==200 and events[2]['code']=='S100'


def test_header_preserves_native_names_and_explicit_microvolt_scale():
    text='DataOrientation=MULTIPLEXED\nBinaryFormat=IEEE_FLOAT_32\nNumberOfChannels=67\nSamplingInterval=2000\nCodepage=UTF-8\n'
    text+='\n'.join(f'Ch{i}={name},,0.0406901,'+('\u00b5V' if i<=64 else 'mg') for i,name in enumerate(EEG+AUX,1))
    channels,encoding,_=read_header(text.encode('cp1252'))
    assert len(channels)==67 and channels[0]['name']=='FP1' and channels[64]['unit']=='mg'
    assert encoding.startswith('cp1252')
    with pytest.raises(ValueError):read_header(text.replace('FP1','unknown').encode('cp1252'))


def test_calibration_casts_to_float64_before_multiplying():
    digital=np.array([[123456.7,123.456],[456789.1,987.654]],dtype=np.float32);resolution=np.array([.0406901,.0406901])
    result=physical_eeg(digital,resolution)
    assert result.dtype==np.float64
    assert np.array_equal(result,digital.astype(np.float64).T*resolution[:,None])
    assert not np.array_equal(result,(digital.T*np.float32(.0406901)).astype(np.float64))


def test_flag_interval_is_half_open_and_keeps_unknown_codes():
    events=[dict(code=c,position_1based=p,marker_ordinal=i) for i,(c,p) in enumerate([('S3',10),('S27',12),('S26',14),('S28',16),('S128',20)])]
    flags=context(events,10,20)
    assert [f['code'] for f in flags]==['S3','S27','S26','S28']
