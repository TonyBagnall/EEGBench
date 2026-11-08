"""Unit-independent flatline detection versus aeon's absolute std threshold."""
import json

import numpy as np

from tools.audit_signal_scale import audit_dataset,masks,metrics


def test_tiny_varying_signal_is_not_an_exact_constant():
    channels=['1,1,1,1','0,0,0,0','0,1e-13,2e-13,3e-13','0,1e-5,2e-5,3e-5']
    values=metrics(channels)[:,None,:]
    flags=masks(values)
    assert flags['exact_constant'].tolist()==[[True,True,False,False]]
    assert flags['zero_constant'].tolist()==[[False,True,False,False]]
    assert flags['aeon_tiny_nonconstant'].tolist()==[[False,False,True,False]]
    assert flags['numpy_allclose_to_first'].tolist()==[[True,True,True,False]]


def test_unit_conversion_changes_threshold_flag_but_preserves_variation():
    volts=metrics(['0,1e-8,2e-8,3e-8'])[:,None,:]
    microvolts=metrics(['0,0.01,0.02,0.03'])[:,None,:]
    assert masks(volts)['aeon_tiny_nonconstant'][0,0]
    assert not masks(microvolts)['aeon_tiny_nonconstant'][0,0]
    assert not masks(volts)['exact_constant'][0,0]
    assert not masks(microvolts)['exact_constant'][0,0]


def test_missing_samples_are_reported_separately():
    values=metrics(['1,?,1'])[:,None,:]
    flags=masks(values)
    assert flags['nonfinite'][0,0] and not flags['exact_constant'][0,0]
    assert values[7,0,0]==1


def test_streaming_audit_preserves_source_bytes_and_row_indices(tmp_path):
    source=tmp_path/'data'/'Example';source.mkdir(parents=True)
    header='@problemName Example\n@timestamps false\n@univariate false\n@classLabel true a b\n@data\n'
    snapshots={}
    for split in ['TRAIN','TEST']:
        path=source/f'Example_{split}.ts'
        path.write_text(header+'1,1,1:0,1e-13,2e-13:a\n0,0,0:1,2,3:b\n')
        snapshots[path]=(path.read_bytes(),path.stat().st_mtime_ns)
    report=audit_dataset('Example',tmp_path/'data',tmp_path/'audit')
    for path,(data,mtime) in snapshots.items():
        assert path.read_bytes()==data and path.stat().st_mtime_ns==mtime
    assert report['partitions']['TRAIN']['counts']['exact_constant']==2
    assert report['partitions']['TEST']['counts']['aeon_tiny_nonconstant']==1
    assert (tmp_path/'audit'/'Example'/'constants.csv').read_text().splitlines()[1].startswith('Example,TRAIN,0,0,a,')
    assert json.loads((tmp_path/'audit'/'Example'/'summary.json').read_text())['dataset']=='Example'
