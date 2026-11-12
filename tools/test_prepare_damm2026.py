"""Unit tests for Damm2026 (ImaginedFingers) native BIDS verification and split."""

import csv
import json
from pathlib import Path
import tempfile

import numpy as np
import pytest

from tools.prepare_damm2026 import (
    EXPECTED_62_CHANNELS,
    LABELS,
    LOCK_PATH,
    TEST_SUBJECTS,
    TRAIN_SUBJECTS,
    extract_finger_blocks,
    parse_events_vector,
)


def test_split_partitions_twenty_subjects_cleanly():
    """The 15/5 whole-subject split covers 01..20 with zero overlap."""
    expected_all = {f"{idx:02d}" for idx in range(1, 21)}
    n_train = 15
    n_test = 5
    assert len(TRAIN_SUBJECTS) == n_train
    assert len(TEST_SUBJECTS) == n_test
    assert TRAIN_SUBJECTS.isdisjoint(TEST_SUBJECTS)
    assert TRAIN_SUBJECTS | TEST_SUBJECTS == expected_all
    assert "18" in TRAIN_SUBJECTS  # single truncated recording stays in TRAIN
    assert len(EXPECTED_62_CHANNELS) == len(set(EXPECTED_62_CHANNELS))
    assert set(LABELS) == {"1", "2", "3", "4", "5"}


def test_source_lock_excludes_redundant_sourcedata_csv_tree():
    """Source lock pins all 80 BIDS EDFs while excluding the 27.15 GB CSV duplicate."""
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    edf_files = [f for f in lock["files"] if f["name"].endswith("_eeg.edf")]
    events_files = [f for f in lock["files"] if f["name"].endswith("_events.tsv")]
    n_expected_runs = 80
    assert len(edf_files) == n_expected_runs
    assert len(events_files) == n_expected_runs
    assert not any("Raw CSV Dataset" in f["name"] for f in lock["files"])
    assert any(f["name"] == "sourcedata/counterbalancing_log.json" for f in lock["files"])


def test_parse_events_and_extract_finger_blocks_roundtrip():
    """Per-sample 512^2 BIDS onset reconstruction matches EDF Marker and handles truncation."""
    sfreq = 512.0
    points = 64
    n_fingers = 5
    gap = 16
    n_times = gap + n_fingers * (points + gap)
    marker = np.zeros(n_times, dtype=np.int64)
    for idx, code in enumerate((3, 4, 5, 6, 7)):
        start = gap + idx * (points + gap)
        marker[start : start + points] = code

    with tempfile.TemporaryDirectory() as tmp_dir:
        events_path = Path(tmp_dir) / "sub-01_events.tsv"
        with events_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(["onset", "duration", "trial_type"])
            for sample_idx, code in enumerate(marker):
                writer.writerow([f"{sample_idx / (sfreq * sfreq):.17g}", "0.0", str(code)])

        reconstructed, max_res = parse_events_vector(events_path, n_times=n_times, sfreq=sfreq)
        assert max_res < 1e-6
        blocks, excluded = extract_finger_blocks(
            marker,
            reconstructed,
            points=points,
            expected_full_blocks=n_fingers,
            allow_truncated_final=False,
        )
        assert len(blocks) == n_fingers
        assert excluded == []

        # Perturbing a single sample in Marker must fail cross-verification.
        corrupted = marker.copy()
        corrupted[gap] = 7
        with pytest.raises(ValueError, match="disagrees"):
            extract_finger_blocks(
                corrupted,
                reconstructed,
                points=points,
                expected_full_blocks=n_fingers,
            )

        # Truncated final cue is rejected by default and recorded when explicitly allowed.
        truncated_len = points - 10
        trunc_total = n_times + truncated_len + 4
        trunc_marker = np.zeros(trunc_total, dtype=np.int64)
        trunc_marker[:n_times] = marker
        trunc_marker[n_times : n_times + truncated_len] = 6
        with pytest.raises(ValueError, match="duration"):
            extract_finger_blocks(
                trunc_marker,
                trunc_marker.copy(),
                points=points,
                expected_full_blocks=n_fingers,
                allow_truncated_final=False,
            )
        comp_blocks, excl = extract_finger_blocks(
            trunc_marker,
            trunc_marker.copy(),
            points=points,
            expected_full_blocks=n_fingers,
            allow_truncated_final=True,
        )
        assert len(comp_blocks) == n_fingers
        assert len(excl) == 1
        assert excl[0]["available_samples"] == truncated_len
        assert excl[0]["source_event_code"] == 6
