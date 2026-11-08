"""Precision, channel mapping and backed-up publication of local transformations."""
import csv
import json
from pathlib import Path

import numpy as np
import pytest

from tools import transform_local_signals as t


def test_scale_uses_float64_and_exact_decimal_roundtrip():
    segments=['1.123456789012345e-13,2.345678901234567e-13,3.456789012345678e-13','-1.5e-11,-1.5e-11,-1.5e-11','4e-13,5e-13,6e-13']
    old,new,text=t.transform_values(segments,1,1e15)
    actual=np.stack([np.fromstring(s,sep=',') for s in text.split(':')])
    assert new.dtype==np.float64
    np.testing.assert_array_equal(new,old[[0,2]]*np.float64(1e15))
    np.testing.assert_array_equal(actual,new)
    assert new[0,0]!=float(np.float32(new[0,0]))


def test_removal_only_keeps_numeric_tokens_verbatim():
    segments=['1.00000000,2e-5,3.40','0,0,0','-1.23,-2.34,-3.45']
    _,new,text=t.transform_values(segments,1,1.)
    assert text==segments[0]+':'+segments[2]
    np.testing.assert_array_equal(new,np.stack([np.fromstring(s,sep=',') for s in [segments[0],segments[2]]]))


def fixture(tmp_path,monkeypatch,bad_drop=False):
    root=tmp_path/'data';folder=root/'MatchWords';folder.mkdir(parents=True)
    spec=dict(channels=3,points=3,drop=1,gain=1e15,before_unit='T',after_unit='fT',counts={'TRAIN':2,'TEST':2},reason='Fixture flat source axis')
    monkeypatch.setitem(t.SPECS,'MatchWords',spec)
    monkeypatch.setattr(t,'smoke',lambda *args:dict(passed=True,fixture=True))
    header='@problemName MatchWords\n@timestamps false\n@dimension 3\n@equalLength true\n@seriesLength 3\n@classLabel true No Yes\n@data\n'
    for split,offset in [('TRAIN',0),('TEST',10)]:
        lines=[]
        for i,label in enumerate(['No','Yes']):
            a=(np.arange(3)+1+offset+i)*1e-13;b=np.full(3,-1.5e-11);c=(np.arange(3)+8+offset+i)*1e-13
            if bad_drop:b[1]=0
            lines.append(':'.join(','.join(format(float(v),'.17g') for v in ch) for ch in [a,b,c])+':'+label+'\n')
        (folder/f'MatchWords_{split}.ts').write_text(header+''.join(lines))
        with (folder/f'MatchWords_{split}_rows.tsv').open('w',newline='') as file:
            writer=csv.DictWriter(file,['case_index_0based','class_label','participant_id'],delimiter='\t');writer.writeheader();writer.writerows(dict(case_index_0based=i,class_label=label,participant_id='001') for i,label in enumerate(['No','Yes']))
    with (folder/'MatchWords_channels.tsv').open('w',newline='') as file:
        writer=csv.DictWriter(file,['array_index_0based','name','units'],delimiter='\t');writer.writeheader();writer.writerows(dict(array_index_0based=i,name=f'MEG {i+1:03d}',units='T') for i in range(3))
    (folder/'MatchWords_metadata.json').write_text(json.dumps(dict(local_data=dict(dimensions_per_case={'channels':3,'timepoints':3},channel_mapping={'local_array_order_verified':False}),source_channels={'file':'MatchWords_channels.tsv','units':'T','count':3})))
    return root,folder


def test_complete_transform_preserves_backup_labels_ids_and_axes(tmp_path,monkeypatch):
    root,folder=fixture(tmp_path,monkeypatch)
    before=(folder/'MatchWords_TRAIN.ts').read_bytes()
    result=t.transform_dataset(root,tmp_path/'backups','MatchWords','fixture-revision')
    assert Path(result['backup'],'MatchWords_TRAIN.ts').read_bytes()==before
    metadata=json.loads((folder/'MatchWords_metadata.json').read_text())
    assert metadata['units']=='fT' and metadata['channel_names']==['MEG 001','MEG 003']
    assert metadata['shapes']=={'train':[2,2,3],'test':[2,2,3]}
    assert metadata['change_history'][0]['kept_source_array_indices']==[0,2]
    with (folder/'MatchWords_TRAIN_rows.tsv').open() as file:rows=list(csv.DictReader(file,delimiter='\t'))
    assert [r['participant_id'] for r in rows]==['001','001']
    assert [r['class_label'] for r in rows]==['No','Yes']
    assert all(r['signal_hash_dtype']=='<f8' and r['signal_sha256'] for r in rows)
    assert result['validation']['TRAIN']['exact_constant_pairs']==0


def test_invalid_requested_flat_axis_leaves_original_folder_untouched(tmp_path,monkeypatch):
    root,folder=fixture(tmp_path,monkeypatch,bad_drop=True)
    before=(folder/'MatchWords_TRAIN.ts').read_bytes()
    with pytest.raises(ValueError,match='not globally flat'):
        t.transform_dataset(root,tmp_path/'backups','MatchWords','invalid-fixture')
    assert (folder/'MatchWords_TRAIN.ts').read_bytes()==before
    assert not (tmp_path/'backups'/'invalid-fixture'/'MatchWords').exists()
