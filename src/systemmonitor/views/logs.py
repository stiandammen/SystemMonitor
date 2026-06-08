"""
Log Viewer — In-app inspection of application log files
Tails the rotating log files written by SystemLogger, with category/level
filtering, text search, and optional auto-refresh.
"""
import html
import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTextEdit, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import QUrl
import qtawesome as qta

from systemmonitor.scaler import S, ScaleMixin
from systemmonitor.styles.theme import theme_manager
from systemmonitor.i18n import tr, I18nMixin
from systemmonitor.utils.logger import SystemLogger
from systemmonitor.widgets.settings_row import ToggleWidget


def _c():
    return theme_manager.colors


_LEVEL_RE = re.compile(r"\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\]")
_LEVELS = ["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
_MAX_LINES = 1000


class LogView(QWidget, ScaleMixin, I18nMixin):
    """Read-only viewer for the rotating per-category log files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = SystemLogger()
        self._current_category: str | None = None
        self._search_text = ""
        self._last_file_stat = (0, 0)  # (mtime, size)
        self._ui_built = False

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(2000)
        self._refresh_timer.timeout.connect(self._reload_log)

        self.scale_connect()
        self.i18n_connect()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self._setup_ui()

    # ── lifecycle ──────────────────────────────────────────────────────────
    def showEvent(self, event):
        super().showEvent(event)
        if self._auto_toggle.isChecked():
            self._refresh_timer.start()
        self._reload_log(force=True)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._refresh_timer.stop()

    def on_scale_changed(self, _factor: float):
        self._ui_built = False
        QTimer.singleShot(0, self._setup_ui)

    def retranslate_ui(self):
        self._ui_built = False
        QTimer.singleShot(0, self._setup_ui)

    def _on_theme_changed(self, _name: str):
        self._ui_built = False
        QTimer.singleShot(0, self._setup_ui)

    # ── UI construction ────────────────────────────────────────────────────
    def _setup_ui(self):
        if self._ui_built and self.layout():
            return

        if self.layout():
            old = self.layout()
            while old.count():
                item = old.takeAt(0)
                w = item.widget()
                if w:
                    w.hide()
                    w.setParent(None)
                    w.deleteLater()
            tmp = QWidget()
            tmp.setLayout(old)
            tmp.deleteLater()

        c = _c()
        self.setStyleSheet(f"background-color: {c.BG_PRIMARY};")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        root = QVBoxLayout()
        root.setContentsMargins(S.px(16), S.px(16), S.px(16), S.px(16))
        root.setSpacing(S.px(12))
        self.setLayout(root)

        root.addWidget(self._build_header())
        root.addWidget(self._build_toolbar())

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._text.setFont(QFont("Consolas", S.font_pt(10)))
        self._text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c.BG_SECONDARY};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: {S.px(8)}px;
                padding: {S.px(10)}px;
            }}
            QScrollBar:vertical {{
                width: {S.px(6)}px;
                background: transparent;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {c.BORDER};
                border-radius: {S.px(3)}px;
                min-height: {S.px(30)}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c.TEXT_MUTED};
            }}
        """)
        root.addWidget(self._text, stretch=1)

        self._populate_categories()
        self._ui_built = True
        self._reload_log(force=True)

    def _build_header(self) -> QFrame:
        c = _c()
        header = QFrame()
        header.setMinimumHeight(S.px(52))
        header.setMaximumHeight(S.px(62))
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: none;
                border-radius: {S.px(10)}px;
            }}
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(20), 0, S.px(20), 0)
        layout.setSpacing(S.px(12))
        header.setLayout(layout)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon("ph.file-text", color=c.ACCENT_GREEN).pixmap(S.px(22), S.px(22)))
        icon_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(icon_lbl)

        title = QLabel(tr("Log Viewer"))
        title.setFont(QFont("Segoe UI", S.font_pt(18), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(title)

        sep = QLabel("·")
        sep.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        sep.setFont(QFont("Segoe UI", S.font_pt(14)))
        layout.addWidget(sep)

        subtitle = QLabel(tr("Inspect application log files in real time"))
        subtitle.setFont(QFont("Segoe UI", S.font_pt(11)))
        subtitle.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        layout.addWidget(subtitle)

        layout.addStretch()
        return header

    def _build_toolbar(self) -> QFrame:
        c = _c()
        bar = QFrame()
        bar.setMinimumHeight(S.px(48))
        bar.setMaximumHeight(S.px(48))
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {c.BG_CARD};
                border: none;
                border-radius: {S.px(10)}px;
            }}
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(S.px(16), 0, S.px(16), 0)
        layout.setSpacing(S.px(10))
        bar.setLayout(layout)

        layout.addWidget(self._field_label(tr("Category")))
        self._category_combo = self._combo()
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        layout.addWidget(self._category_combo)

        layout.addWidget(self._field_label(tr("Level")))
        self._level_combo = self._combo()
        for level in _LEVELS:
            self._level_combo.addItem(tr(level) if level == "ALL" else level, level)
        self._level_combo.currentIndexChanged.connect(self._on_level_changed)
        layout.addWidget(self._level_combo)

        self._search_edit = QLineEdit()
        self._search_edit.setText(self._search_text)
        self._search_edit.setPlaceholderText(tr("Search log..."))
        self._search_edit.setFixedHeight(S.px(34))
        self._search_edit.setFont(QFont("Segoe UI", S.font_pt(10)))
        self._search_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c.BG_SECONDARY};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: {S.px(6)}px;
                padding: 0 {S.px(10)}px;
            }}
            QLineEdit:focus {{
                border-color: {c.ACCENT_GREEN};
            }}
        """)
        self._search_edit.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search_edit, stretch=1)

        self._auto_toggle = ToggleWidget()
        self._auto_toggle.setChecked(self._refresh_timer.isActive())
        self._auto_toggle.toggled.connect(self._on_auto_toggled)
        layout.addWidget(self._auto_toggle)
        layout.addWidget(self._field_label(tr("Auto-refresh")))

        refresh_btn = self._icon_btn("ph.arrow-clockwise", tr("Refresh"))
        refresh_btn.clicked.connect(self._reload_log)
        layout.addWidget(refresh_btn)

        folder_btn = self._icon_btn("ph.folder-open", tr("Open Folder"))
        folder_btn.clicked.connect(self._open_log_folder)
        layout.addWidget(folder_btn)

        return bar

    # ── small factories ────────────────────────────────────────────────────
    def _field_label(self, text: str) -> QLabel:
        c = _c()
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", S.font_pt(10)))
        lbl.setStyleSheet(f"color: {c.TEXT_MUTED}; background: transparent;")
        return lbl

    def _combo(self) -> QComboBox:
        c = _c()
        combo = QComboBox()
        combo.setCursor(Qt.CursorShape.PointingHandCursor)
        combo.setFixedHeight(S.px(34))
        combo.setMinimumWidth(S.px(140))
        combo.setFont(QFont("Segoe UI", S.font_pt(10)))
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {c.BG_SECONDARY};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: {S.px(6)}px;
                padding: 0 {S.px(10)}px;
            }}
            QComboBox:hover {{
                border-color: {c.ACCENT_GREEN};
                background-color: {c.BG_HOVER};
            }}
            QComboBox::drop-down {{
                border: none;
                width: {S.px(24)}px;
            }}
            QComboBox::down-arrow {{
                border-left: {S.px(4)}px solid transparent;
                border-right: {S.px(4)}px solid transparent;
                border-top: {S.px(5)}px solid {c.TEXT_MUTED};
                margin-right: {S.px(8)}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c.BG_CARD};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: {S.px(6)}px;
                selection-background-color: {c.BG_HOVER};
                padding: {S.px(4)}px;
                outline: none;
            }}
        """)
        return combo

    def _icon_btn(self, icon: str, text: str) -> QPushButton:
        c = _c()
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", S.font_pt(10), QFont.Weight.Medium))
        btn.setFixedHeight(S.px(34))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.BG_SECONDARY};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: {S.px(6)}px;
                padding: 0 {S.px(14)}px;
            }}
            QPushButton:hover {{
                background-color: {c.BG_HOVER};
                border-color: {c.ACCENT_GREEN};
            }}
        """)
        try:
            btn.setIcon(qta.icon(icon, color=c.TEXT_PRIMARY))
            btn.setIconSize(QSize(S.px(14), S.px(14)))
        except Exception:
            pass
        return btn

    # ── data ───────────────────────────────────────────────────────────────
    def _populate_categories(self):
        log_dir = self._logger.log_dir
        try:
            names = sorted(p.stem for p in log_dir.glob("*.log"))
        except Exception:
            names = []

        if not names:
            self._current_category = None
            self._category_combo.clear()
            return

        # Only rebuild the list if it's different to prevent flickering/resets
        current_items = [self._category_combo.itemData(i) for i in range(self._category_combo.count())]
        if names == current_items:
            return

        previous = self._current_category or self._category_combo.currentData()
        
        self._category_combo.blockSignals(True)
        self._category_combo.clear()
        for name in names:
            self._category_combo.addItem(name, name)
        
        if previous in names:
            self._category_combo.setCurrentIndex(names.index(previous))
            self._current_category = previous
        else:
            self._category_combo.setCurrentIndex(0)
            self._current_category = names[0]
            
        self._category_combo.blockSignals(False)

    def _on_category_changed(self, _index: int):
        new_cat = self._category_combo.currentData()
        if new_cat != self._current_category:
            self._current_category = new_cat
            self._last_file_stat = (0, 0)  # Reset stat to force reload of new file
            self._reload_log(force=True)

    def _on_level_changed(self, _index: int):
        self._reload_log()

    def _on_search_changed(self, text: str):
        self._search_text = text
        self._reload_log()

    def _on_auto_toggled(self, checked: bool):
        if checked and self.isVisible():
            self._refresh_timer.start()
        else:
            self._refresh_timer.stop()

    def _open_log_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._logger.log_dir)))

    def _reload_log(self, force=False):
        # Don't reload if hidden and not forced
        if not self.isVisible() and not force:
            return

        self._populate_categories()

        c = _c()
        if not self._current_category:
            self._text.setPlainText(tr("No log files found."))
            return

        log_path = self._logger.log_dir / f"{self._current_category}.log"

        # Performance: Check if file actually changed to avoid heavy UI work
        try:
            st = log_path.stat()
            current_stat = (st.st_mtime, st.st_size)
            if not force and current_stat == self._last_file_stat:
                return
            self._last_file_stat = current_stat
        except Exception:
            pass

        try:
            # For large files, read only the last ~100KB to save memory/CPU
            file_size = log_path.stat().st_size
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                if file_size > 100000:
                    f.seek(file_size - 100000)
                    f.readline()  # skip potentially partial line
                lines = f.readlines()
        except Exception as e:
            self._text.setPlainText(tr("Could not read log file: {0}").format(e))
            return

        lines = [ln.rstrip("\n") for ln in lines[-_MAX_LINES:]]

        level_filter = self._level_combo.currentData() or "ALL"
        search = self._search_text.strip().lower()

        filtered = []
        for line in lines:
            match = _LEVEL_RE.search(line)
            level = match.group(1) if match else None
            if level_filter != "ALL" and level != level_filter:
                continue
            if search and search not in line.lower():
                continue
            filtered.append((line, level))

        # Save scroll state before update
        scrollbar = self._text.verticalScrollBar()
        was_at_bottom = self._is_scrolled_to_bottom()
        old_pos = scrollbar.value()

        if not filtered:
            self._text.setPlainText(tr("No matching log entries."))
            return

        level_colors = {
            "DEBUG": c.TEXT_MUTED,
            "INFO": c.TEXT_SECONDARY,
            "WARNING": c.ACCENT_YELLOW,
            "ERROR": c.ACCENT_RED,
            "CRITICAL": c.ACCENT_PINK,
        }

        rows = []
        for line, level in filtered:
            escaped = html.escape(line)
            color = level_colors.get(level)
            if color:
                rows.append(f'<span style="color:{color};">{escaped}</span>')
            else:
                rows.append(f'<span style="color:{c.TEXT_PRIMARY};">{escaped}</span>')

        # Atomic UI update to prevent flickering
        self._text.setUpdatesEnabled(False)
        self._text.setHtml(
            f'<pre style="margin:0; font-family: Consolas, monospace;">'
            + "<br>".join(rows) + "</pre>"
        )

        # Restore scroll behavior: only jump to bottom if user was already there.
        # Otherwise, maintain the exact same scroll position to avoid "jumping"
        # while the user is reading older logs.
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(old_pos)

        self._text.setUpdatesEnabled(True)

    def _is_scrolled_to_bottom(self) -> bool:
        scrollbar = self._text.verticalScrollBar()
        return scrollbar.value() >= scrollbar.maximum() - 4
