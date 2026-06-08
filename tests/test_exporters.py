import csv
import json

import pytest

from systemmonitor.utils.exporters import DataExporter


SAMPLE_DATA = {
    'cpu': {'percent': 42.5, 'core_count': 8},
    'disks': [
        {'device': 'C:', 'percent': 70},
        {'device': 'D:', 'percent': 30},
    ],
}


@pytest.fixture
def exporter(qapp):
    return DataExporter()


def test_flatten_dict_handles_nested_dicts_and_lists(exporter):
    flat = exporter._flatten_dict(SAMPLE_DATA)
    assert flat['cpu.percent'] == 42.5
    assert flat['cpu.core_count'] == 8
    assert flat['disks[0].device'] == 'C:'
    assert flat['disks[1].percent'] == 30


def test_export_snapshot_csv(tmp_path, exporter):
    target = tmp_path / "snapshot.csv"
    results = []
    exporter.export_completed.connect(lambda ok, msg: results.append((ok, msg)))
    try:
        exporter.export_snapshot(SAMPLE_DATA, str(target), 'csv')
    finally:
        exporter.export_completed.disconnect()

    assert results and results[0][0] is True
    assert target.exists()

    with open(target, newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    assert rows[0] == ['Metric', 'Value']
    assert ['cpu.percent', '42.5'] in rows


def test_export_snapshot_json(tmp_path, exporter):
    target = tmp_path / "snapshot.json"
    results = []
    exporter.export_completed.connect(lambda ok, msg: results.append((ok, msg)))
    try:
        exporter.export_snapshot(SAMPLE_DATA, str(target), 'JSON')
    finally:
        exporter.export_completed.disconnect()

    assert results and results[0][0] is True
    with open(target, encoding='utf-8') as f:
        loaded = json.load(f)
    assert 'timestamp' in loaded
    assert loaded['data'] == SAMPLE_DATA


def test_export_snapshot_txt(tmp_path, exporter):
    target = tmp_path / "snapshot.txt"
    results = []
    exporter.export_completed.connect(lambda ok, msg: results.append((ok, msg)))
    try:
        exporter.export_snapshot(SAMPLE_DATA, str(target), 'txt')
    finally:
        exporter.export_completed.disconnect()

    assert results and results[0][0] is True
    text = target.read_text(encoding='utf-8')
    assert "System Monitor Export" in text
    assert "cpu:" in text
    assert "percent: 42.5" in text


def test_export_snapshot_unsupported_format_emits_failure(tmp_path, exporter):
    target = tmp_path / "snapshot.xyz"
    results = []
    exporter.export_completed.connect(lambda ok, msg: results.append((ok, msg)))
    try:
        exporter.export_snapshot(SAMPLE_DATA, str(target), 'xyz')
    finally:
        exporter.export_completed.disconnect()

    assert results
    ok, message = results[0]
    assert ok is False
    assert "Unsupported format" in message
    assert not target.exists()
