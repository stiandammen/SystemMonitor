"""Memory View Debug Test - Capture all output with signal spy"""
import sys
import os

# Create a log file
log_path = os.path.join(os.environ.get('TEMP', '.'), 'memory_debug.log')
log = open(log_path, 'w')

def log_msg(msg):
    log.write(f"{msg}\n")
    log.flush()
    print(msg, flush=True)

log_msg('Starting debug...')

sys.path.insert(0, '.')

from PyQt6.QtWidgets import QApplication
from core.window import MainWindow
from core.theme import ThemeManager
from PyQt6.QtCore import QTimer
import time
import traceback

app = QApplication([])
theme_manager = ThemeManager()
app.setStyleSheet(theme_manager.get_stylesheet())

window = MainWindow()
window.show()
log_msg('Window shown')

# Switch to memory view
window._switch_view('memory')
log_msg('Switched to memory')

# Install our own timer that catches ALL errors
class SafeTimer(QTimer):
    def __init__(self):
        super().__init__()
        self.count = 0

    def timeout(self):
        self.count += 1
        try:
            if self.count == 1:
                log_msg(f'Timer callback #{self.count}')
            window.update_data({})
            if self.count <= 3:
                log_msg(f'Update # {self.count} OK')
        except Exception as e:
            log_msg(f'ERROR in timer callback: {e}')
            traceback.print_exc()

timer = SafeTimer()
timer.timeout.connect(timer.timeout)
timer.start(1000)
log_msg('SafeTimer started')

# Process events with extensive error handling
log_msg('Starting event loop...')
try:
    for i in range(10):
        app.processEvents()
        time.sleep(0.1)
        if i == 0:
            log_msg('First iteration done')
except Exception as e:
    log_msg(f'ERROR in event loop: {e}')
    traceback.print_exc()

log_msg('Event loop done')
log.close()