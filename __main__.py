#!/usr/bin/env python3
import sys, pathlib
# Add src to sys.path and invoke systemmonitor.__main__
src_path = pathlib.Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))
if __name__ == '__main__':
    from systemmonitor.__main__ import main  # type: ignore
    sys.exit(main())
