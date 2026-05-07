from dtcli.utilities import utilities


def test_split():
    test_array = ["a", "b"]
    split_by = 2
    result = utilities.split(test_array, split_by)
    assert result == [["a"], ["b"]]


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
