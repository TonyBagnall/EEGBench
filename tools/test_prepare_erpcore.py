"""Verify semantic labels, native binary orientation and one-based EEG events."""

import csv
import hashlib
import json

import numpy as np
import pandas as pd
import pytest
from scipy.io import savemat

import tools.prepare_erpcore as module


def fixture_source(tmp_path,monkeypatch):
    cache=tmp_path/'source';cache.mkdir()
    (cache/'LICENSE').write_text('Original resources: CC BY-SA 4.0')
    (cache/'participants.tsv').write_text('participant_id\tage\tsex\thandedness\nsub-001\t20\tF\tright\nsub-002\t25\tM\tleft\n')
    (cache/'dataset_description.json').write_text(json.dumps({'License':'CC0'}))
    for subject in (1,2):
        stem=f'sub-{subject:03d}_task-N400';directory=cache/f'sub-{subject:03d}'/'eeg';directory.mkdir(parents=True)
        names=module.CHANNELS+['HEOG_left','HEOG_right','VEOG_lower']
        data=np.random.default_rng(subject).normal(size=(10000,33)).astype('<f4');data.tofile(directory/f'{stem}_eeg.fdt')
        native=[];event_rows=[]
        for i,code in enumerate([211,212,221,222]):
            target=1001+i*2000
            for sample,value,kind in [(target-500,code-100,'stimulus'),(target,code,'stimulus'),(target+250,201,'response')]:
                native.append(dict(type=value,latency=sample,urevent=len(native)+1))
                event_rows.append(dict(onset=f'{(sample-1)/1024:.4f}',duration='0.2',sample=str(sample),trial_type=kind,stim_file='n/a',value=str(value)))
        eeg=dict(nbchan=33,pnts=10000,trials=1,srate=1024,data=f'{stem}_eeg.fdt',ref='common',chanlocs=[dict(labels=n) for n in names],event=native,etc=dict(T0=np.array([2014,1,subject,12,0,0])))
        savemat(directory/f'{stem}_eeg.set',dict(EEG=eeg))
        pd.DataFrame(event_rows).to_csv(directory/f'{stem}_events.tsv',sep='\t',index=False)
        pd.DataFrame(dict(name=names,type=['EEG']*30+['EOG']*3,units=['microV']*33)).to_csv(directory/f'{stem}_channels.tsv',sep='\t',index=False)
        pd.DataFrame(dict(name=names,x=['1']*33,y=['2']*33,z=['3']*33)).to_csv(directory/f'{stem}_electrodes.tsv',sep='\t',index=False)
        (directory/f'{stem}_coordsystem.json').write_text(json.dumps(dict(EEGCoordinateUnits='mm',EEGCoordinateSystem='ARS')))
        (directory/f'{stem}_eeg.json').write_text(json.dumps(dict(EEGReference='CMS',SamplingFrequency=1024)))
    rows=[]
    for p in cache.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(cache).as_posix();pid=rel.split('/')[0] if rel.startswith('sub-') else ''
        rows.append(dict(component='N400',local_path='erpcore/N400/'+rel,url='https://example.invalid/'+rel,hash='md5:'+hashlib.md5(p.read_bytes()).hexdigest(),participant_id=pid,file_type='',size=p.stat().st_size))
    path=cache/'erpcore_manifest.csv';pd.DataFrame(rows).to_csv(path,index=False)
    monkeypatch.setattr(module,'MANIFEST_SHA256',hashlib.sha256(path.read_bytes()).hexdigest())
    (cache/'moabb-erpcore-loader.py').write_text('# Test evidence only\n')
    return cache


def test_native_samples_labels_metadata_and_roundtrip(tmp_path,monkeypatch):
    cache=fixture_source(tmp_path,monkeypatch)
    metadata,validation=module.convert(cache,tmp_path/'out',subjects=(1,2),train=(1,),download=False,smoke=False)
    assert metadata['shapes']=={'train':[4,30,1024],'test':[4,30,1024]}
    assert metadata['license']=='CC-BY-SA-4.0'
    assert metadata['excluded_channel_types']=={'EOG':3}
    assert metadata['channel_names']==module.CHANNELS
    folder=tmp_path/'out'/module.NAME
    with (folder/'cases_train.tsv').open(newline='') as file:rows=list(csv.DictReader(file,delimiter='\t'))
    assert rows[0]['participant_id']=='001'
    assert rows[0]['source_sample_1based']=='1001' and rows[0]['event_sample_0based']=='1000'
    assert rows[0]['start_sample']=='795' and rows[0]['end_sample']=='1819'
    assert rows[0]['original_eeglab_event_index']=='2' and rows[0]['original_urevent_id']=='2'
    assert rows[0]['word_list_id']=='1' and rows[1]['word_list_id']=='2'
    assert [row['label'] for row in rows]==['1','1','2','2']
    assert rows[0]['response_codes']=='[201]' and rows[0]['first_response_correct']=='True'
    assert float(rows[0]['first_response_time_seconds'])==250/1024
    raw=np.fromfile(cache/'sub-001/eeg/sub-001_task-N400_eeg.fdt',dtype='<f4').reshape(10000,33)
    actual=np.stack([np.fromstring(ch,dtype='<f4',sep=',') for ch in next(module.lines(folder/f'{module.NAME}_TRAIN.ts')).strip().split(':')[:-1]])
    np.testing.assert_array_equal(actual,raw[795:1819,:30].T)
    assert validation['cross_split_duplicate_signal_hashes']==0


def test_modified_source_rejected(tmp_path,monkeypatch):
    cache=fixture_source(tmp_path,monkeypatch)
    with (cache/'sub-001/eeg/sub-001_task-N400_eeg.fdt').open('ab') as file:file.write(b'changed')
    with pytest.raises(ValueError,match='modified source'):module.sources(cache,(1,2),download=False)


def test_wrong_sample_base_rejected(tmp_path,monkeypatch):
    cache=fixture_source(tmp_path,monkeypatch)
    _,_,events,lookup,*_=module.read_recording(cache,1)
    row=events.index[events.value=='211'][0];events.loc[row,'sample']='1000'
    with pytest.raises(ValueError,match='EEGLAB target'):module.target_rows(events,lookup)


def test_channel_order_conflict_rejected(tmp_path,monkeypatch):
    cache=fixture_source(tmp_path,monkeypatch)
    path=cache/'sub-001/eeg/sub-001_task-N400_channels.tsv';s=path.read_text();path.write_text(s.replace('FP1\t','WRONG\t'))
    with pytest.raises(ValueError,match='channel order'):module.read_recording(cache,1)
