"""Source timing, sensor identity and participant membership safeguards."""
from pathlib import Path

import numpy as np
import pytest

from tools.prepare_open_moabb import SHARED, crop, harmonise_castillos, main_brain_files, pulse_onsets, native_json, training_people, gdf_files,store_intermediate


def test_native_crop_is_half_open_and_preserves_every_channel():
    source=np.arange(120,dtype=np.float32).reshape(4,30)
    result=crop(source,7,10)
    np.testing.assert_array_equal(result,source[:,7:17])
    assert result.dtype==np.float64
    with pytest.raises(ValueError,match='Incomplete'):crop(source,25,10)


def test_pulse_events_do_not_repeat_held_markers():
    assert pulse_onsets([0,1,1,0,2,0,1]).tolist()==[1,4,6]


def test_two_layouts_harmonise_by_sensor_identity_without_positional_assumptions():
    for extra in ['F9 P9 P10 F10','FT9 TP9 TP10 FT10']:
        native=list(reversed(SHARED))+extra.split()
        indices=harmonise_castillos(native)
        assert [native[i] for i in indices]==SHARED
    with pytest.raises(ValueError):harmonise_castillos(SHARED+['bad']*4)


def test_brainform_requires_both_main_conditions_and_excludes_extra(tmp_path):
    for person,session in [('P01','0grain'),('P01','1cb'),('P01','2cbExtra'),('P15','1cb')]:
        p=tmp_path/f'sub-{person}'/f'ses-{session}'/'eeg'/f'sub-{person}_ses-{session}_task-ERP_eeg.edf'
        p.parent.mkdir(parents=True,exist_ok=True);p.touch()
    complete,excluded=main_brain_files(tmp_path)
    assert list(complete)==['P01'] and excluded==['P15']
    assert len(complete['P01'])==2


def test_native_header_scalars_and_unknown_coordinates_are_valid_json():
    import json
    result=native_json({'samples':np.int64(12),'position':np.array([1,np.nan,3])})
    assert result=={'samples':12,'position':[1,None,3]}
    json.dumps(result,allow_nan=False)


def test_kumar_subject_split_preserves_both_feedback_groups_in_each_partition():
    people=[f'{i:02d}' for i in range(1,20) if i!=10]
    train=training_people('kumar',people,14)
    assert len(train)==14 and set(people)-train=={'08','09','18','19'}


def test_gdf_discovery_counts_each_file_once_on_case_insensitive_filesystems(tmp_path):
    for name in ['first.gdf','second.GDF','ignore.txt']:(tmp_path/name).touch()
    files=gdf_files(tmp_path)
    assert len(files)==len(set(files))==2
    assert {p.name for p in files}=={'first.gdf','second.GDF'}

def test_intermediate_reuse_requires_identical_source_bits(tmp_path,monkeypatch):
    p=tmp_path/'cases.npz';x=np.array([[[0.,1.,2.]]]);store_intermediate(p,x)
    original=np.savez_compressed;writes=[]
    def record(*args,**kwargs):writes.append(True);return original(*args,**kwargs)
    monkeypatch.setattr(np,'savez_compressed',record)
    store_intermediate(p,x.copy());assert writes==[]
    changed=x.copy();changed[0,0,0]=-0.
    store_intermediate(p,changed);assert len(writes)==1
    with np.load(p,allow_pickle=False) as a:assert np.signbit(a['X'][0,0,0])
    p.write_bytes(b'incomplete old archive')
    store_intermediate(p,x);assert len(writes)==2
    p.write_bytes(b'')
    store_intermediate(p,x);assert len(writes)==3
    with np.load(p,allow_pickle=False) as saved:assert np.array_equal(saved['X'],x)


def test_interrupted_cache_write_keeps_previous_complete_archive(tmp_path,monkeypatch):
    p=tmp_path/'cases.npz';x=np.arange(6,dtype=float).reshape(1,2,3);store_intermediate(p,x)
    def interrupted(handle,**kwargs):
        handle.write(b'partial archive');raise OSError('simulated interruption')
    monkeypatch.setattr(np,'savez_compressed',interrupted)
    with pytest.raises(OSError,match='interruption'):store_intermediate(p,x+1)
    with np.load(p,allow_pickle=False) as saved:assert np.array_equal(saved['X'],x)
    assert list(tmp_path.iterdir())==[p]


def test_duplicate_source_cases_fail_before_export_even_with_conflicting_labels():
    from tools.prepare_open_moabb import preflight_case_hashes
    import numpy as np
    import pytest
    seen={};case=np.arange(8,dtype=float).reshape(1,2,4)
    preflight_case_hashes(case,[dict(source_file='a',event_index=0,label='1')],seen)
    preflight_case_hashes(case+1,[dict(source_file='b',event_index=0,label='1')],seen)
    with pytest.raises(ValueError,match='Duplicate source case before export'):
        preflight_case_hashes(case,[dict(source_file='c',event_index=0,label='2')],seen)


def test_cached_zip_member_is_repaired_if_same_size_but_wrong_bytes(tmp_path):
    import zipfile
    from tools.prepare_open_moabb import extract_selected
    archive=tmp_path/'source.zip';root=tmp_path/'extracted';root.mkdir()
    with zipfile.ZipFile(archive,'w') as z:z.writestr('signal.bin',b'original')
    (root/'signal.bin').write_bytes(b'changed!')
    extract_selected(archive,root,lambda name:True)
    assert (root/'signal.bin').read_bytes()==b'original'
