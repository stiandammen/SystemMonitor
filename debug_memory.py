"""Test with timer that catches errors"""
import sys
sys.path.insert(0, '.')

from PyQt5.QtWidgets import QApplication
from core.window import MainWindow
from core.theme import ThemeManager
from PyQt5.QtCore import QTimer
import time
import traceback

log_file = open('test_log.txt', 'w')
def log(msg):
    log_file.write(f'{msg}\n')
    log_file.flush()
    print(msg, flush=True)

log('Starting...')

app = QApplication([])
theme_manager = ThemeManager()
app.setStyleSheet(theme_manager.get_stylesheet())

window = MainWindow()
window.show()
log('Window shown')

# Safe timer callback
count = [0]
def safe_update():
    count[0] += 1
    log(f'Timer callback #{count[0]}')
    try:
        window.update_data({})
        log(f'Timer callback #{count[0]} done')
    except Exception as e:
        log(f'Timer error: {e}')
        traceback.print_exc()

timer = QTimer()
timer.timeout.connect(safe_update)
timer.start(1000)
log('Timer started')

# Run event loop
for i in range(50):
    app.processEvents()
    time.sleep(0.1)
    if i % 10 == 0:
        log(f'Second {i//10 + 1}')

log('SUCCESS')
log_file.close()