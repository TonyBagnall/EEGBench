"""Native calibration/order, discontinuity and fixed split safeguards."""
import pytest
from tools import prepare_vagaja as v


def native_header(names=None,unit='uV'):
    names=names or v.EEG+v.AUX
    return ('[Common Infos]\nSamplingInterval=2000\nNumberOfChannels=38\nDataFormat=BINARY\nDataOrientation=MULTIPLEXED\n'
            '[Binary Infos]\nBinaryFormat=IEEE_FLOAT_32\n[Channel Infos]\n'+
            '\n'.join(f'Ch{i+1}={n},,0.0406901,{unit}' for i,n in enumerate(names))+
            '\n[Coordinates]\n'+'\n'.join(f'Ch{i+1}=1,0,0' for i in range(38))).encode()


def test_sensor_order_and_explicit_units_are_required():
    channels,coordinates,_,_=v.header(native_header())
    assert channels[0]['name']=='Fp1' and channels[0]['resolution']==0.0406901
    assert len(coordinates)==38
    with pytest.raises(ValueError,match='order'):v.header(native_header(list(reversed(v.EEG))+v.AUX))
    with pytest.raises(ValueError,match='units'):v.header(native_header(unit='unknown'))


def markers():
    events=[]
    for i in range(40):
        start=i*6000+1
        events += [dict(type='Stimulus',code='S7' if i%2==0 else 'S8',position_1based=start),
                   dict(type='Stimulus',code='S10',position_1based=start+4997+i%5)]
    return events


def test_common_window_never_crosses_native_end_and_keeps_source_ordinals():
    retained,excluded=v.windows(markers(),240000)
    assert len(retained)==40 and not excluded
    assert retained[0]['start']==0 and retained[0]['end']==4997
    assert [r['trial_index'] for r in retained]==list(range(40))
    events=markers();events[1]['position_1based']-=1
    with pytest.raises(ValueError,match='duration'):v.windows(events,240000)


def test_lost_samples_exclude_whole_trial_without_interpolating():
    events=markers()+[dict(type='New Segment',code='LostSamples:3',position_1based=100)]
    retained,excluded=v.windows(events,240000)
    assert len(retained)==39 and [e['trial_index'] for e in excluded]==[0]
    assert retained[0]['trial_index']==1 and excluded[0]['segment_markers'][0]['position_1based']==100


def test_fixed_split_holds_out_three_people_per_priming_group():
    train=v.split_people(v.PEOPLE,[]);test=set(v.PEOPLE)-train
    assert len(train)==20 and len(test)==6
    assert len(test&set(v.EMBODIED))==len(test&set(v.CONTROL))==3
    assert not train&test and v.split_people(['03','30'],[])=={'03'}
