"""Source boundary, label/order and recording-identity safeguards."""
import numpy as np
import pandas as pd
import pytest
from tools import prepare_mi_next as m


def frame():
    t=np.tile(np.arange(-749,1251)/250,40)
    out=pd.DataFrame({'TimeStamp':t})
    for i,n in enumerate(m.LEE_CHANNELS):out[n]=t+i
    out['trial']=np.repeat(np.arange(1,41),2000)
    out['class']=np.repeat([-1,1]*20,2000)
    return out


def test_csv_finds_true_zero_instead_of_nominal_three_second_offset():
    x,meta=m.csv_epochs(frame())
    assert x.shape==(40,16,1250) and x.dtype==np.float64
    assert x[0,0,0]==0 and x[0,0,-1]==4.996
    assert meta[0]['cue_local']==749 and meta[0]['csv_start_row']==749
    assert meta[1]['trial_id']=='2' and meta[1]['source_label']=='1'


def test_csv_rejects_trial_label_change_and_reordered_sensors():
    data=frame();data.loc[100,'class']=1
    with pytest.raises(ValueError,match='class'):m.csv_epochs(data)
    data=frame();columns=list(data.columns);columns[1],columns[2]=columns[2],columns[1]
    with pytest.raises(ValueError,match='order'):m.csv_epochs(data[columns])


def test_csv_rejects_missing_samples_instead_of_constructing_timeline():
    with pytest.raises(ValueError,match='time axis'):m.csv_epochs(frame().drop(index=10))


def polo(condition):
    codes=[110,210,211,310,311,210,211,911] if condition=='STATIC' else [120,220,221,320,321,220,221,921]
    task=np.repeat(codes,[1000,500,3750,500,7000,500,3750,1000])
    raw=np.broadcast_to(np.arange(len(task),dtype=float),(35,len(task))).copy()
    device=dict(electrodes_names_selected=m.POLO_CHANNELS+['VU','VD','HR','HL','AX','AY','AZ'],fm=250)
    return dict(data_EEG=raw,task_EEG=task,conf=dict(acquisition=dict(EEG_index=np.arange(1,29),device=dict(devices_EEG=device))))


@pytest.mark.parametrize('condition',['STATIC','MOTION'])
def test_polo_selects_two_rest_phases_and_mi_without_audio_or_settling(condition):
    x,phases,names,_=m.polo_epochs(polo(condition),condition)
    assert x.shape==(3,28,1000) and names[:28]==m.POLO_CHANNELS
    assert [x[i,0,0] for i in range(3)]==[1500,5750,13250]
    assert [e-s for _,s,e in phases]==[3750,7000,3750]


def test_batista_keeps_cue_ordinals_and_excludes_lost_sample_trials():
    events=[dict(type='Stimulus',code='S7',position_1based=1),dict(type='New Segment',code='LostSamples:2',position_1based=100),dict(type='Stimulus',code='S10',position_1based=2501),
            dict(type='Stimulus',code='S8',position_1based=3001),dict(type='Stimulus',code='S10',position_1based=5498)]
    good,bad=m.batista_trials(events,6000)
    assert good[0]['trial_index']==1 and good[0]['native_duration']==2497
    assert bad[0]['trial_index']==0 and bad[0]['segment_markers'][0]['position_1based']==100


def test_identity_hash_ignores_auxiliary_changes_but_detects_eeg_changes():
    a=np.arange(76*38,dtype='<f4').reshape(76,38);b=a.copy();b[:,32:]=0
    res=np.ones(32)
    assert m.eeg_record_hash(a,res)==m.eeg_record_hash(b,res)
    assert m.eeg_record_hash(a,res)==m.eeg_record_hash(a*2,res/2)
    b[0,0]+=1
    assert m.eeg_record_hash(a,res)!=m.eeg_record_hash(b,res)


def test_batista_preserves_pilot_identity_and_balances_cohorts():
    people=[f'{n:02d}' for n in list(range(1,10))+list(range(12,20))]+['p01','p02','p03']
    train=m.subject_split(people,[]);test=set(people)-train
    assert len(train)==15 and len(test)==5
    assert {'p01','p02'}<=train and 'p03' in test and not train&test


def test_polo_pilot_preserves_full_cohort_split_membership():
    assert m.polo_split(['B01','B06'],[])=={'B01'}
    assert m.polo_split([f'B{i:02d}' for i in range(1,7)],[])=={'B01','B02','B03','B04'}


@pytest.mark.parametrize('auxiliary',m.BATISTA_AUX_SCHEMAS)
@pytest.mark.parametrize('coordinates',[True,False])
def test_batista_auxiliary_variation_keeps_exact_native_eeg_order(auxiliary,coordinates):
    from tools.test_prepare_vagaja import native_header
    data=native_header(names=m.EEG+auxiliary)
    if not coordinates:data=data.split(b'[Coordinates]')[0]
    channels,positions,_,_=m.batista_header(data)
    assert len(positions)==(38 if coordinates else 0)
    assert [c['name'] for c in channels[:32]]==m.EEG
    assert [c['name'] for c in channels[32:]]==auxiliary
    with pytest.raises(ValueError,match='order'):
        m.batista_header(native_header(names=list(reversed(m.EEG))+auxiliary))


def test_batista_prepare_derives_crop_before_loading_finished_metadata(monkeypatch,tmp_path):
    events=[dict(type='Stimulus',code='S7',position_1based=1),dict(type='Stimulus',code='S10',position_1based=2496)]
    monkeypatch.setattr(m,'batista_paths',lambda *args:[('01','20220224',tmp_path/'native.vhdr',events)])
    seen=[]
    def prepared(key,*args):
        seen.append(m.core.SPECS[key])
        return {'sentinel':True}
    monkeypatch.setattr(m.core,'prepare',prepared)
    monkeypatch.setattr(m,'finish_sidecars',lambda result,key:result)
    assert m.prepare('batista',cache_root=tmp_path,output=tmp_path/'out')=={'sentinel':True}
    assert seen[0]['points']==2495 and m.SPECS['batista']['points']==2500
