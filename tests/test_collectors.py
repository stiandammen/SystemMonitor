"""Collector tests — psutil is mocked so these run deterministically without
depending on the host machine's actual hardware state."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from systemmonitor.data.cpu import CPUCollector
from systemmonitor.data.memory import MemoryCollector


# ── CPUCollector ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("name, expected", [
    ("Intel(R) Core(TM) i7-9700K", "Intel"),
    ("AMD Ryzen 7 5800X", "AMD"),
    ("AMD EPYC 7763", "AMD"),
    ("Apple M2 Pro", "Apple"),
    ("ARM Cortex-A76", "ARM"),
    ("Some Mystery Chip", "Unknown"),
])
def test_detect_manufacturer(name, expected):
    collector = CPUCollector()
    assert collector._detect_manufacturer(name) == expected


def test_cpu_collect_uses_psutil_and_returns_expected_shape(monkeypatch):
    fake_psutil = SimpleNamespace(
        cpu_percent=MagicMock(side_effect=[55.5, [10.0, 20.0, 30.0, 40.0]]),
        cpu_freq=lambda: SimpleNamespace(current=3200.0, max=4500.0),
        cpu_times=lambda: SimpleNamespace(),
        cpu_stats=lambda: SimpleNamespace(ctx_switches=123, interrupts=456),
        cpu_count=lambda logical=True: 8 if logical else 4,
        sensors_temperatures=lambda: {},
    )
    monkeypatch.setitem(__import__('sys').modules, 'psutil', fake_psutil)

    collector = CPUCollector()
    monkeypatch.setattr(collector, '_get_temperature', lambda: 42.0)

    data = collector.collect()

    assert data['percent'] == 55.5
    assert data['per_core'] == [10.0, 20.0, 30.0, 40.0]
    assert data['core_count'] == 4
    assert data['thread_count'] == 8
    assert data['frequency_current'] == 3200.0
    assert data['frequency_max'] == 4500.0
    assert data['temperature'] == 42.0
    assert data['ctx_switches'] == 123
    assert data['interrupts'] == 456


def test_cpu_collect_falls_back_on_error(monkeypatch):
    collector = CPUCollector()

    def boom():
        raise RuntimeError("psutil exploded")

    fake_psutil = SimpleNamespace(cpu_percent=boom)
    monkeypatch.setitem(__import__('sys').modules, 'psutil', fake_psutil)

    data = collector.collect()
    assert data == collector._get_fallback_data()


def test_cpu_get_fallback_data_shape():
    collector = CPUCollector()
    fallback = collector._get_fallback_data()
    assert set(fallback.keys()) >= {
        'percent', 'per_core', 'core_count', 'thread_count',
        'frequency_current', 'frequency_max', 'temperature',
    }


# ── MemoryCollector ───────────────────────────────────────────────────────
def test_memory_collect_uses_psutil_and_returns_expected_shape(monkeypatch):
    vm = SimpleNamespace(total=16_000_000_000, available=8_000_000_000,
                         used=8_000_000_000, free=8_000_000_000, percent=50.0,
                         cached=1_000, buffers=500)
    swap = SimpleNamespace(total=2_000_000_000, used=0, free=2_000_000_000, percent=0.0)
    fake_psutil = SimpleNamespace(virtual_memory=lambda: vm, swap_memory=lambda: swap)
    monkeypatch.setitem(__import__('sys').modules, 'psutil', fake_psutil)

    data = MemoryCollector().collect()

    assert data['ram']['total'] == 16_000_000_000
    assert data['ram']['percent'] == 50.0
    assert data['ram']['cached'] == 1_000
    assert data['swap']['total'] == 2_000_000_000


def test_memory_collect_falls_back_on_error(monkeypatch):
    def boom():
        raise RuntimeError("psutil exploded")

    fake_psutil = SimpleNamespace(virtual_memory=boom)
    monkeypatch.setitem(__import__('sys').modules, 'psutil', fake_psutil)

    collector = MemoryCollector()
    data = collector.collect()
    assert data == collector._get_fallback_data()


def test_memory_fallback_data_shape():
    fallback = MemoryCollector()._get_fallback_data()
    assert fallback['ram']['percent'] == 0
    assert fallback['swap']['percent'] == 0


def test_memory_get_top_consumers_sorted_and_limited(monkeypatch):
    def make_proc(pid, name, mem_percent):
        proc = MagicMock()
        proc.info = {
            'pid': pid,
            'name': name,
            'memory_percent': mem_percent,
            'memory_info': SimpleNamespace(rss=mem_percent * 1_000_000),
        }
        return proc

    procs = [
        make_proc(1, 'low.exe', 1.0),
        make_proc(2, 'high.exe', 9.0),
        make_proc(3, 'mid.exe', 5.0),
        make_proc(4, 'zero.exe', 0.0),
    ]
    fake_psutil = SimpleNamespace(
        process_iter=lambda attrs: procs,
        NoSuchProcess=Exception,
        AccessDenied=Exception,
    )
    monkeypatch.setitem(__import__('sys').modules, 'psutil', fake_psutil)

    top = MemoryCollector().get_top_consumers(limit=2)

    assert [p['name'] for p in top] == ['high.exe', 'mid.exe']
    assert top[0]['memory_rss'] == 9_000_000
