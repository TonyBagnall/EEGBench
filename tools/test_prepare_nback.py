"""Check joint labels, confirmed subject blocks and lossless NBack export."""

import csv
import json

import pytest

from tools.prepare_nback import LABELS, Layout, NAME, parse_source, prepare


def source_file(tmp_path, duplicate=False):
    path = tmp_path / "source.txt"
    lines = []
    for subject in range(1, 4):
        for label in LABELS:
            value = 1 if duplicate else subject
            lines.append(f"{value}.{label},2,3:4,5,6\x00:{label % 10} {label // 10} {label}\n")
    path.write_text("".join(lines), encoding="ascii")
    return path


def test_export_joint_labels_and_metadata(tmp_path):
    layout = Layout(subjects=3, rows_per_subject=12, channels=2, timepoints=3,
                    excluded=(2,), train=(1,))
    metadata, validation = prepare(source_file(tmp_path), tmp_path / "output", layout, smoke=False)
    folder = tmp_path / "output" / NAME
    assert metadata["shapes"] == {"train": [12, 2, 3], "test": [12, 2, 3]}
    assert metadata["channel_names"] == [None, None]
    assert metadata["sampling_frequency_hz"] == 200
    assert metadata["original_sampling_frequency_hz"] == 200
    assert metadata["window_seconds"] == 3 / 200
    assert metadata["sessions"] is None
    assert validation["cross_split_duplicate_signal_hashes"] == 0
    for split, subject, start in [("train", "1", 0), ("test", "3", 24)]:
        with (folder / f"cases_{split}.tsv").open(newline="") as file:
            rows = list(csv.DictReader(file, delimiter="\t"))
        assert [int(r["source_row_index"]) for r in rows] == list(range(start, start + 12))
        assert {r["participant_id"] for r in rows} == {subject}
        assert [int(r["label"]) for r in rows] == LABELS
        assert all(r["session_id"] == "" for r in rows)
    manifest = json.loads((folder / f"{NAME}_manifest.json").read_text())
    assert manifest["source"]["sha256"]
    assert manifest["split"]["excluded"] == ["2"]
    with pytest.raises(FileExistsError):
        prepare(source_file(tmp_path), tmp_path / "output", layout, smoke=False)


def test_cross_partition_duplicates_rejected(tmp_path):
    layout = Layout(subjects=3, rows_per_subject=12, channels=2, timepoints=3,
                    excluded=(2,), train=(1,))
    with pytest.raises(ValueError, match="duplicate signal"):
        prepare(source_file(tmp_path, duplicate=True), tmp_path / "output", layout, smoke=False)
    assert not (tmp_path / "output" / NAME).exists()


@pytest.mark.parametrize("line", [b"1,2,3:4,5,6:0 1 0", b"1,2:4,5,6:0 0 0", b"nan,2,3:4,5,6:0 0 0"])
def test_invalid_source_rejected(line):
    with pytest.raises(ValueError):
        parse_source(line, Layout(channels=2, timepoints=3))
