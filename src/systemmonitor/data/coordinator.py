"""
Data Collector Coordinator - Manages all data collection threads
Professional technician-grade system monitoring
"""
import time
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from systemmonitor.utils.logger import get_logger, LogCategory, log_info, log_warning, log_error


class DataCollectorCoordinator(QObject):
    """
    Central coordinator for all data collection threads.
    Aggregates data from all collectors and emits unified signals.
    Runs in main thread but spawns separate collector threads.
    """

    # Unified signal emitted with all aggregated data
    data_ready = pyqtSignal(dict)

    # Signal for storage/partition updates (less frequent)
    storage_updated = pyqtSignal(list)

    # Signal for system info (static info, cached)
    system_info_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._collectors = {}
        self._aggregated_data = {}
        self._last_storage_update = 0
        self._last_system_info_update = 0
        self._storage_interval = 5  # seconds
        self._system_info_interval = 30  # seconds

        # Debounce timer to limit UI updates
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._emit_data)

        self._pending_update = False

        self._alert_manager = None
        self._alerts_ready = False

        self._prometheus_exporter = None

    def _interval_scale_for(self, update_interval_ms) -> float:
        """Map the 'update_interval' setting (ms) to a scale factor relative
        to the Normal baseline (AppConfig.UPDATE_INTERVAL_MS), which the
        collectors' hardcoded REFRESH_INTERVAL values are tuned for."""
        from systemmonitor.config import AppConfig
        try:
            ms = float(update_interval_ms)
        except (TypeError, ValueError):
            ms = AppConfig.UPDATE_INTERVAL_MS
        if ms <= 0:
            ms = AppConfig.UPDATE_INTERVAL_MS
        return ms / AppConfig.UPDATE_INTERVAL_MS

    def _apply_update_speed(self, update_interval_ms=None):
        """Apply the configured Update Speed to all running collectors."""
        from systemmonitor.config import settings
        if update_interval_ms is None:
            update_interval_ms = settings.get('update_interval', 500)
        scale = self._interval_scale_for(update_interval_ms)
        for collector in self._collectors.values():
            if hasattr(collector, 'set_interval_scale'):
                collector.set_interval_scale(scale)

    def start(self):
        """Start all data collection threads"""
        log_info(LogCategory.COLLECTOR, "Starting DataCollectorCoordinator")

        # Import and create collectors
        from systemmonitor.data.collector import (
            CPUCollectorThread,
            MemoryCollectorThread,
            DiskCollectorThread,
            NetworkCollectorThread,
            GPUCollectorThread,
            SystemInfoCollectorThread,
        )

        # CPU collector - high frequency
        self._collectors['cpu'] = CPUCollectorThread()
        self._collectors['cpu'].data_updated.connect(lambda d: self._on_collector_update('cpu', d))
        self._collectors['cpu'].start()

        # Memory collector - medium frequency
        self._collectors['memory'] = MemoryCollectorThread()
        self._collectors['memory'].data_updated.connect(lambda d: self._on_collector_update('memory', d))
        self._collectors['memory'].start()

        # Disk collector - lower frequency
        self._collectors['disk'] = DiskCollectorThread()
        self._collectors['disk'].data_updated.connect(lambda d: self._on_collector_update('disk', d))
        self._collectors['disk'].start()

        # Network collector - high frequency
        self._collectors['network'] = NetworkCollectorThread()
        self._collectors['network'].data_updated.connect(lambda d: self._on_collector_update('network', d))
        self._collectors['network'].start()

        # GPU collector - medium frequency
        self._collectors['gpu'] = GPUCollectorThread()
        self._collectors['gpu'].data_updated.connect(lambda d: self._on_collector_update('gpu', d))
        self._collectors['gpu'].start()

        # System info collector - low frequency (static data)
        self._collectors['system_info'] = SystemInfoCollectorThread()
        self._collectors['system_info'].data_updated.connect(self._on_system_info_update)
        self._collectors['system_info'].start()

        log_info(LogCategory.COLLECTOR, f"Started {len(self._collectors)} collector threads")

        self._apply_update_speed()
        self._init_alerts()
        self._init_prometheus_exporter()

    def stop(self):
        """Stop all data collection threads"""
        log_info(LogCategory.COLLECTOR, "Stopping DataCollectorCoordinator")

        if self._prometheus_exporter is not None:
            self._prometheus_exporter.stop()
            self._prometheus_exporter = None

        for name, collector in self._collectors.items():
            collector.stop()
            collector.wait(2000)  # Wait up to 2 seconds for thread to finish

        self._collectors.clear()

    def _init_alerts(self):
        """Initialize alert system and wire it to settings"""
        try:
            from systemmonitor.data.alerts import AlertManager
            from systemmonitor.config import settings
            from systemmonitor.core.signals import signal_bus

            self._alert_manager = AlertManager()

            # Apply saved thresholds and enabled state
            self._alert_manager.set_globally_enabled(settings.get('alerts_enabled', True))
            self._alert_manager.update_rule_threshold(
                'cpu_percent', float(settings.get('alert_cpu_threshold', 80)))
            self._alert_manager.update_rule_threshold(
                'memory_percent', float(settings.get('alert_memory_threshold', 85)))
            self._alert_manager.update_rule_threshold(
                'disk_percent', float(settings.get('alert_disk_threshold', 90)))
            self._alert_manager.update_rule_threshold(
                'cpu_temperature', float(settings.get('alert_temperature_threshold', 80)))
            self._alert_manager.update_rule_threshold(
                'gpu_temperature', float(settings.get('alert_gpu_threshold', 85)))

            # Forward triggered alerts to the global signal bus
            self._alert_manager.alert_triggered.connect(self._on_alert_triggered)

            # React to settings changes from the UI
            signal_bus.setting_changed.connect(self._on_setting_changed)

            self._alerts_ready = True
            log_info(LogCategory.COLLECTOR, "Alert system initialized")
        except Exception as e:
            log_error(LogCategory.COLLECTOR, f"Alert system init failed: {e}")

    def _init_prometheus_exporter(self):
        """Create the exporter and start it if enabled in settings."""
        try:
            from systemmonitor.utils.prometheus_exporter import PrometheusExporter
            from systemmonitor.config import settings

            self._prometheus_exporter = PrometheusExporter(self.get_data)
            if settings.get('prometheus_enabled', False):
                self._start_prometheus_exporter(int(settings.get('prometheus_port', 9090)))
        except Exception as e:
            log_error(LogCategory.COLLECTOR, f"Prometheus exporter init failed: {e}")

    def _start_prometheus_exporter(self, port: int):
        if self._prometheus_exporter is None:
            return
        try:
            self._prometheus_exporter.start(port)
        except Exception as e:
            log_error(LogCategory.COLLECTOR, f"Prometheus exporter could not start on port {port}: {e}")

    def _apply_prometheus_setting(self, key: str, value):
        if self._prometheus_exporter is None:
            return
        from systemmonitor.config import settings
        try:
            if key == 'prometheus_enabled':
                if value:
                    self._start_prometheus_exporter(int(settings.get('prometheus_port', 9090)))
                else:
                    self._prometheus_exporter.stop()
            elif key == 'prometheus_port':
                if settings.get('prometheus_enabled', False):
                    self._start_prometheus_exporter(int(value))
        except Exception as e:
            log_error(LogCategory.COLLECTOR, f"Prometheus exporter setting update failed: {e}")

    def _on_alert_triggered(self, alert):
        """Convert Alert object to dict and forward to signal bus"""
        try:
            from systemmonitor.core.signals import signal_bus
            level_val = (alert.rule.level.value
                         if hasattr(alert.rule.level, 'value')
                         else str(alert.rule.level))
            signal_bus.alert_triggered.emit({
                'id': alert.id,
                'metric': alert.rule.metric,
                'value': alert.value,
                'threshold': alert.rule.threshold,
                'level': level_val,
                'message': alert.message,
                'timestamp': alert.timestamp,
            })
        except Exception as e:
            log_error(LogCategory.COLLECTOR, f"Alert forward failed: {e}")

    def _on_setting_changed(self, key: str, value):
        """React to relevant settings changes (alert rules, collection speed)"""
        if key == 'update_interval':
            try:
                self._apply_update_speed(value)
            except Exception as e:
                log_error(LogCategory.COLLECTOR, f"Update speed change failed: {e}")
            return

        if key in ('prometheus_enabled', 'prometheus_port'):
            self._apply_prometheus_setting(key, value)
            return

        if self._alert_manager is None:
            return
        try:
            if key == 'alerts_enabled':
                self._alert_manager.set_globally_enabled(bool(value))
            elif key == 'alert_cpu_threshold':
                self._alert_manager.update_rule_threshold('cpu_percent', float(value))
            elif key == 'alert_memory_threshold':
                self._alert_manager.update_rule_threshold('memory_percent', float(value))
            elif key == 'alert_disk_threshold':
                self._alert_manager.update_rule_threshold('disk_percent', float(value))
            elif key == 'alert_temperature_threshold':
                self._alert_manager.update_rule_threshold('cpu_temperature', float(value))
            elif key == 'alert_gpu_threshold':
                self._alert_manager.update_rule_threshold('gpu_temperature', float(value))
        except Exception as e:
            log_error(LogCategory.COLLECTOR, f"Setting update failed: {e}")

    def _check_alerts(self, snapshot: dict):
        """Evaluate current metrics against all alert rules"""
        if not self._alerts_ready or self._alert_manager is None:
            return
        try:
            cpu = snapshot.get('cpu', {})
            if isinstance(cpu, dict):
                if cpu.get('percent') is not None:
                    self._alert_manager.check_metric('cpu_percent', float(cpu['percent']))
                if cpu.get('temperature') is not None:
                    self._alert_manager.check_metric('cpu_temperature', float(cpu['temperature']))

            memory = snapshot.get('memory', {})
            if isinstance(memory, dict) and memory.get('percent') is not None:
                self._alert_manager.check_metric('memory_percent', float(memory['percent']))

            gpu = snapshot.get('gpu', {})
            if isinstance(gpu, dict) and gpu.get('temperature') is not None:
                self._alert_manager.check_metric('gpu_temperature', float(gpu['temperature']))

            disk = snapshot.get('disk', {})
            if isinstance(disk, dict):
                partitions = disk.get('partitions', [])
                if partitions:
                    max_pct = max(p.get('percent', 0) for p in partitions)
                    self._alert_manager.check_metric('disk_percent', float(max_pct))
        except Exception as e:
            log_error(LogCategory.COLLECTOR, f"Alert check error: {e}")

    def _on_collector_update(self, name: str, data: dict):
        """Handle updates from individual collectors"""
        self._aggregated_data[name] = data

        # Schedule debounced emit
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(50)  # 50ms debounce

    def _emit_data(self):
        """Emit aggregated data to UI (debounced)"""
        self._pending_update = False
        snapshot = self._aggregated_data.copy()
        self.data_ready.emit(snapshot)
        from systemmonitor.core.signals import signal_bus
        signal_bus.data_updated.emit(snapshot)
        self._check_alerts(snapshot)

    def _on_system_info_update(self, data: dict):
        """Handle system info updates"""
        self._aggregated_data['system_info'] = data
        self.system_info_updated.emit(data)

    def get_data(self) -> dict:
        """Get current aggregated data"""
        return self._aggregated_data.copy()


# Backwards compatibility alias
DataCollector = DataCollectorCoordinator
