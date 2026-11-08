"""Source naming, timing, missing data and export integrity for Ofner2017."""
import csv
import hashlib
import io

import numpy as np
import pytest

from tools.prepare_ofner import CHANNELS, POINTS, channel_names, epochs, fetch_original, header, source_event_metadata, validate
from tools.prepare_moabb import signal_hash


def raw_fixture():
    import mne
    names=CHANNELS+['eog-l','eog-m','eog-r']+[f'aux-{i}' for i in range(32)]
    info=mne.create_info(names,512,['eeg']*61+['eog']*3+['misc']*32)
    rng=np.random.default_rng(5)
    data=np.zeros((96,42*1600+2000));data[:61]=rng.normal(size=data[:61].shape)
    data[64:]=np.nan
    raw=mne.io.RawArray(data,info,verbose='ERROR')
    raw.set_annotations(mne.Annotations(np.arange(42)*1600/512+1,np.zeros(42),[str(1536+i%7) for i in range(42)]))
    return raw


def test_original_generic_aliases_only_at_documented_source():
    native=[f'eeg-{i}' for i in range(61)]
    assert channel_names(native,1,'execution')==(CHANNELS,True)
    with pytest.raises(ValueError,match='order'):channel_names(native,1,'imagination')
    swapped=CHANNELS.copy();swapped[0],swapped[1]=swapped[1],swapped[0]
    with pytest.raises(ValueError,match='order'):channel_names(swapped,2,'execution')


def test_cue_crop_auxiliary_nan_and_nonfinite_eof_are_preserved():
    raw=raw_fixture();raw._data[:61,-10:]=np.nan
    cases,audit=epochs(raw,2,'imagination')
    assert len(cases)==42 and cases[0][2:4]==(512,1536)
    np.testing.assert_array_equal(cases[0][-1],raw._data[:61,512:512+POINTS].astype('<f4'))
    assert audit['nonfinite_eeg_values']==610
    assert np.isnan(raw._data[64:]).all()  # No auxiliary zero filling.
    assert audit['all_retained_epochs_finite']


def test_nonfinite_selected_epoch_fails():
    raw=raw_fixture();raw._data[0,600]=np.nan
    with pytest.raises(ValueError,match='Nonfinite'):epochs(raw,2,'execution')


def test_missing_class_event_fails():
    raw=raw_fixture();raw.annotations.delete(0)
    with pytest.raises(ValueError,match='six events'):epochs(raw,2,'execution')


def test_original_gdf_event_identity_and_sample_base():
    extra=dict(event_sfreq=512,events=[3,np.array([10,512,600]),np.array([768,1537,33536]),np.zeros(3),np.ones(3)])
    assert source_event_metadata(extra,512,1537)==dict(source_gdf_event_index=1,source_event_sample_1based=513,source_event_duration_samples=1)
    with pytest.raises(ValueError,match='identity'):source_event_metadata(extra,513,1537)


def test_numeric_export_alignment_and_label_corruption(tmp_path):
    case=np.arange(61*POINTS,dtype='<f4').reshape(61,POINTS)/37
    path=tmp_path/'ArmMovements_TRAIN.ts'
    fmt=','.join(['%.9g']*POINTS)
    path.write_text(header('ArmMovements')+':'.join(fmt%tuple(ch.tolist()) for ch in case)+':0\n')
    row=dict(split='TRAIN',row=0,participant_id='01',run_id='01',trial_index=0,label=0,source_label=1536,start_sample=512,event_sample=512,source_event_sample_1based=513,end_sample=512+POINTS,signal_sha256=signal_hash(case))
    table=tmp_path/'cases_train.tsv'
    def write():
        with table.open('w',newline='') as file:
            writer=csv.DictWriter(file,row,delimiter='\t');writer.writeheader();writer.writerow(row)
    write();report,_=validate(tmp_path,'ArmMovements','TRAIN')
    assert report['shape']==[1,61,1536] and report['subjects']==['01']
    row['source_label']=1537;write()
    with pytest.raises(ValueError,match='Label'):validate(tmp_path,'ArmMovements','TRAIN')


@pytest.mark.parametrize('supports_range',[True,False])
def test_resume_original_bytes_and_verify_both_checksums(tmp_path,monkeypatch,supports_range):
    data=b'verified original recording bytes';path=tmp_path/'run.gdf'
    path.with_name('run.gdf.part').write_bytes(data[:10])
    class Response(io.BytesIO):
        status=206 if supports_range else 200
        headers={'Content-Range':f'bytes 10-{len(data)-1}/{len(data)}'} if supports_range else {}
    def open_response(request,timeout):
        assert request.get_header('Range')==f'bytes=10-{len(data)-1}'
        return Response(data[10:] if supports_range else data)
    monkeypatch.setattr('tools.prepare_ofner.urllib.request.urlopen',open_response)
    fetch_original('https://example.invalid/run',path,'md5:'+hashlib.md5(data).hexdigest(),len(data),hashlib.sha256(data).hexdigest())
    assert path.read_bytes()==data and not path.with_name('run.gdf.part').exists()


def test_cli_refuses_existing_destination_before_network(tmp_path,monkeypatch):
    from tools import prepare_ofner
    (tmp_path/'ArmMovements').mkdir()
    monkeypatch.setattr('sys.argv',['prepare_ofner','--output',str(tmp_path)])
    def forbidden(*args,**kwargs):raise AssertionError('Existing output must be checked before downloading')
    monkeypatch.setattr(prepare_ofner,'download_sources',forbidden)
    with pytest.raises(FileExistsError,match='another --output'):prepare_ofner.main()
