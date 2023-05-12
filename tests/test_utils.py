from dtcli.utilities import utilities


def test_split():
    test_array = ["a", "b"]
    split_by = 2
    result = utilities.split(test_array, split_by)
    assert result == [["a"], ["b"]]
