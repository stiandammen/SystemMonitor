import PyInstaller.__main__
import os
import sys

# Define paths
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, "src")
# Use the root __main__.py instead of the one inside the package
main_script = os.path.join(base_dir, "__main__.py")
assets_dir = os.path.join(src_dir, "systemmonitor", "assets")
icon_path = os.path.join(assets_dir, "hacker.png")

# PyInstaller arguments
args = [
    main_script,
    '--onefile',
    '--windowed',
    '--noconfirm',
    '--clean',
    '--name=SystemMonitor',
    # Ensure PyInstaller looks in src/ to find the systemmonitor package
    f'--paths={src_dir}',
    # Add assets folder. Format: "source;destination"
    f'--add-data={assets_dir}{os.pathsep}systemmonitor/assets',
    # Request administrator privileges for hardware sensors
    '--uac-admin',
    # Set the icon
    f'--icon={icon_path}',
    # ULTRA-EXPLICIT imports to bypass any remaining shadowing issues
    '--hidden-import=csv',
    '--hidden-import=json',
    '--hidden-import=datetime',
    '--hidden-import=pathlib',
    '--hidden-import=enum',
    '--hidden-import=typing',
    '--hidden-import=pkg_resources.extern',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtWidgets',
    '--hidden-import=psutil',
    '--hidden-import=wmi',
    '--hidden-import=GPUtil',
    '--hidden-import=qtawesome',
    # Force include collect-all for systemmonitor to be absolutely sure
    '--collect-all=systemmonitor',
]

print(f"Starting build with command: pyinstaller {' '.join(args)}")

try:
    PyInstaller.__main__.run(args)
    print("\nBuild completed successfully! Check the 'dist' folder.")
except Exception as e:
    print(f"\nBuild failed: {e}")
    sys.exit(1)
