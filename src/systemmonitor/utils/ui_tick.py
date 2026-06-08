"""
Central UI tick - a single shared QTimer that emits a periodic signal so
throttled widgets (sparklines, per-core graphs, ...) can repaint at ~30fps
without each owning its own private QTimer instance.
"""
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class _UiTick(QObject):
    """Emits `tick` on a fixed interval. Widgets connect and repaint on demand."""

    tick = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30fps, matches the previous per-widget throttle
        self._timer.timeout.connect(self.tick)
        self._timer.start()


ui_tick = _UiTick()
