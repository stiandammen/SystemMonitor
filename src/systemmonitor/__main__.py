
"""
System Monitor - Main Entry Point
Responsive, professional enterprise-grade performance monitoring
"""
import os
import sys
import argparse
import traceback

# Monkey-patch subprocess.Popen on Windows to hide black console windows globally
if sys.platform == 'win32':
    import subprocess
    _orig_Popen = subprocess.Popen
    def _patched_Popen(*args, **kwargs):
        # 0x08000000 is CREATE_NO_WINDOW
        flags = kwargs.get('creationflags', 0)
        # Skip if it is a detached process (like the installer)
        if not (flags & (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)):
            kwargs['creationflags'] = flags | 0x08000000
        return _orig_Popen(*args, **kwargs)
    subprocess.Popen = _patched_Popen

# Single Instance Lock on Windows to prevent multiple tray icons and background instances
if sys.platform == 'win32':
    try:
        import win32event
        import win32api
        import winerror
        
        mutex_name = "Local\\SystemMonitor_SingleInstance_Mutex"
        # We must keep a reference to the handle so it doesn't get garbage collected
        _single_instance_mutex = win32event.CreateMutex(None, True, mutex_name)
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            # Another instance is already running, exit silently
            sys.exit(0)
    except Exception:
        pass

# Handle PyInstaller packaged app paths
if getattr(sys, 'frozen', False):
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.argv[0])))
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

    # Ensure src/ is at the front of sys.path so systemmonitor.* imports work
    parent_dir = os.path.abspath(os.path.join(bundle_dir, os.pardir))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)


def _show_fatal_startup_error(text: str) -> None:
    """Last-resort error display for failures that happen before logging
    itself is available. Uses ctypes directly (no PyQt6/logging dependency)
    so the app can never fail with literally no visible window and no error,
    which is otherwise indistinguishable from a working-but-silent process.
    """
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, "System Monitor - Error", 0x10)
    except Exception:
        pass


# Setup logging - guarded because this runs at import time, before main()'s
# own try/except blocks exist. A failure here (e.g. the log/i18n directories
# not being writable at the installed location) would otherwise propagate as
# a bare, unhandled exception with nothing to catch or report it.
try:
    from systemmonitor.utils.logger import get_logger, LogCategory, log_info, log_error, log_warning, log_exception
    from systemmonitor.i18n import tr, language_manager

    _log = get_logger()
except Exception:
    import traceback as _tb
    _show_fatal_startup_error(
        "System Monitor failed to initialize logging/translations:\n\n" + _tb.format_exc()
    )
    sys.exit(1)


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

    # Splash screen — shown immediately since PyQt6/psutil/WMI take a moment to
    # Splash screen — shown immediately since PyQt6/psutil/WMI take a moment to
    # import and the main window has heavy widgets to build on first show.
    splash = None
    try:
        from PyQt6.QtWidgets import QSplashScreen
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont as _SplashFont, QPen, QLinearGradient, QBrush, QPainterPath
        from PyQt6.QtCore import Qt as _SplashQt, QRectF
        import math
        import time

        class AnimatedSplashScreen(QSplashScreen):
            def __init__(self):
                # Create a blank transparent pixmap of the size we want the splash screen to be
                pix = QPixmap(460, 280)
                pix.fill(QColor(0, 0, 0, 0))  # Start fully transparent
                super().__init__(pix)
                
                # Make splash screen frameless and translucent
                self.setWindowFlags(self.windowFlags() | _SplashQt.WindowType.FramelessWindowHint)
                self.setAttribute(_SplashQt.WidgetAttribute.WA_TranslucentBackground, True)
                
                self.angle = 0
                self.loading_text = tr("Loading monitoring engine")
                
            def rotate(self):
                # We rotate by 4 degrees for an ultra-smooth motion
                self.angle = (self.angle + 4) % 360
                self.update()  # Repaint
                
            def set_loading_text(self, text):
                # Remove trailing dots if any, we format it as terminal output
                clean_text = text.replace('…', '').replace('...', '').strip()
                self.loading_text = clean_text
                self.update()
                
            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                # 1. Glassmorphic Background with Rounded Corners
                path = QPainterPath()
                path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 16, 16)
                
                # Draw background gradient inside path (semi-translucent dark cyberpunk theme)
                grad = QLinearGradient(0, 0, self.width(), self.height())
                grad.setColorAt(0.0, QColor(10, 13, 20, 248))  # Deep dark space blue
                grad.setColorAt(1.0, QColor(21, 27, 38, 248))  # Tech slate
                painter.fillPath(path, QBrush(grad))
                
                # 2. Glowing Neon Border
                border_grad = QLinearGradient(0, 0, self.width(), self.height())
                border_grad.setColorAt(0.0, QColor(6, 182, 212))   # Cyan
                border_grad.setColorAt(0.5, QColor(99, 102, 241))  # Indigo
                border_grad.setColorAt(1.0, QColor(16, 185, 129))  # Emerald
                
                border_pen = QPen(border_grad, 1.5)
                painter.setPen(border_pen)
                painter.setBrush(_SplashQt.BrushStyle.NoBrush)
                painter.drawPath(path)
                
                # 3. Dynamic Title with Gradient Text & Breathing Glow
                rad = self.angle * math.pi / 180
                alpha = int(170 + 85 * math.sin(rad * 2))  # pulses twice per rotation
                alpha = max(80, min(255, alpha))
                
                title_grad = QLinearGradient(0, 35, 0, 75)
                title_grad.setColorAt(0.0, QColor(0, 242, 254, alpha))  # Bright cyan
                title_grad.setColorAt(1.0, QColor(79, 172, 254, alpha)) # Deep sky blue
                
                painter.setPen(QPen(title_grad, 1))
                font_title = _SplashFont("Segoe UI", 26, _SplashFont.Weight.Black)
                painter.setFont(font_title)
                painter.drawText(self.rect().adjusted(0, 35, 0, 0),
                                 _SplashQt.AlignmentFlag.AlignHCenter | _SplashQt.AlignmentFlag.AlignTop,
                                 "SYSTEM MONITOR")
                                 
                # Subtitle (Small uppercase tracked out tech text)
                painter.setPen(QColor(148, 163, 184, int(alpha * 0.7)))
                font_sub = _SplashFont("Segoe UI", 7, _SplashFont.Weight.Bold)
                painter.setFont(font_sub)
                painter.drawText(self.rect().adjusted(0, 75, 0, 0),
                                 _SplashQt.AlignmentFlag.AlignHCenter | _SplashQt.AlignmentFlag.AlignTop,
                                 "E N T E R P R I S E   H A R D W A R E   S U I T E")
                                 
                # 4. Concentric HUD Loader Spinner
                cx = self.width() / 2
                cy = self.height() / 2 + 15
                
                # Outer dashed HUD track (slow rotation counter-clockwise)
                r1 = 28
                dashed_pen = QPen(QColor(148, 163, 184, 40), 1.5)
                dashed_pen.setStyle(_SplashQt.PenStyle.DashLine)
                painter.setPen(dashed_pen)
                painter.drawEllipse(int(cx - r1), int(cy - r1), r1 * 2, r1 * 2)
                
                # Middle Cyan Active Arc (rotates clockwise)
                r2 = 23
                pen_spinner1 = QPen(QColor(6, 182, 212), 3.5)
                pen_spinner1.setCapStyle(_SplashQt.PenCapStyle.RoundCap)
                painter.setPen(pen_spinner1)
                painter.drawArc(int(cx - r2), int(cy - r2), r2 * 2, r2 * 2, -self.angle * 16, 120 * 16)
                
                # Inner Emerald Arc (rotates counter-clockwise faster)
                r3 = 15
                pen_spinner2 = QPen(QColor(16, 185, 129), 2)
                pen_spinner2.setCapStyle(_SplashQt.PenCapStyle.RoundCap)
                painter.setPen(pen_spinner2)
                inner_angle = int(self.angle * 1.6) % 360
                painter.drawArc(int(cx - r3), int(cy - r3), r3 * 2, r3 * 2, inner_angle * 16, 90 * 16)
                
                # Center Glowing Pulse core
                pulse_r = 4.0 + 1.5 * math.sin(rad * 3)
                core_color = QColor(6, 182, 212, int(150 + 105 * math.sin(rad * 3)))
                painter.setPen(_SplashQt.PenStyle.NoPen)
                painter.setBrush(QBrush(core_color))
                painter.drawEllipse(QRectF(cx - pulse_r, cy - pulse_r, pulse_r * 2, pulse_r * 2))
                
                # 5. Technical Terminal-Style Loading status log
                painter.setPen(QColor(165, 243, 252)) # Light cyan
                font_text = _SplashFont("Consolas", 9)  # Code terminal font
                painter.setFont(font_text)
                
                # Format text: e.g. ":: LOADING CORE ENGINE..."
                formatted_text = f":: {self.loading_text.upper()}..."
                painter.drawText(self.rect().adjusted(0, 0, 0, 30),
                                 _SplashQt.AlignmentFlag.AlignHCenter | _SplashQt.AlignmentFlag.AlignBottom,
                                 formatted_text)
                                 
                painter.end()

        splash = AnimatedSplashScreen()
        splash.show()
        
        def animate_phase(duration_ms, text):
            if splash:
                splash.set_loading_text(text)
            steps = int(duration_ms / 16)
            for _ in range(steps):
                if splash:
                    splash.rotate()
                app.processEvents()
                time.sleep(0.016)

        # Initial transition phase (400ms)
        animate_phase(400, tr("Starting System Monitor…"))
            
        log_info(LogCategory.APP, "Animated splash screen shown")
    except Exception as e:
        log_warning(LogCategory.APP, f"Failed to show splash screen: {e}")
        splash = None

    try:
        if splash:
            animate_phase(500, tr("Initializing resolution scaler…"))

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
        if splash:
            animate_phase(600, tr("Loading core window modules…"))

        from systemmonitor.core.window import MainWindow
        from systemmonitor.styles.theme import theme_manager
        from systemmonitor.config import settings as app_settings
        log_info(LogCategory.APP, "core modules imported OK")

        # Apply saved theme (or fall back to cyber-cyan) before building the window
        saved_theme = app_settings.get('theme', 'cyber-cyan')
        theme_manager.set_theme(saved_theme)
        app.setStyleSheet(theme_manager.get_stylesheet())
        log_info(LogCategory.APP, "Theme applied OK")

        # Filled in once the MainWindow exists (not available in overlay mode),
        # so the tray menu and in-app toast can reach it.
        _main_window_ref: list = [None]

        # System tray: alert notifications + minimize-to-tray controls (cross-platform via Qt)
        from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
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

        def _restore_main_window():
            win = _main_window_ref[0]
            if win is not None:
                win.showNormal()
                win.activateWindow()
                win.raise_()

        def _toggle_main_window():
            win = _main_window_ref[0]
            if win is None:
                return
            if win.isVisible():
                win.hide()
            else:
                _restore_main_window()

        def _on_tray_activated(reason):
            if reason == QSystemTrayIcon.ActivationReason.Trigger:
                _toggle_main_window()

        tray = QSystemTrayIcon()  # type: ignore[call-overload]
        tray.setIcon(_build_tray_icon())
        tray.setToolTip("System Monitor")

        _tray_menu = QMenu()
        _show_action = _tray_menu.addAction(tr("Show System Monitor"), _restore_main_window)
        _tray_menu.addSeparator()
        _quit_action = _tray_menu.addAction(tr("Quit"), app.quit)
        tray.setContextMenu(_tray_menu)
        tray.activated.connect(_on_tray_activated)

        def _retranslate_tray_menu(_language: str):
            _show_action.setText(tr("Show System Monitor"))
            _quit_action.setText(tr("Quit"))

        language_manager.language_changed.connect(_retranslate_tray_menu)

        if QSystemTrayIcon.isSystemTrayAvailable():
            tray.show()
            log_info(LogCategory.APP, "System tray initialized")

        from systemmonitor.core.signals import signal_bus as _signal_bus

        def _show_alert(alert_dict):
            level = alert_dict.get('level', 'warning')
            message = alert_dict.get('message', tr('System threshold exceeded'))
            method = app_settings.get('notification_method', 'system')

            if method == 'in_app' and _main_window_ref[0] is not None:
                _main_window_ref[0].show_alert_toast(message, level)
                return

            if not tray.isVisible():
                return
            icon_type = (QSystemTrayIcon.MessageIcon.Critical
                         if level in ('critical', 'CRITICAL')
                         else QSystemTrayIcon.MessageIcon.Warning)
            tray.showMessage("System Monitor", message, icon_type, 6000)

        _signal_bus.alert_triggered.connect(_show_alert)

        if args.overlay:
            # Start in overlay/widget mode
            from systemmonitor.widgets.responsive import OverlayWidget
            overlay = OverlayWidget()
            overlay.show()
            if splash is not None:
                splash.finish(overlay)

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
            if splash:
                animate_phase(600, tr("Building user interface widgets…"))

            window = MainWindow()
            _main_window_ref[0] = window

            start_minimized = (app_settings.get('start_minimized', False)
                               and QSystemTrayIcon.isSystemTrayAvailable())
            if start_minimized:
                log_info(LogCategory.APP, "MainWindow created hidden (start minimized to tray)")
            else:
                window.show()
                log_info(LogCategory.APP, "MainWindow shown OK")

            if splash is not None:
                if start_minimized:
                    splash.close()
                else:
                    splash.finish(window)

            if splash:
                animate_phase(600, tr("Starting background monitoring threads…"))

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


