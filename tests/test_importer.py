from pathlib import Path

from utils.importer import import_records


def test_import_csv_sample():
    rows = import_records(Path("samples/sample_data.csv"))
    assert len(rows) >= 3
    assert rows[0]["nombre"] == "Laura"
