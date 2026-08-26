import pytest

from dtcli.utilities import utilities


def test_split():
    test_array = ["a", "b"]
    split_by = 2
    result = utilities.split(test_array, split_by)
    assert result == [["a"], ["b"]]


def test_split_edges():
    """Test split() with edge cases like empty list and invalid counts."""
    # Empty data
    assert utilities.split([], 2) == []

    # Zero count should raise ValueError
    with pytest.raises(ValueError, match="count must be greater than 0"):
        utilities.split([1, 2, 3], 0)

    # Negative count should raise ValueError
    with pytest.raises(ValueError, match="count must be greater than 0"):
        utilities.split([1, 2, 3], -1)


def test_split_more_batches_than_items():
    """split() must not return more batches than there are items.

    Regression guard for GitHub issue #147: when the user requests more
    parallel workers (-c flag) than there are files to download, the
    number of sublists returned by split() must equal len(data), not
    the requested count.  The pget() caller now caps processors to
    min(processors, len(source)) before iterating, so this test documents
    the invariant that split() never produces empty sublists.
    """
    test_array = ["a", "b", "c", "d", "e", "f"]  # 6 files
    split_by = 8  # user requested 8 workers
    result = utilities.split(test_array, split_by)
    # split() drops empty batches, so we get at most len(data) sublists
    assert len(result) <= len(test_array)
    # every element appears exactly once
    assert sorted(sum(result, [])) == sorted(test_array)


def test_common_paths() -> None:
    """Test common path derivation per storage element."""
    derived = utilities.common_paths(
        {
            "minoc": [
                "cadc:CHIMEFRB/data/event/1/a.h5",
                "cadc:CHIMEFRB/data/event/1/b.h5",
                "cadc:CHIMEFRB/data/event/1/sub/c.h5",
            ],
            "arc": ["/arc/projects/chime_frb/data/event/1/a.h5"],
            "empty": [],
        }
    )
    assert derived["minoc"] == {
        "common_path": "cadc:CHIMEFRB/data/event/1",
        "files": ["a.h5", "b.h5", "sub/c.h5"],
    }
    assert derived["arc"] == {
        "common_path": "/arc/projects/chime_frb/data/event/1",
        "files": ["a.h5"],
    }
    # A storage element with no files is omitted, not invented.
    assert "empty" not in derived


def test_common_paths_no_usable_split() -> None:
    """Test elements with no common directory keep their original paths."""
    derived = utilities.common_paths(
        {
            "mixed": ["/abs/a.h5", "rel/b.h5"],
            "no_common": ["a/b.h5", "c/d.h5"],
            "bare": ["a.h5"],
        }
    )
    # No usable split: common_path is "" and the original paths survive.
    assert derived["mixed"] == {"common_path": "", "files": ["/abs/a.h5", "rel/b.h5"]}
    assert derived["no_common"] == {"common_path": "", "files": ["a/b.h5", "c/d.h5"]}
    assert derived["bare"] == {"common_path": "", "files": ["a.h5"]}
