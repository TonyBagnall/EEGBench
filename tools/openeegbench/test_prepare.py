"""Synthetic on-disk source tests; no network or large datasets required."""

from copy import deepcopy
import gzip
import hashlib
import json

import h5py
import numpy as np
import pandas as pd
import pytest

from .prepare import (
    Source, ZROOT, case_hash, check_blob, convert, dump, export_ts,
    load_prepared, load_records, partition, read_json, safe_path, validate_arrays,
    verify_licence,
)
from .registry import DATASETS


@pytest.fixture
def source(tmp_path):
    config = deepcopy(DATASETS["arithmetic_zyma2019"])
    config["partitions"] = dict(train=["00"], validation=["01"], test=["02"])
    config["notes"] = []
    result = Source(config, tmp_path / "cache")
    dump(result.cache / ZROOT / "zarr.json", dict(zarr_format=3, attributes=dict(
        n_datasets=3, dataset_type="WindowsDataset", raw_preproc_kwargs="[]",
        window_kwargs=json.dumps([["create_fixed_length_windows", {"mapping": {"rest": 0, "arithmetic": 1}}]]))))
    info = dict(ch_names=["X-original", "ECG-original"], nchan=2, sfreq=200.0,
                chs=[dict(ch_name="X-original", kind=dict(name="FIFFV_EEG_CH", value=2)),
                     dict(ch_name="ECG-original", kind=dict(name="FIFFV_ECG_CH", value=402))])
    for i in range(3):
        relative = f"{ZROOT}/recording_{i}"
        dump(result.cache / relative / "zarr.json", dict(attributes=dict(info=info,
            description=dict(subject=f"{i:02d}", session=None, run=f"{i:02d}",
                             task="arithmetic", path=f"sub-{i:02d}_eeg.edf"))))
        dump(result.cache / relative / "data/zarr.json", dict(shape=[2, 2, 3], data_type="float32",
            chunk_grid=dict(configuration=dict(chunk_shape=[2, 2, 3])),
            chunk_key_encoding=dict(name="default", configuration=dict(separator="/")),
            codecs=[dict(name="bytes", configuration=dict(endian="little")),
                    dict(name="gzip", configuration=dict(level=5))]))
        pd.DataFrame(dict(i_window_in_trial=[0, 1], i_start_in_trial=[0, 3],
                          i_stop_in_trial=[3, 6], target=[0, 1])).to_csv(
            result.cache / relative / "metadata.tsv", sep="\t", index=True)
        X = (np.arange(12, dtype="<f4") + i * 100).reshape(2, 2, 3)
        data = gzip.compress(X.tobytes(), mtime=0)
        name = relative + "/data/c/0/0/0"
        path = result.cache / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        result.files[name] = dict(path=name, size=len(data), lfs=dict(oid=hashlib.sha256(data).hexdigest()))
    # Mock only network transfer, not decoding, indexing or serialization.
    original_fetch = result.fetch
    def fetch(name, target=None):
        if target is None:
            return original_fetch(name)
        data = (result.cache / name).read_bytes()
        check_blob(data, result.files[name])
        target.write_bytes(data)
        return target
    result.fetch = fetch
    evidence = result.cache / "original-source/licence-evidence-0.txt"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("Open Data Commons Attribution License", encoding="utf-8")
    return result


def test_conversion_order_metadata_sensor_identity_and_labels(source, tmp_path):
    m = convert(source, tmp_path / "out", smoke=False)
    X, y, test, yt = load_prepared(tmp_path / "out/arithmetic_zyma2019")
    assert X.shape == (4, 2, 3) and test.shape == (2, 2, 3)
    np.testing.assert_array_equal(X[:, 0, 0], [0, 6, 100, 106])
    np.testing.assert_array_equal(test[:, 0, 0], [200, 206])
    np.testing.assert_array_equal(y, [0, 1, 0, 1])
    assert yt.tolist() == [0, 1]
    table = pd.read_parquet(tmp_path / "out/arithmetic_zyma2019/cases_train.parquet")
    assert table.subject_id.tolist() == ["00", "00", "01", "01"]
    assert table.original_partition.tolist() == ["train", "train", "validation", "validation"]
    assert table.original_trial_id.isna().all() and table.original_start_sample.isna().all()
    assert m["channel_names"] == ["X-original", "ECG-original"]
    assert m["sensors"][1]["kind"]["name"] == "FIFFV_ECG_CH"
    assert read_json(tmp_path / "out/arithmetic_zyma2019/validation.json")["passed"]


def test_ts_roundtrip_and_classifier(source, tmp_path):
    from aeon.datasets import load_from_ts_file
    from .prepare import smoke_classifier
    convert(source, tmp_path / "out", smoke=False)
    folder = tmp_path / "out/arithmetic_zyma2019"
    export_ts(folder, tmp_path / "ts")
    exported_manifest = read_json(tmp_path / "ts/manifest.json")
    assert exported_manifest["format"] == "aeon multivariate .ts"
    assert "arrays.h5" not in exported_manifest["artifacts"]
    assert (tmp_path / "ts/source-manifest.json").exists()
    expected = load_prepared(folder)
    for i, split in enumerate(("TRAIN", "TEST")):
        X, y = load_from_ts_file(tmp_path / f"ts/arithmetic_zyma2019_{split}.ts")
        np.testing.assert_array_equal(X.astype(np.float32), expected[i * 2])
        np.testing.assert_array_equal(y.astype(int), expected[i * 2 + 1])
    assert smoke_classifier(folder)["passed"]


def test_changed_channel_order_is_rejected(source):
    path = source.cache / ZROOT / "recording_1/zarr.json"
    data = read_json(path)
    data["attributes"]["info"]["ch_names"].reverse()
    data["attributes"]["info"]["chs"].reverse()
    dump(path, data)
    with pytest.raises(ValueError, match="Channel order"):
        load_records(source)


def test_sparse_labels_survive_conversion_and_generic_ts_export(source, tmp_path):
    from aeon.datasets import load_from_ts_file
    source.config.update(classes=9, observed_class_values=[0, 8])
    root = source.cache / ZROOT / "zarr.json"
    attrs = read_json(root)
    attrs["attributes"]["window_kwargs"] = json.dumps([
        ["create_fixed_length_windows", {"mapping": {"rest": 0, "arithmetic": 8}}]])
    dump(root, attrs)
    for i in range(3):
        path = source.cache / ZROOT / f"recording_{i}/metadata.tsv"
        table = pd.read_csv(path, sep="\t", index_col=0)
        table["target"] = [0, 8]
        table.to_csv(path, sep="\t")
    meta = convert(source, tmp_path / "out", smoke=False)
    assert meta["classes"] == 2 and meta["declared_source_classes"] == 9
    folder = tmp_path / "out/arithmetic_zyma2019"
    export_ts(folder, tmp_path / "ts")
    _, labels = load_from_ts_file(tmp_path / "ts/arithmetic_zyma2019_TRAIN.ts")
    assert labels.tolist() == ["0", "8", "0", "8"]


def test_metadata_row_count_is_rejected(source):
    path = source.cache / ZROOT / "recording_1/metadata.tsv"
    pd.read_csv(path, sep="\t").iloc[:1].to_csv(path, sep="\t", index=False)
    with pytest.raises(ValueError, match="metadata length"):
        load_records(source)


def test_duplicates_across_partitions_rejected(source, tmp_path):
    src = f"{ZROOT}/recording_0/data/c/0/0/0"
    dst = f"{ZROOT}/recording_2/data/c/0/0/0"
    (source.cache / dst).write_bytes((source.cache / src).read_bytes())
    source.files[dst] = dict(source.files[src], path=dst)
    with pytest.raises(ValueError, match="identical signal"):
        convert(source, tmp_path / "out", smoke=False)
    assert not (tmp_path / "out/arithmetic_zyma2019/manifest.json").exists()


def test_output_tampering_detected(source, tmp_path):
    convert(source, tmp_path / "out", smoke=False)
    folder = tmp_path / "out/arithmetic_zyma2019"
    with h5py.File(folder / "arrays.h5", "r+") as f:
        f["X_train"][0, 0, 0] = 999
    with pytest.raises(ValueError, match="correspondence"):
        validate_arrays(folder, source.config)


def test_missing_chunks_are_not_zero_filled(source, tmp_path):
    del source.files[f"{ZROOT}/recording_0/data/c/0/0/0"]
    with pytest.raises(ValueError, match="Missing signal chunk"):
        convert(source, tmp_path / "out", smoke=False)


def test_facED_gate_and_no_seed_v(tmp_path):
    assert not any("seed" in name for name in DATASETS)
    assert DATASETS["faced"]["local_preparation_only"] is True
    with pytest.raises(ValueError, match="Missing original-source access evidence"):
        verify_licence(Source(DATASETS["faced"], tmp_path))


def test_split_ids_and_checksums():
    assert partition(1, DATASETS["bcic2a"]) == "train"
    assert partition(6, DATASETS["bcic2a"]) == "validation"
    assert partition(9, DATASETS["bcic2a"]) == "test"
    assert partition("II001", DATASETS["isruc-sleep"]) == "excluded"
    assert partition("I091", DATASETS["isruc-sleep"]) == "test"
    assert partition("00", DATASETS["arithmetic_zyma2019"]) == "train"
    with pytest.raises(ValueError):
        partition(0, DATASETS["arithmetic_zyma2019"])
    assert partition("02", DATASETS["bcic2020-3"]) == "test"
    assert case_hash(np.array([0.0], dtype="f4")) == case_hash(np.array([-0.0], dtype="f4"))
    with pytest.raises(ValueError, match="checksum"):
        check_blob(b"corrupt", dict(path="x", size=7, oid="wrong"))
    with pytest.raises(ValueError, match="Unsafe"):
        safe_path("root", "../secret")


def test_intentional_run_split_allows_shared_subject(source, tmp_path):
    source.config["split_key"] = "run"
    for i in range(3):
        path = source.cache / ZROOT / f"recording_{i}/zarr.json"
        data = read_json(path)
        data["attributes"]["description"]["subject"] = "00"
        dump(path, data)
    convert(source, tmp_path / "out", smoke=False)
    report = read_json(tmp_path / "out/arithmetic_zyma2019/validation.json")
    assert report["subject_overlap"] == ["00"]
    assert report["subject_overlap_intentional"] and report["passed"]


def test_source_label_mismatch_is_detected_even_if_outputs_agree(source, tmp_path):
    convert(source, tmp_path / "out", smoke=False)
    folder = tmp_path / "out/arithmetic_zyma2019"
    table = pd.read_parquet(folder / "cases_train.parquet")
    table.loc[0, "label_encoded"] = 1
    table.to_parquet(folder / "cases_train.parquet")
    with h5py.File(folder / "arrays.h5", "r+") as f:
        f["y_train"][0] = 1
    with pytest.raises(ValueError, match="distributed source rows"):
        validate_arrays(folder, source.config)


def test_interrupted_conversion_resumes_without_refetching_completed_records(source, tmp_path):
    fetch = source.fetch
    fetched = []
    def fail_second_record(name, target=None):
        fetched.append(name)
        if "/recording_1/data/c/" in name:
            raise OSError("simulated interrupted download")
        return fetch(name, target)
    source.fetch = fail_second_record
    with pytest.raises(OSError, match="interrupted"):
        convert(source, tmp_path / "out", smoke=False)
    source.fetch = fetch
    convert(source, tmp_path / "out", smoke=False, resume=True)
    X, y, _, _ = load_prepared(tmp_path / "out/arithmetic_zyma2019")
    assert X[:, 0, 0].tolist() == [0, 6, 100, 106]
    assert y.tolist() == [0, 1, 0, 1]
    assert len([n for n in fetched if "/recording_0/" in n]) == 1


def test_padded_multi_chunk_zarr(source):
    from .prepare import read_array
    attrs, records = load_records(source)
    r = records[0]
    r["array"]["chunk_grid"]["configuration"]["chunk_shape"] = [1, 2, 4]
    expected = np.arange(12, dtype="<f4").reshape(2, 2, 3)
    for i in range(2):
        padded = np.zeros((1, 2, 4), dtype="<f4")
        padded[0, :, :3] = expected[i]
        data = gzip.compress(padded.tobytes(), mtime=0)
        name = r["relative"] + f"/data/c/{i}/0/0"
        path = source.cache / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        source.files[name] = dict(path=name, size=len(data), lfs=dict(oid=hashlib.sha256(data).hexdigest()))
    actual, receipts = read_array(r, source)
    np.testing.assert_array_equal(actual, expected)
    assert len(receipts) == 2


def test_protocol_exclusion_is_explicit():
    assert partition("chb24", DATASETS["chbmit"]) == "excluded"
    with pytest.raises(ValueError, match="Unassigned"):
        partition("chb25", DATASETS["chbmit"])


def test_quarantine_keeps_rejected_data_out_of_ts_export(source, tmp_path):
    from .prepare import SCRIPT_BYTES, REGISTRY_BYTES
    from .report import quarantine_manifest
    src = f"{ZROOT}/recording_0/data/c/0/0/0"
    dst = f"{ZROOT}/recording_2/data/c/0/0/0"
    (source.cache / dst).write_bytes((source.cache / src).read_bytes())
    source.files[dst] = dict(source.files[src], path=dst)
    with pytest.raises(ValueError, match="identical signal"):
        convert(source, tmp_path / "out", smoke=False)
    folder = tmp_path / "out/arithmetic_zyma2019"
    (folder / "conversion_code").mkdir(exist_ok=True)
    (folder / "conversion_code/prepare.py").write_bytes(SCRIPT_BYTES)
    (folder / "conversion_code/registry.py").write_bytes(REGISTRY_BYTES)
    manifest = quarantine_manifest(folder, source.config)
    assert manifest["status"] == "quarantined"
    assert not (folder / "manifest.json").exists()
    assert len(pd.read_csv(folder / "cross-split-duplicates.csv")) == 2
    with pytest.raises(ValueError, match="Validation failed"):
        export_ts(folder, tmp_path / "ts")


def test_report_measures_actual_case_fields_and_does_not_invent_pilot_success(source, tmp_path):
    from .prepare import inspect_report
    from .report import build_report
    for i in range(3):
        dump(source.cache / f"original-source/bids/sub-{i:02d}_eeg.json", {"SamplingFrequency": 500.0})
    attrs, records = load_records(source)
    inspect_report(source, attrs, records)
    convert(source, tmp_path / "out", smoke=False)
    folder = tmp_path / "out/arithmetic_zyma2019"
    legacy = read_json(folder / "metadata-completeness.json")
    del legacy["original_frequency_from_bids"]
    dump(folder / "metadata-completeness.json", legacy)
    report = build_report(tmp_path / "cache", tmp_path / "out")
    assert report["completeness"]["arithmetic_zyma2019"]["original_frequency_from_bids"]["available"] == 6
    assert not any("Arithmetic .ts pilot:" in f for f in report["findings"])
