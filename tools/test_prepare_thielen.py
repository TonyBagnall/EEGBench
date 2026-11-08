"""Original c-VEP trial identity, MATLAB metadata and export ordering."""
import csv

import h5py
import numpy as np
import pytest

from tools.prepare_moabb import signal_hash
from tools.prepare_thielen import NAME,NATIVE,POINTS,header,inspect_recording,matlab_value,trial_groups,validate


def markers():
    samples=[];starts=[]
    for trial in range(20):
        starts.append(2048+trial*34*512)
        count=15 if trial%2 else 16
        samples.extend(np.rint(starts[-1]+np.arange(count)*2.1*512).astype(int))
    return np.array([[s,0,257] for s in samples]),starts


def test_trial_grouping_preserves_all_targets_with_optional_sixteenth_marker():
    events,starts=markers();labels=np.arange(20,0,-1)
    groups=trial_groups(events,labels)
    assert [g['sample'] for g in groups]==starts
    assert [g['label'] for g in groups]==labels.tolist()
    assert [len(g['samples']) for g in groups]==[16,15]*10
    assert groups[2]['event_index']==31  # Fixed [::16] indexing would be wrong.


def test_missing_cycle_and_zero_based_target_labels_rejected():
    events,_=markers()
    with pytest.raises(ValueError,match='1..20'):trial_groups(events,np.arange(20))
    with pytest.raises(ValueError,match='cycle markers'):trial_groups(np.delete(events,range(13,16),axis=0),np.arange(1,21))


def test_cycle_jitter_is_retained_without_moving_original_onset():
    events,starts=markers();events[4,0]+=10
    groups=trial_groups(events,np.arange(1,21))
    assert groups[0]['sample']==starts[0] and groups[0]['samples'][4]==events[4,0]
    assert groups[0]['max_deviation_samples']>=9


def test_accumulated_display_delay_is_flagged_without_retiming():
    events,starts=markers()
    events[20:31,0]+=86  # Delayed cycles in the 15-marker second trial.
    groups=trial_groups(events,np.arange(1,21))
    assert groups[1]['sample']==starts[1]
    assert groups[1]['timing_warning'] and groups[1]['max_deviation_samples']>85
    assert groups[1]['samples'][-1]==events[30,0]


def test_matlab_struct_chars_cells_vectors_and_internal_id(tmp_path):
    path=tmp_path/'cfg.mat'
    with h5py.File(path,'w') as file:
        group=file.create_group('v');main=group.create_group('main')
        d=main.create_dataset('subject',data=np.array([ord(c) for c in 'sub-23'],dtype='u2')[:,None]);d.attrs['MATLAB_class']=np.bytes_('char')
        main.create_dataset('subjectid',data=[[1.]])
        main.create_dataset('trainlabels',data=np.arange(1,21)[:,None])
        refs=file.create_group('#refs#');d=refs.create_dataset('label',data=np.array([70,112,49],dtype='u2')[:,None]);d.attrs['MATLAB_class']=np.bytes_('char')
        cell=group.create_dataset('label',shape=(1,1),dtype=h5py.ref_dtype);cell[0,0]=d.ref
    value=matlab_value(path)
    assert value['main']['subject']=='sub-23' and value['main']['subjectid']==1
    assert value['main']['trainlabels']==list(range(1,21))
    assert value['label']=='Fp1'


def test_exact_case_readback_and_label_vector_alignment(tmp_path):
    case=np.arange(8*POINTS,dtype='<f4').reshape(8,POINTS)*np.float32(1e-8)
    fmt=','.join(['%.9g']*POINTS)
    (tmp_path/f'{NAME}_TRAIN.ts').write_text(header()+':'.join(fmt%tuple(ch.tolist()) for ch in case)+':5\n')
    row=dict(split='TRAIN',row=0,participant_id='01',run_id='01',trial_index=0,source_label=5,label=5,cycle_marker_samples='[2048]',cycle_marker_count=1,start_sample=2048,end_sample=2048+POINTS,signal_sha256=signal_hash(case))
    path=tmp_path/'cases_train.tsv'
    def write():
        with path.open('w',newline='') as file:
            writer=csv.DictWriter(file,row,delimiter='\t');writer.writeheader();writer.writerow(row)
    write();report,_=validate(tmp_path,'TRAIN')
    assert report['shape']==[1,8,POINTS] and report['subjects']==['01']
    row['source_label']=6;write()
    with pytest.raises(ValueError,match='Label'):validate(tmp_path,'TRAIN')


@pytest.mark.parametrize('condition',['valid','wrong_order','nonfinite'])
def test_source_channel_selection_and_quality(monkeypatch,tmp_path,condition):
    import mne
    events,starts=markers();n=starts[-1]+POINTS+100
    data=np.tile(np.arange(9)[:,None]*1e-6,(1,n));data[0]=0
    data[0,events[:,0]]=257
    native=NATIVE.copy()
    if condition=='wrong_order':native[0],native[1]=native[1],native[0]
    if condition=='nonfinite':data[1,starts[0]+10]=np.nan
    raw=mne.io.RawArray(data,mne.create_info(['STATUS',*native],512,['stim']+['eeg']*8),verbose='ERROR')
    raw._raw_extras=[dict(units=np.r_[1,np.full(8,1e-6)])];raw._orig_units={}
    labels=list(range(1,21))
    cfg=dict(main=dict(subject='sub-23',subjectid=1,trainlabels=labels,trialtime=31.5),stimulation=dict(rate=60,layout=labels))
    values={'cfg.mat':cfg,'hdr.mat':{'Fs':180},'trainlabels.mat':labels}
    monkeypatch.setattr('tools.prepare_thielen.matlab_value',lambda path:values[path.name])
    monkeypatch.setattr(mne.io,'read_raw_gdf',lambda *args,**kwargs:raw)
    if condition=='wrong_order':
        with pytest.raises(ValueError,match='order'):inspect_recording(tmp_path,'dummy.gdf',23)
    elif condition=='nonfinite':
        with pytest.raises(ValueError,match='Nonfinite'):inspect_recording(tmp_path,'dummy.gdf',23)
    else:
        groups,native,_,_=inspect_recording(tmp_path,'dummy.gdf',23)
        assert groups[0]['case'].shape==(8,POINTS)
        np.testing.assert_array_equal(groups[0]['case'][0],np.full(POINTS,1e-6,dtype='<f4'))
        np.testing.assert_array_equal(groups[0]['case'][-1],np.full(POINTS,8e-6,dtype='<f4'))
        assert native['types']==['stim']+['eeg']*8
