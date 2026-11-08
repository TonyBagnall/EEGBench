"""Synthetic native records check calibration, state bits and truncation."""
import numpy as np
import pytest
from tools.read_bci2000_native import read,state,calibrated,intervals


def fixture(path):
    h=('BCI2000V= 1.1 HeaderLen= 1024 SourceCh= 2 StatevectorLen= 3 DataFormat= float32\r\n'
       '[ State Vector Definition ]\r\nStimulusCode 12 0 0 5\r\n[ Parameter Definition ]\r\n'
       'Source int SamplingRate= 1000Hz\r\nSource list SourceChGain= 2 0.1 0.2\r\n'
       'Source list SourceChOffset= 2 1 2\r\nSource list ChannelNames= 0\r\n').encode()
    a=np.zeros(5,dtype=[('signal','<f4',(2,)),('states','u1',(3,))]);a['signal']=[[1,2],[11,12],[21,22],[31,32],[41,42]]
    codes=[0,257,257,2,0]
    for i,v in enumerate(codes):a['states'][i]=np.frombuffer((v<<5).to_bytes(3,'little'),dtype='u1')
    path.write_bytes(h.ljust(1024,b' ')+a.tobytes());return codes


def test_reader_multibyte_state_gain_and_offset(tmp_path):
    p=tmp_path/'native.dat';codes=fixture(p);r=read(p)
    assert state(r,'StimulusCode').tolist()==codes
    assert intervals(state(r,'StimulusCode'))==[(1,3,257),(3,4,2)]
    assert np.array_equal(calibrated(r,1,3),np.array([[1.,2.],[2.,4.]]))
    assert r['frequency']==1000 and r['n_channels']==2
    del r


def test_truncated_binary_rejected(tmp_path):
    p=tmp_path/'native.dat';fixture(p);p.write_bytes(p.read_bytes()[:-1])
    with pytest.raises(ValueError,match='Incomplete native binary'):read(p)


def test_calibration_casts_before_multiplying():
    r=dict(data={'signal':np.array([[12345678]],dtype=np.float32)},offsets=np.array([0.]),gains=np.array([0.1]))
    actual=calibrated(r,0,1)[0,0]
    assert actual==float(np.float32(12345678))*0.1
    assert actual!=float(np.float32(12345678)*np.float32(0.1))
