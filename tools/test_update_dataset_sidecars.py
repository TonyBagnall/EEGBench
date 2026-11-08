"""Post-conversion sidecar enrichment must preserve case/label identity."""
import csv
import json
from tools import update_dataset_sidecars as u


def test_native_sensor_mapping_update_preserves_rows_labels_and_hashes(tmp_path,monkeypatch):
    root=tmp_path/'repo';(root/'tools').mkdir(parents=True);(root/'docs').mkdir()
    for name in ['update_dataset_sidecars.py','prepare_open_moabb.py']:(root/'tools'/name).write_text('# snapshot\n',encoding='utf-8')
    (root/'docs/open-moabb-conversion-results.json').write_text('{}',encoding='utf-8');monkeypatch.setattr(u,'ROOT',root)
    folder=tmp_path/'Toy';folder.mkdir();(folder/'Toy_manifest.json').write_text('{"artifacts":{}}',encoding='utf-8')
    original='row\tlabel\tsignal_sha256\tparticipant_id\n0\t1\tabc\t001\n'
    for split in ['train','test']:(folder/f'cases_{split}.tsv').write_text(original,encoding='utf-8')
    metadata=dict(sensors=[dict(name='A',native_channel_index=1),dict(name='B',native_channel_index=3)],metadata_evidence={'direct':'source'},missing_or_inconsistent_metadata=[])
    result=u.finish(dict(dataset='Toy',path=str(folder),source_key='toy'),metadata,[],[],{'label_mapping':{'1':'target'}})
    with (folder/'cases_train.tsv').open(encoding='utf-8',newline='') as src:row=next(csv.DictReader(src,delimiter='\t'))
    assert [row[k] for k in ['row','label','signal_sha256','participant_id']]==['0','1','abc','001']
    assert json.loads(row['exported_native_channel_indices'])==[1,3]
    manifest=json.loads((folder/'Toy_manifest.json').read_text(encoding='utf-8'));assert manifest['artifacts']['cases_train.tsv']['sha256']==u.sha(folder/'cases_train.tsv')
    assert result['size_GB']>0
