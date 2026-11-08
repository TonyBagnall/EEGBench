"""BI2014a channel evidence, event epoching and archive validation tests."""

import csv
import hashlib
import io
import json
import zipfile

import numpy as np
import pytest
from scipy.io import savemat

from tools.prepare_moabb import CHANNELS, NAME, RECORD, convert, event_onsets, sources


def source_fixture(tmp_path, duplicate=False, wrong_header=False):
    cache = tmp_path / "source"
    cache.mkdir()
    channels = CHANNELS.copy()
    if wrong_header:
        channels[2] = "F3"
    (cache / "Header.csv").write_text(",".join(["Time", *channels, "Event", "Target"]))
    for subject in (1, 2):
        array = np.zeros((1800, 19))
        array[:, 0] = np.arange(1800) / 512
        array[:, 1:17] = np.arange(1800)[:, None] * 0.1 + np.arange(16) + (1 if duplicate else subject) * 0.125
        # One held marker and one overlapping epoch; final onset is too near EOF.
        array[100:103, 18] = 1
        array[200, 18] = 2
        array[1500, 18] = 1
        array[100:103, 17] = 20
        array[200, 17] = 60
        array[1500, 17] = 21
        raw = io.BytesIO()
        savemat(raw, {"samples": array})
        with zipfile.ZipFile(cache / f"subject_{subject:02d}.zip", "w") as zipped:
            zipped.writestr(f"subject_{subject:02d}.mat", raw.getvalue())
    files = [dict(key=p.name, size=p.stat().st_size, checksum="md5:" + hashlib.md5(p.read_bytes()).hexdigest(),
                  links={"self": "https://example.invalid/" + p.name}) for p in cache.iterdir()]
    record = dict(id=RECORD, metadata=dict(license={"id": "cc-by-4.0"}, creators=[]), files=files)
    (cache / f"zenodo-record-{RECORD}.json").write_text(json.dumps(record))
    for label in ("moabb", "author"):
        (cache / f"{label}-loader.py").write_text("# Test evidence only\n")
    return cache


def test_subject_split_channels_bounds_and_roundtrip(tmp_path):
    metadata, validation = convert(source_fixture(tmp_path), tmp_path / "out", subjects=(1,2), train=(1,), download=False, smoke=False)
    folder = tmp_path / "out" / NAME
    assert metadata["channel_names"] == CHANNELS
    assert metadata["channel_names"][2:5] == ["F5", "AFZ", "F6"]
    assert metadata["shapes"] == {"train": [2,16,512], "test": [2,16,512]}
    assert validation["cross_split_duplicate_signal_hashes"] == 0
    assert len(validation["dropped_events"]) == 2
    assert validation["partitions"]["TRAIN"]["exact_float32_roundtrip"]
    with (folder / "cases_test.tsv").open(newline="") as file:
        rows = list(csv.DictReader(file, delimiter="\t"))
    assert [r["participant_id"] for r in rows] == ["02", "02"]
    assert [r["start_sample"] for r in rows] == ["100", "200"]
    assert [r["end_sample"] for r in rows] == ["612", "712"]
    assert [r["source_epoch_index"] for r in rows] == ["0", "1"]
    assert [r["label"] for r in rows] == ["1", "2"]
    assert all(r["session_id"] == "" and r["loader_session_id"] == "0" for r in rows)
    with pytest.raises(FileExistsError):
        convert(tmp_path / "source", tmp_path / "out", subjects=(1,2), train=(1,), download=False, smoke=False)


def test_changed_source_channel_header_rejected(tmp_path):
    cache = source_fixture(tmp_path, wrong_header=True)
    with pytest.raises(ValueError, match="channel header"):
        sources(cache, subjects=(1,2), download=False)


def test_source_tampering_rejected(tmp_path):
    cache = source_fixture(tmp_path)
    with (cache / "subject_01.zip").open("ab") as file:
        file.write(b"changed")
    with pytest.raises(ValueError, match="modified source"):
        sources(cache, subjects=(1,2), download=False)


def test_duplicate_signals_across_subjects_rejected(tmp_path):
    with pytest.raises(ValueError, match="Signal duplicates"):
        convert(source_fixture(tmp_path, duplicate=True), tmp_path / "out", subjects=(1,2), train=(1,), download=False, smoke=False)
    assert not (tmp_path / "out" / NAME).exists()


def test_held_marker_has_one_onset():
    array = np.zeros((12,19))
    array[2:5,18] = 1
    array[7,18] = 2
    np.testing.assert_array_equal(event_onsets(array), [2,7])
