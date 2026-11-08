"""Native column selection, cue timing, bounds and ID parsing."""
import numpy as np
import pytest

from tools.prepare_imagined_grip_force import identify, windows


def test_filename_ids_and_force_level_are_preserved_without_inventing_classes():
    assert identify('user001_40_2.txt') == ('001', '40', '2')
    for bad in ['user001_0_1.txt', 'user001_70_3.txt', 'user011_10_1.txt', '../user001_10_1.txt']:
        with pytest.raises(ValueError):
            identify(bad)


def test_protocol_crops_keep_native_eeg_axis_and_exclude_auxiliary_columns():
    data = np.arange(5300*23, dtype=np.float64).reshape(5300, 23)
    epochs = list(windows(data))
    assert len(epochs) == 5
    first, index, onset, start, end = epochs[0]
    assert (index, onset, start, end) == (0, 2.9, 371, 1011)
    assert first.shape == (14, 640) and first.dtype == np.float64
    np.testing.assert_array_equal(first, data[371:1011, 2:16].T)
    last, _, _, start, end = epochs[-1]
    assert (start, end) == (4467, 5107)
    np.testing.assert_array_equal(last, data[start:end, 2:16].T)


def test_incomplete_trial_is_rejected_rather_than_padded_or_silently_dropped():
    with pytest.raises(ValueError, match='Incomplete'):
        list(windows(np.ones((5106, 23))))


def test_changed_schema_and_nonfinite_data_are_rejected():
    for data in [np.ones((5300, 22)), np.full((5300, 23), np.nan)]:
        with pytest.raises(ValueError, match='23-column'):
            list(windows(data))
