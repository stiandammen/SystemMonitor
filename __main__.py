"""
System Monitor - Main Entry Point
"""
import os
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
import sys

import traceback

# Handle PyInstaller packaged app paths
if getattr(sys, 'frozen', False):
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, bundle_dir)

# Setup logging for packaged app
LOG_FILE = None
if getattr(sys, 'frozen', False):
    log_dir = os.path.join(os.environ.get('TEMP', ''), 'SystemMonitor')
    os.makedirs(log_dir, exist_ok=True)
    LOG_FILE = os.path.join(log_dir, 'error.log')

def log_error(msg):
    """Log error to file"""
    print(f"[SystemMonitor] {msg}", flush=True)
    if LOG_FILE:
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                import datetime
                f.write(f"[{datetime.datetime.now()}] {msg}\n")
                f.flush()
        except:
            pass

def main():
    """Main application entry point"""
    log_error("=== SystemMonitor Starting ===")
    log_error(f"Python: {sys.version}")
    log_error(f"Frozen: {getattr(sys, 'frozen', False)}")
    log_error(f"Bundle dir: {bundle_dir}")

    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        log_error("PyQt6 imported OK")
    except Exception as e:
        log_error(f"Failed to import PyQt6: {e}\n{traceback.format_exc()}")
        return 1

    try:
        app = QApplication(sys.argv)
        log_error("QApplication created OK")
    except Exception as e:
        log_error(f"Failed to create QApplication: {e}\n{traceback.format_exc()}")
        return 1

    try:
        from scaler import init_scaler, S
        init_scaler(app)
        log_error("Scaler initialized OK")
    except Exception as e:
        log_error(f"Failed to init scaler: {e}")

    try:
        from core.window import MainWindow
        from core.theme import ThemeManager
        log_error("core modules imported OK")

        theme_manager = ThemeManager()
        app.setStyleSheet(theme_manager.get_stylesheet())
        log_error("Theme applied OK")

        window = MainWindow()
        window.show()
        log_error("MainWindow shown OK")

        from data.collector import DataCollector
        collector = DataCollector()
        collector.start()
        log_error("DataCollector started OK")

        collector.data_ready.connect(window.update_data)
        log_error("Signals connected OK")

        from views.overview_page import OverviewPage
        from views.cpu import CPUView
        if isinstance(window._views["overview"], OverviewPage):
            window._views["overview"].set_data_collector(collector)
        if isinstance(window._views["cpu"], CPUView):
            window._views["cpu"].set_data_collector(collector)
        log_error("Views connected OK")

        log_error("Entering main loop")
        from PyQt6.QtWidgets import QWidget
        log_error(f"Window visible: {window.isVisible()}, widgets count: {len(window.findChildren(QWidget))}")
        log_error(f"About to enter Qt event loop")
        try:
            result = app.exec()
            log_error(f"App exited with code: {result}")
        except Exception as e:
            log_error(f"app.exec_ exception: {e}\n{traceback.format_exc()}")
            result = 1
        collector.stop()
        return result
    except Exception as e:
        log_error(f"Application error: {e}\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())