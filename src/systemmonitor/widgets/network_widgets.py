"""
Reusable widget components for the Network view dashboard:
sparklines, KPI cards, traffic graph, protocol donut, connections table,
interface rows and the topology radar.
"""
import math
from collections import deque

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QLinearGradient,
    QPainterPath, QRadialGradient
)
import qtawesome as qta

from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, I18nMixin
from systemmonitor.scaler import S, ScaleMixin
from typing import Dict, List


def _qcolor(color_str: str) -> QColor:
    """Parse hex or CSS rgba(...) string into QColor"""
    s = color_str.strip()
    if s.startswith("rgba("):
        try:
            parts = s[5:-1].split(",")
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            a = float(parts[3].strip())
            c = QColor(r, g, b)
            c.setAlphaF(a)
            return c
        except Exception:
            pass
    return QColor(s)


# ---------------------------------------------------------------------------
# Sparkline
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------

class ConnectionsTable(QTableWidget, I18nMixin):
    """Active TCP/UDP connections"""

    _HEADERS = ["Local IP", "Port", "Remote IP", "Port", "Proto", "State"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.i18n_connect()
        self._build()

    def retranslate_ui(self):
        self._build()

    def _build(self):
        c = theme_manager.colors
        self.setColumnCount(len(self._HEADERS))
        self.setHorizontalHeaderLabels([tr(h) for h in self._HEADERS])
        self.horizontalHeader().setFont(QFont("Cutive", S.font_pt(9), QFont.Weight.Bold))
        hh = self.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setStretchLastSection(True)
        hh.setMinimumSectionSize(S.px(48))
        self.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.setWordWrap(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumWidth(0)
        self.setFont(QFont("Cutive", S.font_pt(9)))
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {c.BG_CARD};
                color: {c.TEXT_PRIMARY};
                border: none;
                alternate-background-color: {c.BG_SECONDARY};
            }}
            QTableWidget::item {{
                padding: {S.px(6)}px {S.px(10)}px;
                color: {c.TEXT_PRIMARY};
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: {c.BG_HOVER};
                color: {c.TEXT_PRIMARY};
            }}
            QTableWidget::item:alternate {{
                background-color: {c.BG_SECONDARY};
            }}
            QHeaderView::section {{
                background-color: {c.BG_SECONDARY};
                color: {c.TEXT_SECONDARY};
                padding: {S.px(8)}px {S.px(10)}px;
                border: none;
                font-weight: bold;
            }}
            QHeaderView {{
                border: none;
            }}
        """)

    def retheme(self):
        self._build()

    def set_filter(self, text: str):
        """Case-insensitive substring filter over all columns."""
        self._filter = (text or "").strip().lower()
        self.load(getattr(self, '_rows', []))

    def load(self, rows: List[Dict]):
        self._rows = rows
        flt = getattr(self, '_filter', "")
        if flt:
            rows = [r for r in rows if flt in " ".join(str(v) for v in r.values()).lower()]
        self.setRowCount(0)
        c = theme_manager.colors
        state_colors = {
            "ESTABLISHED": c.STATUS_GREEN,
            "LISTEN": c.ACCENT_BLUE,
            "TIME_WAIT": c.ACCENT_ORANGE,
            "CLOSE_WAIT": c.ACCENT_YELLOW,
            "SYN_SENT": c.ACCENT_CYAN,
            "NONE": c.TEXT_SECONDARY,
        }
        for row in rows[:80]:
            r = self.rowCount()
            self.insertRow(r)
            values = [
                row.get("local_ip", "-"),
                str(row.get("local_port", "-")),
                row.get("remote_ip", "-"),
                str(row.get("remote_port", "-")),
                row.get("proto", "-"),
                row.get("state", "-"),
            ]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setFont(QFont("Cutive", S.font_pt(9)))
                if col == 5:  # state column — colour coded
                    color = state_colors.get(text.upper(), c.TEXT_SECONDARY)
                    item.setForeground(QColor(color))
                self.setItem(r, col, item)
