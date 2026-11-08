"""Tests for the local D:/Data/EEG-compatible layout, using tiny source arrays."""

import numpy as np
import pandas as pd
import pytest

from .test_prepare import source
from .prepare import convert, read_json, SCRIPT_BYTES, REGISTRY_BYTES, ZROOT
from .export_local import export_dataset, parse_case
from .report import quarantine_manifest


def test_sparse_source_labels_load_with_aeon(tmp_path):
    from aeon.datasets import load_from_ts_file
    from .export_local import ts_header
    labels = [0, 1, 2, 3, 5, 6, 7, 8]
    path = tmp_path / "sparse.ts"
    path.write_text(ts_header("FACED", 1, 2, 8, class_values=labels)
                    + "".join(f"1,2:{label}\n" for label in labels), encoding="utf-8")
    X, y = load_from_ts_file(path)
    assert X.shape == (8, 1, 2)
    assert y.tolist() == [str(label) for label in labels]


def test_local_layout_roundtrip_and_leading_zero_ids(source, tmp_path):
    convert(source, tmp_path / "archive", smoke=False)
    manifest = export_dataset(tmp_path / "archive", tmp_path, "arithmetic_zyma2019", smoke=True)
    p = tmp_path / "MentalArithmetic"
    assert manifest["status"] == "validated"
    assert (p / "MentalArithmetic_TRAIN.ts").exists() and (p / "MentalArithmetic_TEST.ts").exists()
    assert (p / "channels.txt").read_text().strip() == "X-original, ECG-original"
    rows = pd.read_csv(p / "MentalArithmetic_rows.tsv", sep="\t", dtype=str, keep_default_na=False)
    assert rows.subject_id.tolist() == ["00", "00", "01", "01", "02", "02"]
    assert rows.split.tolist() == ["TRAIN"] * 4 + ["TEST"] * 2
    assert rows.row.tolist() == ["0", "1", "2", "3", "0", "1"]
    assert rows.validation_fold.tolist() == [""] * 6
    assert read_json(p / "MentalArithmetic_metadata.json")["related_local_dataset"]["name"] == "EEGMAT"
    assert read_json(p / "MentalArithmetic_validation.json")["aeon"]["passed"]
    with pytest.raises(FileExistsError):
        export_dataset(tmp_path / "archive", tmp_path, "arithmetic_zyma2019", smoke=False)


def test_quarantined_export_is_separate_and_marked(source, tmp_path):
    # Exercise isolation using the active synthetic dataset.
    src = f"{ZROOT}/recording_0/data/c/0/0/0"
    dst = f"{ZROOT}/recording_2/data/c/0/0/0"
    (source.cache / dst).write_bytes((source.cache / src).read_bytes())
    source.files[dst] = dict(source.files[src], path=dst)
    with pytest.raises(ValueError):
        convert(source, tmp_path / "archive", smoke=False)
    p = tmp_path / "archive/arithmetic_zyma2019"
    quarantine_manifest(p, source.config)
    with pytest.raises(ValueError, match="include-quarantined"):
        export_dataset(tmp_path / "archive", tmp_path, "arithmetic_zyma2019", smoke=False)
    result = export_dataset(tmp_path / "archive", tmp_path, "arithmetic_zyma2019", include_quarantined=True, smoke=False)
    folder = tmp_path / "_quarantine/MentalArithmetic"
    assert result["status"] == "quarantined"
    assert (folder / "QUARANTINED.txt").exists()
    assert (folder / "MentalArithmetic_TRAIN.ts").read_text().startswith("# QUARANTINED")
    assert not (tmp_path / "MentalArithmetic").exists()


def test_ts_case_structure_is_checked():
    X, y = parse_case("1,2:3,4:1\n", 2, 2)
    np.testing.assert_array_equal(X, [[1, 2], [3, 4]])
    assert y == 1
    with pytest.raises(ValueError, match="channels"):
        parse_case("1,2:1\n", 2, 2)
    with pytest.raises(ValueError, match="timepoint"):
        parse_case("1:2,3,4:1\n", 2, 2)


def test_removed_depression_cannot_be_exported(tmp_path):
    with pytest.raises(ValueError, match="Removed"):
        export_dataset(tmp_path, tmp_path, "mdd_mumtaz2016", include_quarantined=True)
