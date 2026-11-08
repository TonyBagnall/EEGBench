"""Original filename encoding, numeric ordering and exact CSV sensor columns."""
import numpy as np
import pytest
from tools import prepare_milimb as m


def test_native_filename_task_and_rest_suffix_order():
    a={'name':'S2/S2R1I8_2_10.csv'};b={'name':'S10/S10R1I2_1.csv'}
    assert m.file_order(a)==(2,1,8,(2,10))
    assert sorted([b,a],key=m.file_order)==[a,b]
    assert m.LABELS['1']!='rest' and 'rest_between' in m.LABELS['8']


def test_native_csv_preserves_microvolt_values_excludes_sample_index(tmp_path):
    x=np.column_stack([np.arange(500),np.arange(500*16,dtype=np.float64).reshape(500,16)/7])
    p=tmp_path/'epoch.csv';np.savetxt(p,x,delimiter=',',header=','+','.join(str(i) for i in range(16)),comments='',fmt='%.17g')
    actual=m.native_csv(p)
    assert actual.shape==(16,500) and np.array_equal(actual,x[:,1:].T)
    p.write_text(p.read_text(encoding='utf-8').replace(',0,1,2','NaN,0,1,2',1),encoding='utf-8')
    assert np.array_equal(m.native_csv(p),actual)
    x[20,0]=21;np.savetxt(p,x,delimiter=',',header=','+','.join(str(i) for i in range(16)),comments='',fmt='%.17g')
    with pytest.raises(ValueError,match='index'):m.native_csv(p)


def test_milimb_subject_split_numeric_not_lexicographic():
    people=sorted('S'+str(i) for i in range(1,61))
    assert m.specification()['splitter'](people,[])=={'S'+str(i) for i in range(1,46)}


def test_ambiguous_cross_person_copies_are_all_excluded_without_guessing_owner():
    excluded=m.source_exclusions()
    assert len(excluded)==62
    assert {e['participant_id'] for e in excluded.values()}=={'S1','S2'}
    assert {e['source_label'] for e in excluded.values()}=={'8'}
    assert 'S1/S1R1I8_1_1.csv' in excluded and 'S2/S2R1I8_1_1.csv' in excluded
