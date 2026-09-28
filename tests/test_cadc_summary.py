from types import SimpleNamespace

from dtcli.utilities import cadcclient


def test_metadata_summary_aggregates_multiple_files(monkeypatch):
    records = iter(
        [
            dict(
                id="a",
                name="first",
                size=3,
                md5sum="x",
                file_type="hdf5",
                encoding=None,
                lastmod=8,
            ),
            dict(
                id="b",
                name="second",
                size=5,
                md5sum="y",
                file_type="hdf5",
                encoding="gzip",
                lastmod=2,
            ),
        ]
    )
    client = SimpleNamespace(cadcinfo=lambda uri: SimpleNamespace(**next(records)))
    monkeypatch.setattr(cadcclient, "_connect", lambda: (None, client, None))
    (summary,) = cadcclient.info(["first", "second"], summary=True)
    assert summary == {
        "ids": {"a", "b"},
        "names": {"first", "second"},
        "size": 8,
        "md5sums": {"x", "y"},
        "file_types": {"hdf5"},
        "encodings": {None, "gzip"},
        "oldestmod": 2,
        "newestmod": 8,
    }
