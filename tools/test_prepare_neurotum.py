"""Native XDF sensor, timestamp and session-transfer safeguards."""
import numpy as np
import pytest
from tools import prepare_neurotum as n


def test_subject_specific_three_class_protocol_and_last_session_split():
    assert n.session_partition(dict(participant_id='P1',session_id='S4'))=='TRAIN'
    assert n.session_partition(dict(participant_id='P1',session_id='S5'))=='TEST'
    assert n.session_partition(dict(participant_id='P2',session_id='S3'))=='TEST'
    assert n.PEOPLE['P1']['actions']=={'REST':'1','RIGHT HAND MI':'2','LEGS MI':'3'}
    assert 'LEFT HAND MI' in n.PEOPLE['P2']['actions']


def test_nearest_real_sample_not_uniform_synthetic_timeline():
    times=10+np.arange(1000)/250
    assert n.nearest_sample(times,10.0061)==2
    with pytest.raises(ValueError,match='aligned'):n.nearest_sample(times,9.9)
    with pytest.raises(ValueError,match='increasing'):n.nearest_sample([1,2,2],2)


def test_window_preserves_float32_values_in_float64_and_rejects_dropouts():
    data=np.arange(1000*24,dtype=np.float32).reshape(1000,24);times=np.arange(1000)/250
    x=n.task_window(data,times,20)
    assert x.dtype==np.float64 and np.array_equal(x,data[20:770].T)
    with pytest.raises(ValueError,match='Incomplete'):n.task_window(data,times,300)
    times[500:]+=.1
    with pytest.raises(ValueError,match='dropout'):n.task_window(data,times,20)


def test_sensor_names_are_native_not_standardised_and_positions_qualified():
    names=['FP1']+[f'native{i}' for i in range(1,24)]
    info=dict(type=['EEG'],channel_count=['24'],nominal_srate=['250'],desc=[{'channels':[dict(type=['EEG'],channel=[dict(label=[name],location=[dict(X=['1'],Y=['2'],Z=['3'])]) for name in names])]}])
    actual,positions,_=n.native_sensors(info)
    assert actual==names and actual[0]=='FP1' and positions[0]==dict(X=1.,Y=2.,Z=3.)
    info['desc'][0]['channels'][0]['channel'][1]['label']=['FP1']
    with pytest.raises(ValueError,match='duplicate'):n.native_sensors(info)


def test_coincident_non_task_markers_keep_native_order_but_clock_regression_fails():
    assert n.validate_timestamps(np.arange(10)/250,[1,2,2,3])==[1]
    with pytest.raises(ValueError,match='ordering'):n.validate_timestamps([1,2,2],[1,2,3])
    with pytest.raises(ValueError,match='ordering'):n.validate_timestamps([1,2,3],[1,3,2])
