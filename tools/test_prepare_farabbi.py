"""Native phase, indexed sensors and GDF trial/cue correspondence."""
from pathlib import Path
import numpy as np
import pytest
from tools import prepare_farabbi as f
from tools.prepare_open_moabb import case_partition


def test_native_phase_and_feedback_folder_are_separate_from_run_order():
    root=Path('source');p=root/'01/03_session_3/2_condition_1/1st-person-online-[2020.01.23-13.13.09].gdf'
    ids=f.identity(p,root)
    assert ids['person']=='01' and ids['session']=='03_session_3' and ids['view']=='1st' and ids['phase']=='online'
    with pytest.raises(ValueError):f.identity(p.with_name(p.name.replace('1st','3rd')),root)
    assert case_partition({'case_splitter':f.archive_partition},{'original_partition':'training'},set())=='TRAIN'
    assert case_partition({'case_splitter':f.archive_partition},{'original_partition':'online'},set())=='TEST'
    with pytest.raises(ValueError):case_partition({'case_splitter':f.archive_partition},{'original_partition':'unknown'},set())


def test_cues_preserve_native_event_and_trial_indices():
    extra={'events':[5,np.array([0,0,500,2000,2500]),np.array([768,786,769,768,770]),np.zeros(5),np.ones(5)]}
    cues=f.native_cues(extra)
    assert [(c['event_index'],c['position'],c['trial_index']) for c in cues]==[(2,500,0),(4,2500,3)]
    extra['events'][1][-1]=600
    with pytest.raises(ValueError,match='Multiple class cues'):f.native_cues(extra)


def test_original_indexed_locations_not_guessed_names(tmp_path):
    p=tmp_path/'chanlocs.locs';names=[f'EEG{i}' for i in range(32)]+['ACC_X','ACC_Y','ACC_Z']
    p.write_text('\n'.join(f'{i} 0 0.5 {n}' for i,n in enumerate(names,1)),encoding='utf-8')
    loc=f.locations(p);assert loc[0]['native_channel_index']==0 and loc[31]['name']=='EEG31' and loc[-1]['name']=='ACC_Z'
    p.write_text(p.read_text(encoding='utf-8').replace('1 0 0.5 EEG0','2 0 0.5 EEG0'),encoding='utf-8')
    with pytest.raises(ValueError):f.locations(p)
