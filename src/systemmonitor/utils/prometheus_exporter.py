"""Prometheus exporter - lightweight HTTP server exposing /metrics for scraping.

Runs a stdlib http.server in a background daemon thread so external tools
(Prometheus, Grafana agent, curl) can pull the latest aggregated snapshot in
the Prometheus text exposition format without installing extra dependencies.
"""
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Optional

from systemmonitor.utils.logger import LogCategory, log_info, log_error


def _escape_label(value: str) -> str:
    return str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def render_metrics(data: dict) -> str:
    """Render an aggregated data snapshot as Prometheus text exposition format."""
    lines = []

    def gauge(name: str, help_text: str, value):
        if value is None:
            return
        lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")

    cpu = data.get('cpu', {}) or {}
    gauge('systemmonitor_cpu_percent', 'Overall CPU usage percent', cpu.get('percent'))
    gauge('systemmonitor_cpu_temperature_celsius', 'CPU temperature in Celsius', cpu.get('temperature'))
    per_core = cpu.get('per_core') or []
    if per_core:
        lines.append("# HELP systemmonitor_cpu_core_percent Per-core CPU usage percent")
        lines.append("# TYPE systemmonitor_cpu_core_percent gauge")
        for i, pct in enumerate(per_core):
            lines.append(f'systemmonitor_cpu_core_percent{{core="{i}"}} {pct}')

    memory = data.get('memory', {}) or {}
    gauge('systemmonitor_memory_percent', 'Memory usage percent', memory.get('percent'))
    gauge('systemmonitor_memory_used_bytes', 'Memory used in bytes', memory.get('used'))
    gauge('systemmonitor_memory_total_bytes', 'Total memory in bytes', memory.get('total'))

    disk = data.get('disk', {}) or {}
    partitions = disk.get('partitions') or []
    if partitions:
        lines.append("# HELP systemmonitor_disk_usage_percent Disk usage percent per partition")
        lines.append("# TYPE systemmonitor_disk_usage_percent gauge")
        for part in partitions:
            pct = part.get('percent')
            if pct is None:
                continue
            device = _escape_label(part.get('device', 'unknown'))
            lines.append(f'systemmonitor_disk_usage_percent{{device="{device}"}} {pct}')

    network = data.get('network', {}) or {}
    gauge('systemmonitor_network_bytes_sent_total', 'Total bytes sent since boot', network.get('bytes_sent'))
    gauge('systemmonitor_network_bytes_recv_total', 'Total bytes received since boot', network.get('bytes_recv'))

    gpu = data.get('gpu', {}) or {}
    gauge('systemmonitor_gpu_load_percent', 'GPU load percent', gpu.get('load'))
    gauge('systemmonitor_gpu_temperature_celsius', 'GPU temperature in Celsius', gpu.get('temperature'))

    system_info = data.get('system_info', {}) or {}
    battery = system_info.get('battery') or {}
    if battery.get('percent') is not None:
        gauge('systemmonitor_battery_percent', 'Battery charge percent', battery.get('percent'))
        lines.append("# HELP systemmonitor_battery_plugged Whether the system is plugged into AC power (1=yes, 0=no)")
        lines.append("# TYPE systemmonitor_battery_plugged gauge")
        lines.append(f"systemmonitor_battery_plugged {1 if battery.get('power_plugged') else 0}")

    lines.append('')
    return '\n'.join(lines)


class _MetricsHandler(BaseHTTPRequestHandler):
    """Serves /metrics from a data_provider callback set on the class."""

    data_provider: Optional[Callable[[], dict]] = None

    def do_GET(self):
        if self.path != '/metrics':
            self.send_response(404)
            self.end_headers()
            return
        try:
            snapshot = self.data_provider() if self.data_provider else {}
            body = render_metrics(snapshot or {})
        except Exception:
            body = ''
        encoded = body.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        pass  # don't spam stderr with per-request access logs


class PrometheusExporter:
    """Background HTTP server exposing /metrics for Prometheus-style scraping."""

    def __init__(self, data_provider: Callable[[], dict]):
        self._data_provider = data_provider
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._port: Optional[int] = None

    def is_running(self) -> bool:
        return self._server is not None

    @property
    def port(self) -> Optional[int]:
        return self._port

    def start(self, port: int):
        """Start (or restart on a new port) the metrics HTTP server."""
        if self.is_running():
            if self._port == port:
                return
            self.stop()

        provider = self._data_provider
        handler = type('_BoundMetricsHandler', (_MetricsHandler,), {'data_provider': staticmethod(provider)})

        try:
            server = HTTPServer(('0.0.0.0', port), handler)
        except OSError as e:
            log_error(LogCategory.SERVICES, f"Prometheus exporter failed to bind port {port}: {e}")
            raise

        self._server = server
        self._port = port
        self._thread = threading.Thread(target=server.serve_forever, name='PrometheusExporter', daemon=True)
        self._thread.start()
        log_info(LogCategory.SERVICES, f"Prometheus exporter listening on http://localhost:{port}/metrics")

    def stop(self):
        if self._server is not None:
            try:
                self._server.shutdown()
                self._server.server_close()
            except Exception:
                pass
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        if self._port is not None:
            log_info(LogCategory.SERVICES, "Prometheus exporter stopped")
        self._port = None
