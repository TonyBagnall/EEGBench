"""Renaming preserves the complete data block and retains source aliases."""

import pytest

from .test_prepare import source
from .prepare import convert, read_json
from .export_local import export_dataset
from .rename_local import rename_dataset


@pytest.mark.parametrize('labels', [[0, 1, 2, 3, 5, 6, 7, 8], ['left_hand', 'right_hand']])
def test_sparse_emotion_labels_and_payload_survive_rename(tmp_path, labels):
    from aeon.datasets import load_from_ts_file
    from .export_local import ts_header
    from .rename_local import replace_header
    payload = ''.join(f'1,2:{label}\n' for label in labels).encode()
    path = tmp_path / 'FACED_TRAIN.ts'
    path.write_bytes(ts_header('FACED', 1, 2, len(labels), class_values=labels).encode() + payload)
    old_size = path.stat().st_size
    replace_header(path, 'FACED', 'VideoEmotions', 1, 2, len(labels), class_values=labels)
    assert path.stat().st_size == old_size
    assert path.read_bytes().split(b'@data\n', 1)[1] == payload
    X, y = load_from_ts_file(path)
    assert X.shape == (len(labels), 1, 2)
    assert y.tolist() == list(map(str, labels))


def test_legacy_sidecar_rename_preserves_source_metadata(source, tmp_path, monkeypatch):
    from .export_local import EXPORTS
    from .prepare import dump
    monkeypatch.setitem(EXPORTS, 'arithmetic_zyma2019', ('Legacy', 'Imagined movement'))
    convert(source, tmp_path / 'archive', smoke=False)
    export_dataset(tmp_path / 'archive', tmp_path, 'arithmetic_zyma2019', smoke=False)
    root = tmp_path / 'Legacy'
    path = root / 'Legacy_metadata.json'
    m = read_json(path)
    for key in ['provenance', 'source_dataset_name', 'case_metadata', 'classes']:
        m.pop(key)
    m['validation'] = {s:dict(shape=m['shapes'][s.lower()], exact_float32_roundtrip=True,
                              aeon_full_roundtrip_passed=True) for s in ['TRAIN', 'TEST']}
    dump(path, m)
    for filename in ['Legacy_manifest.json', 'Legacy_validation.json', 'README_Legacy.md']:
        (root / filename).unlink()
    payload = (root / 'Legacy_TRAIN.ts').read_bytes().split(b'@data\n', 1)[1]
    rename_dataset(tmp_path, 'Legacy', 'TaskName')
    renamed = tmp_path / 'TaskName'
    assert (renamed / 'TaskName_TRAIN.ts').read_bytes().split(b'@data\n', 1)[1] == payload
    updated = read_json(renamed / 'TaskName_metadata.json')
    assert updated['source_dataset_name'] == 'Legacy'
    assert updated['source_doi'] == m['source_doi']
    assert updated['case_metadata']['file'] == 'TaskName_rows.tsv'


def test_task_name_rename_preserves_signal_bytes_and_aliases(source, tmp_path, monkeypatch):
    from .export_local import EXPORTS
    monkeypatch.setitem(EXPORTS, "arithmetic_zyma2019", ("Arithmetic", "Mental arithmetic versus rest"))
    convert(source, tmp_path / "archive", smoke=False)
    export_dataset(tmp_path / "archive", tmp_path, "arithmetic_zyma2019", smoke=False)
    previous = {}
    offsets = {}
    for split in ("TRAIN", "TEST"):
        data = (tmp_path / f"Arithmetic/Arithmetic_{split}.ts").read_bytes()
        header, previous[split] = data.split(b"@data\n", 1)
        offsets[split] = len(header)
    rename_dataset(tmp_path, "Arithmetic", "MentalArithmetic")
    folder = tmp_path / "MentalArithmetic"
    assert not (tmp_path / "Arithmetic").exists()
    for split in ("TRAIN", "TEST"):
        header, payload = (folder / f"MentalArithmetic_{split}.ts").read_bytes().split(b"@data\n", 1)
        assert payload == previous[split]
        assert len(header) == offsets[split]
        assert b"@problemName MentalArithmetic\n" in header
    metadata = read_json(folder / "MentalArithmetic_metadata.json")
    assert metadata["name"] == "MentalArithmetic"
    assert "Arithmetic" in metadata["aliases"]
    assert metadata["case_metadata"]["file"] == "MentalArithmetic_rows.tsv"
    assert (folder / "previous-name-manifest.json").exists()
    assert read_json(folder / "MentalArithmetic_manifest.json")["status"] == "validated"
