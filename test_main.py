"""
Test app - MainWindow plus signal connection to a dummy slot
"""
import sys
import os

if getattr(sys, 'frozen', False):
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, bundle_dir)

print(f"[Test] Starting...", flush=True)

from PyQt5.QtWidgets import QApplication
from core.window import MainWindow
from core.theme import ThemeManager
print(f"[Test] Imports done", flush=True)

app = QApplication(sys.argv)
theme_manager = ThemeManager()
app.setStyleSheet(theme_manager.get_stylesheet())

window = MainWindow()
window.show()
print(f"[Test] Window shown", flush=True)

# Create a simple signal and connect it to window.update_data
from PyQt5.QtCore import QTimer

# Wrapper to provide empty dict (actual app uses DataCollector which provides data)
def emit_update():
    window.update_data({})

timer = QTimer()
timer.timeout.connect(emit_update)
timer.start(1000)  # Emit every second with empty data
print(f"[Test] Timer connected to window.update_data", flush=True)

print(f"[Test] Entering exec_", flush=True)
sys.stdout.flush()

result = app.exec_()
print(f"[Test] Exited with code: {result}", flush=True)