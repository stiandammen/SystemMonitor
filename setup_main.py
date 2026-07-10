#!/usr/bin/env python3
"""
Entry point for the standalone "System Monitor Setup.exe" installer/uninstaller.
Built separately from the main app via SystemMonitorSetup.spec - see that file
for how this gets bundled together with a copy of SystemMonitor.exe.

Wrapped in a bare-bones error handler (ctypes MessageBoxW, no Qt/other
dependency) so that if ANYTHING fails during startup - even before PyQt6
itself can be imported - the user sees an actual error dialog with the
real exception instead of the process silently doing nothing.
"""
import sys
import pathlib
import traceback


def _show_fatal_error(text: str) -> None:
    """Last-resort error display that works even if PyQt6 failed to import."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, "System Monitor Setup - Error", 0x10)
    except Exception:
        # If even ctypes/MessageBoxW fails, fall back to a log file next to the exe
        try:
            log_path = pathlib.Path(sys.executable).parent / "SystemMonitorSetup-error.log"
            log_path.write_text(text, encoding="utf-8")
        except Exception:
            pass


def _run() -> None:
    src_path = pathlib.Path(__file__).parent / 'src'
    sys.path.insert(0, str(src_path))
    from systemmonitor.utils.setup_installer import main  # type: ignore
    main()


if __name__ == '__main__':
    try:
        _run()
    except Exception:
        _show_fatal_error(
            "System Monitor Setup failed to start:\n\n" + traceback.format_exc()
        )
        sys.exit(1)
