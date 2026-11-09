"""Regression checks for source-specific MI epoch and partition semantics."""
import h5py
import numpy as np
import pytest
from scipy.io import savemat
from tools.prepare_mi_to_30 import pan_epoch_arrays,pan25_partition
from tools.mi_to_30_native import nearest_sample,cho_epochs,daly_recording_selection,DALY_AMBIGUOUS_PATHS,DALY_AMBIGUOUS_SHA256
from tools.audit_pan_identity import fingerprint
from tools.download_original_ranges import fetch_ranges,verify
import hashlib
import io
import json


def test_pan_native_axes_and_one_based_task_indices(tmp_path):
    data=np.arange(28*1375*2,dtype=np.float64).reshape(28,1375,2)
    path=tmp_path/'native.mat';savemat(path,dict(data=data,label=[2,1],Info=dict(fs=250,period=[-1.5,4],chaninfo=np.array([f'Native{i}' for i in range(28)],dtype=object),taskpoints=np.arange(376,1376))))
    x,y,names,cue,info=pan_epoch_arrays(path,'pan25')
    assert cue==375 and np.array_equal(x[1],data[:,375:1375,1])
    assert y.tolist()==[2,1] and names[0]=='Native0'


def test_pan23_unknown_names_and_cue_crop(tmp_path):
    path=tmp_path/'native.mat';data=np.arange(2*1750*28,dtype='<f4').reshape(2,1750,28)
    with h5py.File(path,'w') as f:
        f['data']=data;f['fs']=[[250]];f['label']=[[1,2]]
    x,y,names,cue,info=pan_epoch_arrays(path,'pan23')
    assert np.array_equal(x[0],data[0,750:1750].T.astype('<f8'))
    assert info['native_channel_names'] is None and names[0]=='source_column_01'
    assert x.dtype==np.dtype('<f8')


def test_original_online_partition_boundary():
    assert pan25_partition(dict(session_id='1',source_epoch_index=150))=='TRAIN'
    assert pan25_partition(dict(session_id='2',source_epoch_index=29))=='TRAIN'
    assert pan25_partition(dict(session_id='2',source_epoch_index=30))=='TEST'


def test_raw_xdf_nearest_does_not_assume_sorted_timestamps():
    times=np.array([0,.002,.004,.003,.005,.007])
    assert nearest_sample(times,.0031)==3
    with pytest.raises(ValueError,match='clock'):nearest_sample(times,1)


def test_cho_actual_event_onset_and_interleaved_sequence():
    event=np.zeros(358400,dtype=np.uint8);onsets=1023+np.arange(100)*3584;event[onsets]=1
    left=np.broadcast_to(np.arange(len(event)),(68,len(event)))
    d=dict(srate=512,n_imagery_trials=100,imagery_event=event,imagery_left=left,imagery_right=left+1)
    seq=dict(imagery_left=np.arange(100)*2+2,imagery_right=np.arange(100)*2+1)
    epochs=cho_epochs(d,seq)
    assert epochs[0][1]=='2' and epochs[1][1]=='1'
    assert epochs[0][4]==1023 and epochs[0][-1].shape==(64,1536)
    assert epochs[0][-1][0,0]==1024 # Actual marker is index1023, not assumed1024.
    seq['imagery_right'][0]=2
    with pytest.raises(ValueError,match='Ambiguous'):cho_epochs(d,seq)


def test_identity_hash_preserves_native_precision():
    a=np.array([1,1+2**-40],dtype='<f8');b=a.astype('<f4').astype('<f8')
    assert fingerprint(a)!=fingerprint(b)


def test_original_ranges_resume_and_verify_before_publish(tmp_path,monkeypatch):
    data=b'original native bytes; no float transformation';path=tmp_path/'source.mat'
    path.with_name(path.name+'.part').write_bytes(data[:7]);requested=[]
    class Response(io.BytesIO):
        status=206
        def __init__(self,start,end):
            super().__init__(data[start:end+1]);self.headers={'Content-Range':f'bytes {start}-{end}/{len(data)}'}
    def open_request(request,timeout):
        start,end=map(int,request.get_header('Range').removeprefix('bytes=').split('-'));requested.append((start,end));return Response(start,end)
    monkeypatch.setattr('urllib.request.urlopen',open_request)
    fetch_ranges('https://publisher.invalid/source',path,'sha256:'+hashlib.sha256(data).hexdigest(),len(data),workers=2,chunk_bytes=9)
    assert path.read_bytes()==data and min(s for s,e in requested)==7
    assert not path.with_name(path.name+'.part').exists()


def test_publisher_multipart_etag_is_not_plain_md5(tmp_path):
    first=b'x'*5242880;last=b'final-part';data=first+last;path=tmp_path/'original';path.write_bytes(data)
    etag=hashlib.md5(hashlib.md5(first).digest()+hashlib.md5(last).digest()).hexdigest()+'-2'
    assert verify(path,len(data),'s3-multipart-md5-5242880:'+etag)
    assert not verify(path,len(data),'s3-multipart-md5-5242880:'+hashlib.md5(data).hexdigest()+'-2')


def test_daly_excludes_both_ambiguous_owners_but_keeps_unique_runs():
    copies=[dict(name=p,sha256=DALY_AMBIGUOUS_SHA256,bytes=15015120) for p in sorted(DALY_AMBIGUOUS_PATHS)]
    other=dict(name='sub-17/eeg/sub-17_task-run10_eeg.edf',sha256='unique',bytes=11899120)
    selected,excluded=daly_recording_selection(dict(pilot=False,files=copies+[other]))
    assert selected==[other] and {r['participant_id'] for r in excluded}=={'09','15'}
    copies[0]['sha256']='unexpected release content'
    with pytest.raises(ValueError,match='content changed'):daly_recording_selection(dict(pilot=False,files=copies+[other]))


def test_daly_does_not_suppress_new_unreviewed_duplicates():
    a=dict(name='sub-01/eeg/sub-01_task-run2_eeg.edf',sha256='new-copy',bytes=1)
    b=dict(a,name='sub-02/eeg/sub-02_task-run2_eeg.edf')
    with pytest.raises(ValueError,match='Unreviewed'):daly_recording_selection(dict(pilot=True,files=[a,b]))


@pytest.mark.parametrize('valid',[True,False])
def test_cleanup_only_owned_npz_after_final_verification(tmp_path,monkeypatch,valid):
    from tools import run_mi_to_30 as runner
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    folder=tmp_path/'output';folder.mkdir();name='ImaginedHandsPhysiology'
    (folder/(name+'_metadata.json')).write_text('{}')
    docs=tmp_path/'docs';docs.mkdir();(docs/'cho-to-30-source-lock.json').write_text(json.dumps(dict(source_revision='pinned-original')))
    cache=tmp_path/'sources/Cho2017';intermediate=cache/'classification-intermediate-full';intermediate.mkdir(parents=True)
    owned=intermediate/'recording-0000.npz';owned.write_bytes(b'rebuildable')
    original=cache/'original.mat';original.write_bytes(b'keep original')
    unrelated=intermediate/'notes.txt';unrelated.write_text('keep')
    result=dict(dataset=name,path=str(folder));captured=[]
    def verify(r):
        if not valid:raise ValueError('Final source mismatch')
        return r
    monkeypatch.setattr(runner,'verify_final',verify)
    def finish(r,m,*args,**kwargs):captured.append(m);return r
    monkeypatch.setattr(runner,'finish',finish)
    if valid:
        runner.refresh_final(result,'cho',tmp_path/'sources',True)
        assert not owned.exists() and captured[0]['intermediate_cache_status'].startswith('Cleared after validation')
    else:
        with pytest.raises(ValueError,match='mismatch'):runner.refresh_final(result,'cho',tmp_path/'sources',True)
        assert owned.exists() and not captured
    assert original.read_bytes()==b'keep original' and unrelated.read_text()=='keep'
