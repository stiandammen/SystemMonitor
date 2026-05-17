"""
System Monitor - Main Entry Point
Responsive, professional enterprise-grade performance monitoring
"""
import os
os.environ["QT_ENABLE_HIGH_DPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"
import sys
import argparse
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
    parser = argparse.ArgumentParser(description='System Monitor')
    parser.add_argument('--overlay', action='store_true', help='Start in overlay/widget mode')
    parser.add_argument('--compact', action='store_true', help='Force compact mode')
    parser.add_argument('--expanded', action='store_true', help='Force expanded mode')
    args, unknown = parser.parse_known_args()

    log_info(LogCategory.APP, "=== SystemMonitor Starting ===")
    log_info(LogCategory.APP, f"Python: {sys.version}")
    log_info(LogCategory.APP, f"Frozen: {getattr(sys, 'frozen', False)}")
    log_info(LogCategory.APP, f"Bundle dir: {bundle_dir}")
    log_info(LogCategory.APP, f"Overlay mode: {args.overlay}")
    log_info(LogCategory.APP, f"Compact mode: {args.compact}")

    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        log_info(LogCategory.APP, "PyQt6 imported OK")
    except Exception as e:
        log_error(LogCategory.APP, f"Failed to import PyQt6: {e}\n{traceback.format_exc()}")
        return 1

    try:
        # Enable High DPI scaling before QApplication
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        app = QApplication(sys.argv)
        app.setApplicationName("SystemMonitor")
        app.setApplicationVersion("2.0")

        # Set font for consistent rendering across DPIs
        from PyQt6.QtGui import QFont
        default_font = QFont("Segoe UI", 10)
        default_font.setStyleHint(QFont.StyleHint.SansSerif)
        app.setFont(default_font)

        log_info(LogCategory.APP, "QApplication created OK")
    except Exception as e:
        log_error(LogCategory.APP, f"Failed to create QApplication: {e}\n{traceback.format_exc()}")
        return 1

    try:
        from scaler import init_scaler, S, LayoutMode
        init_scaler(app)

        # Apply mode overrides from command line
        if args.compact:
            S.layout_mode = LayoutMode.COMPACT
        elif args.expanded:
            S.layout_mode = LayoutMode.EXPANDED

        log_info(LogCategory.APP, f"Scaler initialized: {S.info()}")
    except Exception as e:
        log_error(LogCategory.APP, f"Failed to init scaler: {e}")

    try:
        from core.window import MainWindow
        from core.theme import ThemeManager
        log_info(LogCategory.APP, "core modules imported OK")

        theme_manager = ThemeManager()
        app.setStyleSheet(theme_manager.get_stylesheet())
        log_info(LogCategory.APP, "Theme applied OK")

        if args.overlay:
            # Start in overlay/widget mode
            from widgets.responsive import OverlayWidget
            overlay = OverlayWidget()
            overlay.show()

            # Start data collector
            from data.coordinator import DataCollector
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
            from data.coordinator import DataCollector
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