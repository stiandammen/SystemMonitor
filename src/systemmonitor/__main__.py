
"""
System Monitor - Main Entry Point
Responsive, professional enterprise-grade performance monitoring
"""
import os
import sys
import argparse
import traceback

# Handle PyInstaller packaged app paths
if getattr(sys, 'frozen', False):
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.argv[0])))
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

# Ensure src/ is at the front of sys.path so systemmonitor.* imports work
parent_dir = os.path.abspath(os.path.join(bundle_dir, os.pardir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Remove the package directory itself (src/systemmonitor/) from sys.path — Python adds it
# automatically when running __main__.py directly, which causes typing.py and enum.py
# inside the package to shadow the stdlib modules of the same name.
while bundle_dir in sys.path:
    sys.path.remove(bundle_dir)

# Setup logging
from systemmonitor.utils.logger import get_logger, LogCategory, log_info, log_error, log_warning, log_exception

_log = get_logger()


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='System Monitor')
    parser.add_argument('--overlay', action='store_true', help='Start in overlay/widget mode')
    parser.add_argument('--compact', action='store_true', help='Force compact mode')
    parser.add_argument('--expanded', action='store_true', help='Force expanded mode')
    args, unknown = parser.parse_known_args()

    log_info(LogCategory.APP, "=== SystemMonitor Starting ===")
    log_info(LogCategory.APP, f"Python: {sys.version}")
    log_info(LogCategory.APP, f"Frozen: {getattr(sys, 'frozen', False)}")
    log_info(LogCategory.APP, f"Bundle dir: {bundle_dir}")

    # Headless stubs — defined first so Pylance sees one consistent type per name.
    # The real PyQt6 classes are imported below and replace these when available.
    class QApplication:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs): pass
        def exec(self): return 0
        def setApplicationName(self, n): pass
        def setApplicationVersion(self, v): pass
        def setFont(self, f): pass
        @staticmethod
        def setHighDpiScaleFactorRoundingPolicy(p): pass

    class QMessageBox:  # type: ignore[no-redef]
        pass

    class Qt:  # type: ignore[no-redef]
        class HighDpiScaleFactorRoundingPolicy:
            PassThrough = None

    headless = False
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox  # type: ignore[no-redef]
        from PyQt6.QtCore import Qt  # type: ignore[no-redef]
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        log_info(LogCategory.APP, "PyQt6 imported OK")
    except ModuleNotFoundError as e:
        log_warning(LogCategory.APP, f"PyQt6 not installed; running in headless mode: {e}")
        headless = True
    except Exception as e:
        log_error(LogCategory.APP, f"Failed to import PyQt6: {e}\n{traceback.format_exc()}")
        return 1

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("SystemMonitor")
        app.setApplicationVersion("2.0")

        if headless:
            class QFont:
                def __init__(self, *args, **kwargs):
                    pass
            default_font = QFont()
            app.setFont(default_font)
        else:
            from PyQt6.QtGui import QFont  # type: ignore[no-redef]
            default_font = QFont("Segoe UI", 10)
            default_font.setStyleHint(QFont.StyleHint.SansSerif)
            app.setFont(default_font)
        log_info(LogCategory.APP, "QApplication created OK")
        if headless:
            log_info(LogCategory.APP, "Running in headless mode, exiting.")
            return 0
    except Exception as e:
        log_error(LogCategory.APP, f"Failed to create QApplication: {e}\n{traceback.format_exc()}")
        return 1

    try:
        from systemmonitor.scaler import init_scaler, S, LayoutMode
        init_scaler(app)

        # Apply saved UI scale preference
        from systemmonitor.config import settings as app_settings
        saved_scale = app_settings.get('ui_scale', 1.0)
        if saved_scale and float(saved_scale) != 1.0:
            S.set_user_scale(float(saved_scale))

        # Apply mode overrides from command line
        if args.compact:
            S.layout_mode = LayoutMode.COMPACT
        elif args.expanded:
            S.layout_mode = LayoutMode.EXPANDED

        log_info(LogCategory.APP, f"Scaler initialized: {S.info()}")
    except Exception as e:
        log_error(LogCategory.APP, f"Failed to init scaler: {e}")

    try:
        from systemmonitor.core.window import MainWindow
        from systemmonitor.styles.theme import theme_manager
        from systemmonitor.config import settings as app_settings
        log_info(LogCategory.APP, "core modules imported OK")

        # Apply saved theme (or fall back to cyber-cyan) before building the window
        saved_theme = app_settings.get('theme', 'cyber-cyan')
        theme_manager.set_theme(saved_theme)
        app.setStyleSheet(theme_manager.get_stylesheet())
        log_info(LogCategory.APP, "Theme applied OK")

        # System tray for alert notifications (cross-platform via Qt)
        from PyQt6.QtWidgets import QSystemTrayIcon
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
        from PyQt6.QtCore import QSize, Qt as _Qt

        def _build_tray_icon():
            px = QPixmap(QSize(16, 16))
            px.fill(QColor(0, 0, 0, 0))
            p = QPainter(px)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setBrush(QColor(16, 185, 129))
            p.setPen(_Qt.PenStyle.NoPen)
            p.drawEllipse(1, 1, 14, 14)
            p.end()
            return QIcon(px)

        tray = QSystemTrayIcon()  # type: ignore[call-overload]
        tray.setIcon(_build_tray_icon())
        tray.setToolTip("System Monitor")
        if QSystemTrayIcon.isSystemTrayAvailable():
            tray.show()
            log_info(LogCategory.APP, "System tray initialized")

        from systemmonitor.core.signals import signal_bus as _signal_bus

        def _show_alert(alert_dict):
            if not tray.isVisible():
                return
            level = alert_dict.get('level', 'warning')
            icon_type = (QSystemTrayIcon.MessageIcon.Critical
                         if level in ('critical', 'CRITICAL')
                         else QSystemTrayIcon.MessageIcon.Warning)
            tray.showMessage(
                "System Monitor",
                alert_dict.get('message', 'System threshold exceeded'),
                icon_type,
                6000,
            )

        _signal_bus.alert_triggered.connect(_show_alert)

        if args.overlay:
            # Start in overlay/widget mode
            from systemmonitor.widgets.responsive import OverlayWidget
            overlay = OverlayWidget()
            overlay.show()

            # Start data collector
            from systemmonitor.data.coordinator import DataCollector
            collector = DataCollector()
            collector.start()
            collector.data_ready.connect(overlay.update_data)
            log_info(LogCategory.APP, "Overlay mode started")

            result = app.exec()
            collector.stop()
            return result
        else:
            window = MainWindow()
            window.show()
            log_info(LogCategory.APP, "MainWindow shown OK")

            # Use the coordinator-based collector for better performance
            from systemmonitor.data.coordinator import DataCollector
            collector = DataCollector()
            collector.start()
            log_info(LogCategory.APP, "DataCollector started OK")

            # Connect signals with debouncing
            collector.data_ready.connect(window.update_data)
            log_info(LogCategory.APP, "Signals connected OK")

            log_info(LogCategory.APP, "Entering main loop")
            from PyQt6.QtWidgets import QWidget
            log_info(LogCategory.APP, f"Window visible: {window.isVisible()}, widgets count: {len(window.findChildren(QWidget))}")
            log_info(LogCategory.APP, "About to enter Qt event loop")
            try:
                result = app.exec()
                log_info(LogCategory.APP, f"App exited with code: {result}")
            except Exception as e:
                log_error(LogCategory.APP, f"app.exec exception: {e}\n{traceback.format_exc()}")
                result = 1
            collector.stop()
            return result
    except Exception as e:
        log_error(LogCategory.APP, f"Application error: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


