#!/usr/bin/env python3
import sys
import pathlib
import traceback

# Add src to sys.path and invoke systemmonitor.__main__
src_path = pathlib.Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))


def _show_fatal_error(text: str) -> None:
    """Last-resort error display that works even if PyQt6/logging failed.
    PyInstaller's own windowed-mode traceback dialog (disable_windowed_traceback=False)
    should normally catch unhandled exceptions here, but this is a second,
    independent safety net in case that mechanism doesn't fire (e.g. a crash
    inside a native DLL before Python fully initializes) - the goal is that
    the app can NEVER fail completely silently with no window and no error.
    """
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, "System Monitor - Error", 0x10)
    except Exception:
        try:
            log_path = pathlib.Path(sys.executable).parent / "SystemMonitor-startup-error.log"
            log_path.write_text(text, encoding="utf-8")
        except Exception:
            pass


if __name__ == '__main__':
    try:
        from systemmonitor.__main__ import main  # type: ignore
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        _show_fatal_error(
            "System Monitor failed to start:\n\n" + traceback.format_exc()
        )
        sys.exit(1)
