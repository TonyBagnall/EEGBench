"""Native-axis mapping and lossless export checks for FlickerSymbols."""
import itertools
import numpy as np
import pytest
from tools.prepare_wang import TRAIN, format_case, iter_cases, parse_channels


def test_native_axes_keep_target_then_block_order():
    values=np.arange(240,dtype=np.float64).reshape(1,1,40,6)
    source=np.broadcast_to(values,(64,1500,40,6))
    cases=list(itertools.islice(iter_cases(source),7))
    assert [(t,b) for t,b,_ in cases]==[(0,b) for b in range(6)]+[(1,0)]
    for t,b,x in cases:
        assert x.shape==(64,1500)
        assert np.all(x==t*6+b)


def test_decimal_export_retains_binary64_precision():
    x=np.array([[1.2345678901234567,1e-200,-0.0],[np.pi,1e100,123456789.12345679]])
    actual=np.stack([np.fromstring(ch,sep=',') for ch in format_case(x).split(':')])
    assert actual.tobytes()==x.tobytes()


def test_subject_split_preserves_experience_groups_without_leakage():
    test=set(range(1,36))-set(TRAIN)
    assert len(TRAIN)==26 and len(set(TRAIN))==26 and len(test)==9
    assert len(set(TRAIN)&set(range(1,9)))==6
    assert len(test&set(range(1,9)))==2


def test_channel_mapping_uses_original_order_and_labels(tmp_path):
    p=tmp_path/'64-channels.loc'
    p.write_text('\n'.join(f'{i} {i-32} 0.5 '+('CB1' if i==60 else f'source{i}') for i in range(1,65))+'\n\n')
    sensors=parse_channels(p)
    assert sensors[59]['name']=='CB1' and sensors[59]['array_index']==59
    assert sensors[0]['source_electrode_index']==1
    p.write_text('1 0 0.5 unknown\n')
    with pytest.raises(ValueError,match='count/order'):parse_channels(p)
