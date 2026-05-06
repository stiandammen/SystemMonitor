"""
System Monitor - Main Entry Point
Optimized for professional technician-grade performance
"""
import os
os.environ["QT_ENABLE_HIGH_DPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
import sys

import traceback

# Handle PyInstaller packaged app paths
if getattr(sys, 'frozen', False):
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, bundle_dir)

# Setup logging
from utils.logger import get_logger, LogCategory, log_info, log_error, log_exception

_log = get_logger()


def main():
    """Main application entry point"""
    log_info(LogCategory.APP, "=== SystemMonitor Starting ===")
    log_info(LogCategory.APP, f"Python: {sys.version}")
    log_info(LogCategory.APP, f"Frozen: {getattr(sys, 'frozen', False)}")
    log_info(LogCategory.APP, f"Bundle dir: {bundle_dir}")

    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        log_info(LogCategory.APP, "PyQt6 imported OK")
    except Exception as e:
        log_error(LogCategory.APP, f"Failed to import PyQt6: {e}\n{traceback.format_exc()}")
        return 1

    try:
        # Enable High DPI scaling before QApplication
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

        app = QApplication(sys.argv)
        app.setApplicationName("SystemMonitor")
        app.setApplicationVersion("1.0")
        log_info(LogCategory.APP, "QApplication created OK")
    except Exception as e:
        log_error(LogCategory.APP, f"Failed to create QApplication: {e}\n{traceback.format_exc()}")
        return 1

    try:
        from scaler import init_scaler, S
        init_scaler(app)
        log_info(LogCategory.APP, "Scaler initialized OK")
    except Exception as e:
        log_error(LogCategory.APP, f"Failed to init scaler: {e}")

    try:
        from core.window import MainWindow
        from core.theme import ThemeManager
        log_info(LogCategory.APP, "core modules imported OK")

        theme_manager = ThemeManager()
        app.setStyleSheet(theme_manager.get_stylesheet())
        log_info(LogCategory.APP, "Theme applied OK")

        window = MainWindow()
        window.show()
        log_info(LogCategory.APP, "MainWindow shown OK")

        # Use the new coordinator-based collector for better performance
        from data.coordinator import DataCollector
        collector = DataCollector()
        collector.start()
        log_info(LogCategory.APP, "DataCollector started OK")

        # Connect signals with debouncing
        collector.data_ready.connect(window.update_data)
        log_info(LogCategory.APP, "Signals connected OK")

        # Lazy connect data collector to views as they become active
        # The window handles this via lazy loading now
        log_info(LogCategory.APP, "Views use lazy loading - connected on demand")

        log_info(LogCategory.APP, "Entering main loop")
        from PyQt6.QtWidgets import QWidget
        log_info(LogCategory.APP, f"Window visible: {window.isVisible()}, widgets count: {len(window.findChildren(QWidget))}")
        log_info(LogCategory.APP, "About to enter Qt event loop")
        try:
            result = app.exec()
            log_info(LogCategory.APP, f"App exited with code: {result}")
        except Exception as e:
            log_error(LogCategory.APP, f"app.exec_ exception: {e}\n{traceback.format_exc()}")
            result = 1
        collector.stop()
        return result
    except Exception as e:
        log_error(LogCategory.APP, f"Application error: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())