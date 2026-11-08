"""Official temporal split, native target coding and organizer-sheet safeguards."""
import numpy as np
import pytest
from tools import prepare_walking_erp as walking
from tools.prepare_open_moabb import case_partition,partition_people

def test_temporal_partitions_merge_validation_and_preserve_shared_subject():
    rows=[dict(participant_id='01',original_partition=p) for p in ['training','validation','test']]
    spec={'case_splitter':walking.archive_partition}
    assert [case_partition(spec,r,set()) for r in rows]==['TRAIN','TRAIN','TEST']
    assert partition_people(spec,'walking',['01'],[(None,rows)])==({'01'},{'01'})
    assert rows[1]['original_partition']=='validation'
    with pytest.raises(ValueError):case_partition({'case_splitter':lambda r:'VALID'},rows[0],set())

def test_native_onehot_mapping_uses_names_and_agrees_with_event_codes():
    e=dict(className=['non-target','target'],y=np.array([[1,0],[0,1]]),event={'desc':np.array([1,2])})
    assert walking.native_labels(e)[0].tolist()==[1,2]
    e['event']['desc']=np.array([2,1])
    with pytest.raises(ValueError):walking.native_labels(e)

def answer_rows():
    headers={};columns={};rows=[]
    for n in range(1,16):
        trial=walking.excel_column(2*n);label=walking.excel_column(2*n+1)
        headers[trial]=f'Data_sample{n:02d}';columns[trial]='Trial #';columns[label]='True Label'
    for i in range(1,61):
        row={}
        for n in range(1,16):row[walking.excel_column(2*n)]=str(i);row[walking.excel_column(2*n+1)]=str(i%2)
        rows.append(row)
    return [headers,columns]+rows

def test_original_test_sheet_keeps_subject_tokens_and_checks_trial_order(monkeypatch):
    rows=answer_rows();monkeypatch.setattr(walking,'xlsx_rows',lambda *a:rows)
    result=walking.test_answers('unused');assert result['01']['labels'][:3]==[1,0,1] and result['15']['label_column']=='AE'
    rows[3]['B']='5'
    with pytest.raises(ValueError):walking.test_answers('unused')

def test_prediction_probability_template_is_not_a_ground_truth_sheet(monkeypatch):
    rows=answer_rows();rows[1]['C']='Predicted Probability';monkeypatch.setattr(walking,'xlsx_rows',lambda *a:rows)
    with pytest.raises(ValueError,match='schema'):walking.test_answers('unused')

def test_eeg_selection_preserves_native_order_and_excludes_eog_imu():
    assert len(walking.EEG_INDICES)==46
    assert [walking.ALL[i] for i in walking.EEG_INDICES]==walking.SCALP+walking.EAR
    assert not set(walking.EOG+walking.IMU)&set(walking.SCALP+walking.EAR)
