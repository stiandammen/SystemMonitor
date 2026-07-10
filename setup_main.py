#!/usr/bin/env python3
"""
Entry point for the standalone "System Monitor Setup.exe" installer/uninstaller.
Built separately from the main app via SystemMonitorSetup.spec - see that file
for how this gets bundled together with a copy of SystemMonitor.exe.
"""
import sys
import pathlib

# Add src to sys.path, same pattern as the main __main__.py entry point
src_path = pathlib.Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

if __name__ == '__main__':
    from systemmonitor.utils.setup_installer import main  # type: ignore
    main()
