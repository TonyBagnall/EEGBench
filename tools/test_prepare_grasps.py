"""Original answer schema, class order and MI-window safeguards."""
import numpy as np
import pytest
from tools import prepare_grasps as g


def test_imagery_window_uses_native_zero_time_not_epoch_start():
    e=dict(clab=g.CHANNELS,fs=250,t=np.arange(-6000,4001,4),x=np.broadcast_to(np.arange(2501)[:,None,None],(2501,60,150)))
    x=g.imagery(e)
    assert x.shape==(150,60,1000) and x.dtype==np.float64
    assert np.all(x[:,:,0]==1500) and np.all(x[:,:,-1]==2499)
    e['clab']=list(reversed(g.CHANNELS))
    with pytest.raises(ValueError):g.imagery(e)


def test_native_onehot_class_order_and_invalid_vector():
    e=dict(className=g.CLASSES,y=np.tile(np.eye(3,dtype=int),50))
    assert g.onehot_labels(e).tolist()==[0,1,2]*50
    e['y'][1,0]=1
    with pytest.raises(ValueError):g.onehot_labels(e)


def sheet_rows():
    headers={};columns={};rows=[]
    for n in range(1,16):
        trial=g.excel_column(2*n);label=g.excel_column(2*n+1)
        headers[trial]=f'Data_sample{n:02}';columns[trial]='Trial #';columns[label]='True Label'
    for i in range(1,151):
        row={}
        for n in range(1,16):row[g.excel_column(2*n)]=str(i);row[g.excel_column(2*n+1)]=str((i-1)%3)
        rows.append(row)
    return [headers,columns]+rows


def test_original_true_label_sheet_preserves_ids_and_trial_order(monkeypatch):
    rows=sheet_rows();monkeypatch.setattr(g,'xlsx_rows',lambda *a:rows)
    result=g.answers('unused');assert result['01']['labels'][:3]==[0,1,2] and result['15']['label_column']=='AE'
    rows[2]['B']='2'
    with pytest.raises(ValueError):g.answers('unused')


def test_prediction_template_is_rejected(monkeypatch):
    rows=sheet_rows();rows[1]['C']='Predicted Class';monkeypatch.setattr(g,'xlsx_rows',lambda *a:rows)
    with pytest.raises(ValueError,match='true-label'):g.answers('unused')


def test_official_days_merge_validation_only():
    assert [g.archive_partition({'original_partition':p}) for p in ['training','validation','test']]==['TRAIN','TRAIN','TEST']


def test_pilot_and_cohort_use_distinct_recording_caches(monkeypatch):
    """Native file ordinals change when adding subjects to the pilot."""
    seen=[]
    def prepared(key,*args):
        seen.append(dict(g.core.SPECS[key]))
        return {'sentinel':True}
    monkeypatch.setattr(g.core,'prepare',prepared)
    monkeypatch.setattr(g,'finish_sidecars',lambda r:r)
    g.prepare(pilot=True)
    g.prepare(pilot=False)
    assert seen[0]['intermediate_directory']!=seen[1]['intermediate_directory']
    assert seen[0]['subjects']==['01'] and 'subjects' not in seen[1]
