"""Independent marker/partition/release safety checks for SymbolAttention."""
import pytest
from tools.prepare_chailloux import markers,flash_labels,numeric_split
from tools.download_openneuro_release import annex_identity,safe_relative


def test_native_position_is_retained_and_block_target_resets():
    text="Mk1=trigger,201,10,0,0\nMk2=trigger,102,20,0,0\nMk3=trigger,2,30,0,0\nMk4=trigger,1,40,0,0\nMk5=trigger,200,50,0,0"
    rows=flash_labels(markers(text),4)
    assert [r['label'] for r in rows]==['2','1']
    assert rows[0]['position_1based']==30 and rows[0]['marker_number']==3
    assert rows[0]['target_symbol']==2
    with pytest.raises(ValueError,match='without valid'):flash_labels(markers(text+'\nMk6=trigger,2,60,0,0'),4)


def test_target_grid_and_coincident_events_rejected():
    with pytest.raises(ValueError,match='outside'):flash_labels(markers('Mk1=trigger,201,10,0,0\nMk2=trigger,109,20,0,0'),4)
    with pytest.raises(ValueError,match='coincident'):markers('Mk1=trigger,201,10,0,0\nMk2=trigger,102,10,0,0')


def test_numeric_subject_split_keeps_original_string_tokens():
    subjects=['0'+str(i) for i in range(1,20)]
    train=numeric_split(sorted(subjects),[])
    assert len(train)==14 and '09' in train and '014' in train and '015' not in train


def test_release_annex_identity_and_safe_paths():
    assert annex_identity('../../../.git/annex/MD5E-s872--802ffa7a93ea98a97a3048f733b9f514')==('md5',872,'802ffa7a93ea98a97a3048f733b9f514')
    with pytest.raises(ValueError):annex_identity('MD5E-s10--abc.eeg')
    for path in ['../outside','C:/outside','/outside','a\\b']:
        with pytest.raises(ValueError):safe_relative(path)


def test_missing_target_is_explicitly_unlabelled_and_never_stale():
    events=markers("Mk1=trigger,201,10,0,0\nMk2=trigger,102,20,0,0\nMk3=trigger,2,30,0,0\nMk4=trigger,201,40,0,0\nMk5=trigger,2,50,0,0")
    rows=flash_labels(events,4,allow_missing_target=True)
    assert [r['label'] for r in rows]==['2',None]
    assert rows[1]['target_symbol'] is None


def test_label_depends_on_native_target_not_grid_filename():
    events=markers("Mk1=trigger,201,10,0,0\nMk2=trigger,107,20,0,0\nMk3=trigger,7,30,0,0\nMk4=trigger,6,40,0,0")
    assert [r['label'] for r in flash_labels(events,6,strict_grid=False)]==['2','1']
