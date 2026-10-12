"""Tests for the archive lists and metadata."""

import pytest

from eegbench.datasets import (
    DOMAINS,
    by_domain,
    eegbench,
    eegbench_open,
    metadata,
    restricted,
)
from eegbench.estimators import ESTIMATORS, FAMILIES, PAPER_ESTIMATORS


def test_archive_lists():
    """30 problems, 28 of them open, with no repeats."""
    assert len(eegbench) == len(set(eegbench)) == 30
    assert len(eegbench_open) == 28
    assert set(eegbench) - set(eegbench_open) == set(restricted)


def test_domains_partition_the_archive():
    """Every dataset is in exactly one domain."""
    split = [name for domain in DOMAINS for name in by_domain(domain)]
    assert sorted(split) == sorted(eegbench)
    assert "FibroUEA" in by_domain("Med")
    assert "FibroUEA" not in by_domain("Med", open_only=True)
    with pytest.raises(ValueError):
        by_domain("Sleep")


def test_metadata():
    """The table has a row per dataset and the values of Table 1."""
    frame = metadata()
    assert list(frame.index) == eegbench
    assert frame.loc["Alzheimers", "length"] == 30000
    assert frame.loc["SitStand", "classes"] == 4
    assert frame["open"].sum() == 28


def test_estimators():
    """Every estimator has a known family, and the paper's eight are listed."""
    assert {family for family, _, _ in ESTIMATORS.values()} <= set(FAMILIES)
    assert set(PAPER_ESTIMATORS) <= set(ESTIMATORS)
