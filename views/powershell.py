"""
Command Prompt View - Windows CMD terminal with modern UI
INPUT | OUTPUT layout with full CMD functionality and proper TAB cycling
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QFrame, QSplitter,
    QShortcut, QToolTip
)
from PyQt5.QtCore import Qt, QProcess, QRect
from PyQt5.QtGui import QFont, QTextCursor, QKeySequence

from styles.theme import theme_manager
from filesystem import get_filesystem


class CmdInput(QLineEdit):
    """
    Enhanced CMD input with command history and proper TAB cycling autocomplete.
    TAB cycles through matches like real Windows CMD/PowerShell.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []
        self._history_index = -1
        self._current_history_search = ""
        self._fs = get_filesystem()

        # TAB cycling state
        self._tab_matches = []
        self._tab_index = -1
        self._tab_original = ""
        self._tab_cwd = ""

        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        up_shortcut = QShortcut(QKeySequence(Qt.Key_Up), self)
        up_shortcut.activated.connect(self._history_up)

        down_shortcut = QShortcut(QKeySequence(Qt.Key_Down), self)
        down_shortcut.activated.connect(self._history_down)

    def add_to_history(self, command):
        """Add command to history"""
        if command.strip() and (not self._history or self._history[0] != command):
            self._history.insert(0, command)
            if len(self._history) > 100:
                self._history.pop()
        self._history_index = -1
        self._current_history_search = ""

    def _history_up(self):
        """Navigate up in history"""
        if not self._history:
            return

        if self._history_index == -1:
            self._current_history_search = self.text()

        for i, cmd in enumerate(self._history):
            if self._history_index == -1 or i < self._history_index:
                if cmd.lower().startswith(self._current_history_search.lower()):
                    self._history_index = i
                    self.setText(cmd)
                    self.setCursorPosition(len(cmd))
                    return

    def _history_down(self):
        """Navigate down in history"""
        if self._history_index <= -1:
            return

        self._history_index -= 1
        if self._history_index < 0:
            self._history_index = -1
            self.setText(self._current_history_search)
        else:
            self.setText(self._history[self._history_index])
        self.setCursorPosition(len(self.text()))

    def keyPressEvent(self, event):
        """Handle key events with TAB cycling autocomplete - Windows CMD style"""
        # TAB for cycling autocomplete (Windows CMD style)
        if event.key() == Qt.Key_Tab:
            self._handle_tab_cycle()
            event.accept()
            return

        # Reset TAB state on any other key (except modifiers)
        if event.key() not in (Qt.Key_Shift, Qt.Key_Control, Qt.Key_Meta,
                              Qt.Key_Alt, Qt.Key_Tab, Qt.Key_Backtab):
            self._reset_tab_state()

        super().keyPressEvent(event)

    def _reset_tab_state(self):
        """Reset TAB cycling state"""
        self._tab_matches = []
        self._tab_index = -1
        self._tab_original = ""
        self._tab_cwd = ""

    def _handle_tab_cycle(self):
        """
        Handle TAB press - cycles through matching paths like Windows CMD.
        First TAB builds the list, subsequent TABs cycle through matches.
        Implements Windows CMD style TAB completion for paths.
        """
        text = self.text()
        if not text.strip():
            return

        parts = text.split()
        if not parts:
            return

        # Get the last argument (partial path to complete)
        last_arg = parts[-1] if len(parts) > 0 else ""

        # Get current working directory for this session
        cwd = self._fs.get_current_path()

        # First TAB - build the matches list
        if not self._tab_matches or self._tab_cwd != cwd or self._tab_original != last_arg:
            # Building new matches list
            self._tab_original = last_arg
            self._tab_cwd = cwd
            self._tab_matches = self._get_path_matches(last_arg, cwd)
            self._tab_index = -1

            if not self._tab_matches:
                return

            # First match - autocomplete directly (Windows CMD style)
            self._tab_index = 0
            suggestion = self._tab_matches[self._tab_index]

            # Reconstruct the command with the suggestion
            if len(parts) > 1:
                new_text = " ".join(parts[:-1]) + " " + suggestion
            else:
                new_text = suggestion

            self.setText(new_text)
            self.setCursorPosition(len(new_text))
        else:
            # Subsequent TAB - cycle through matches (Windows CMD style)
            if not self._tab_matches:
                return

            self._tab_index = (self._tab_index + 1) % len(self._tab_matches)
            suggestion = self._tab_matches[self._tab_index]

            # Reconstruct the command
            if len(parts) > 1:
                new_text = " ".join(parts[:-1]) + " " + suggestion
            else:
                new_text = suggestion

            self.setText(new_text)
            self.setCursorPosition(len(new_text))

            # Show current position in tooltip (like Windows CMD)
            if len(self._tab_matches) > 1:
                pos = f"{self._tab_index + 1}/{len(self._tab_matches)}"
                matches = ", ".join(self._tab_matches[:5])
                if len(self._tab_matches) > 5:
                    matches += f" (+{len(self._tab_matches) - 5} more)"
                QToolTip.showText(
                    self.mapToGlobal(self.rect().bottomLeft()),
                    f"{pos}: {matches}",
                    self, QRect(), 3000
                )

    def _get_path_matches(self, path_input, cwd):
        """
        Get all path matches for the given input.
        Returns sorted list of folders (with \ suffix) and files.
        """
        completions = []

        # Parse the path input
        clean_path = path_input.replace('/', '\\')

        # Handle drive letter
        if len(clean_path) == 2 and clean_path[1] == ':':
            clean_path += '\\'

        # Determine search directory and partial name
        if '\\' in clean_path:
            parts = clean_path.rsplit('\\', 1)
            if clean_path.endswith('\\'):
                search_dir = clean_path
                partial = ""
            else:
                search_dir = parts[0] if parts[0] else cwd
                partial = parts[1]
        else:
            search_dir = cwd
            partial = clean_path

        # Get items from filesystem
        try:
            items = self._fs.list_directory(search_dir)
            for name, is_dir in items:
                if name.lower().startswith(partial.lower()):
                    if is_dir:
                        completions.append(name + '\\')
                    else:
                        completions.append(name)
        except:
            pass

        return sorted(completions, key=str.lower)

    def _handle_tab_autocomplete(self):
        """Legacy method - redirects to new cycling implementation"""
        self._handle_tab_cycle()


class CommandPromptView(QWidget):
    """
    Windows Command Prompt (CMD) terminal with modern UI.
    INPUT | OUTPUT layout with full CMD functionality.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = None
        self._fs = get_filesystem()
        self._history = []
        self._history_index = -1
        self._activity = []
        self._setup_ui()
        self._start_cmd()

    def _setup_ui(self):
        """Setup modern CMD UI"""
        c = theme_manager.colors

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # ── Header ──────────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet(f"""
            background-color: {c.BG_SECONDARY};
            border-bottom: 1px solid {c.BORDER};
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(16, 0, 12, 0)
        header_layout.setSpacing(10)
        header.setLayout(header_layout)

        # Icon + Title
        icon = QLabel("⌨")
        icon.setFont(QFont("Segoe UI", 14))
        header_layout.addWidget(icon)

        title = QLabel("Command Prompt")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setStyleSheet(f"color: {c.TEXT_PRIMARY};")
        header_layout.addWidget(title)

        # Current path
        self._path_label = QLabel(self._fs.get_current_path())
        self._path_label.setFont(QFont("Consolas", 10))
        self._path_label.setStyleSheet(f"""
            color: {c.ACCENT_GREEN};
            background-color: {c.BG_PRIMARY};
            padding: 4px 10px;
            border-radius: 4px;
            border: 1px solid {c.BORDER};
        """)
        header_layout.addWidget(self._path_label)

        header_layout.addStretch()

        # Status
        self._status_dot = QLabel("●")
        self._status_dot.setFont(QFont("Segoe UI", 9))
        self._status_dot.setStyleSheet(f"color: {c.ACCENT_GREEN};")
        header_layout.addWidget(self._status_dot)

        status_text = QLabel("Active")
        status_text.setFont(QFont("Segoe UI", 9))
        status_text.setStyleSheet(f"color: {c.TEXT_MUTED};")
        header_layout.addWidget(status_text)

        # Buttons
        btn_style = f"""
            QPushButton {{
                background-color: {c.BG_HOVER};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {c.BG_CARD};
                border-color: {c.ACCENT_BLUE};
            }}
        """

        cls_btn = QPushButton("Clear")
        cls_btn.setStyleSheet(btn_style)
        cls_btn.clicked.connect(self._clear_output)
        header_layout.addWidget(cls_btn)

        restart_btn = QPushButton("Restart")
        restart_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c.ACCENT_GREEN};
                color: #000000;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: bold;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: #0d9a5d;
            }}
        """)
        restart_btn.clicked.connect(self._restart_cmd)
        header_layout.addWidget(restart_btn)

        main_layout.addWidget(header)

        # ── Main Content: INPUT | OUTPUT ─────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {c.BORDER};
                width: 2px;
            }}
        """)
        splitter.setSizes([240, 760])

        # ══ INPUT Pane (left) ═══════════════════════════════════════════════
        input_frame = QFrame()
        input_frame.setStyleSheet(f"background-color: {c.BG_PRIMARY};")
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(12, 12, 12, 12)
        input_layout.setSpacing(8)
        input_frame.setLayout(input_layout)

        # Label
        input_label = QLabel("── INPUT ──")
        input_label.setFont(QFont("Consolas", 9, QFont.Bold))
        input_label.setStyleSheet(f"color: {c.ACCENT_BLUE}; letter-spacing: 2px;")
        input_layout.addWidget(input_label)

        # Prompt input
        prompt_frame = QFrame()
        prompt_frame.setStyleSheet(f"""
            background-color: {c.BG_INPUT};
            border: 2px solid {c.ACCENT_BLUE};
            border-radius: 6px;
            padding: 4px 8px;
        """)
        prompt_layout = QHBoxLayout()
        prompt_layout.setContentsMargins(6, 3, 6, 3)
        prompt_layout.setSpacing(4)
        prompt_frame.setLayout(prompt_layout)

        prompt_label = QLabel()
        prompt_label.setFont(QFont("Consolas", 12, QFont.Bold))
        prompt_label.setStyleSheet(f"color: {c.ACCENT_GREEN};")
        prompt_layout.addWidget(prompt_label)
        self._prompt_label = prompt_label
        self._update_prompt_label()

        self._input = CmdInput()
        self._input.setFont(QFont("Consolas", 12))
        self._input.setPlaceholderText("Type command (TAB to cycle)...")
        self._input.setStyleSheet(f"""
            background-color: transparent;
            color: {c.TEXT_PRIMARY};
            border: none;
            padding: 3px 0px;
        """)
        self._input.returnPressed.connect(self._execute_command)
        prompt_layout.addWidget(self._input)

        input_layout.addWidget(prompt_frame)

        # Hint
        hint = QLabel("TAB cycles through folders")
        hint.setFont(QFont("Segoe UI", 9))
        hint.setStyleSheet(f"color: {c.TEXT_MUTED}; font-style: italic;")
        input_layout.addWidget(hint)

        input_layout.addStretch()

        # ══ OUTPUT Pane (right) ════════════════════════════════════════════
        output_frame = QFrame()
        output_frame.setStyleSheet(f"""
            background-color: #0a0e14;
            border-left: 2px solid {c.BORDER};
        """)
        output_layout = QVBoxLayout()
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(0)
        output_frame.setLayout(output_layout)

        # Header
        output_header = QFrame()
        output_header.setFixedHeight(30)
        output_header.setStyleSheet(f"background-color: {c.BG_SECONDARY}; border-bottom: 1px solid {c.BORDER};")
        output_header_layout = QHBoxLayout()
        output_header_layout.setContentsMargins(14, 0, 10, 0)
        output_header_layout.setSpacing(6)
        output_header.setLayout(output_header_layout)

        output_title = QLabel("OUTPUT")
        output_title.setFont(QFont("Consolas", 9, QFont.Bold))
        output_title.setStyleSheet(f"color: {c.TEXT_MUTED}; letter-spacing: 2px;")
        output_header_layout.addWidget(output_title)

        output_header_layout.addStretch()

        copy_btn = QPushButton("Copy")
        copy_btn.setFont(QFont("Segoe UI", 9))
        copy_btn.setFixedSize(46, 20)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {c.TEXT_MUTED};
                border: 1px solid {c.BORDER};
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {c.BG_HOVER};
                color: {c.TEXT_PRIMARY};
            }}
        """)
        copy_btn.clicked.connect(self._copy_output)
        output_header_layout.addWidget(copy_btn)

        output_layout.addWidget(output_header)

        # Terminal output - 20px with tech font
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0e14;
                color: #00ab84;
                border: none;
                font-family: 'Cascadia Mono', 'Fira Code', 'Consolas', monospace;
                font-size: 20px;
                line-height: 1.35;
                padding: 14px 18px;
            }}
        """)
        output_layout.addWidget(self._output, 1)

        splitter.addWidget(input_frame)
        splitter.addWidget(output_frame)

        main_layout.addWidget(splitter, 1)

        # ── Activity Monitor (at bottom) ───────────────────────────────────
        activity_frame = QFrame()
        activity_frame.setStyleSheet(f"""
            background-color: {c.BG_SECONDARY};
            border-top: 2px solid {c.BORDER};
        """)
        activity_layout = QHBoxLayout()
        activity_layout.setContentsMargins(10, 6, 10, 6)
        activity_layout.setSpacing(10)
        activity_frame.setLayout(activity_layout)

        activity_label = QLabel("── ACTIVITY ──")
        activity_label.setFont(QFont("Consolas", 9, QFont.Bold))
        activity_label.setStyleSheet(f"color: {c.ACCENT_BLUE}; letter-spacing: 1px;")
        activity_label.setFixedWidth(100)
        activity_layout.addWidget(activity_label)

        self._activity_log = QTextEdit()
        self._activity_log.setReadOnly(True)
        self._activity_log.setMaximumHeight(80)
        self._activity_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c.BG_PRIMARY};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: 4px;
                font-family: 'Cascadia Mono', 'Consolas', monospace;
                font-size: 20px;
                padding: 8px 10px;
            }}
        """)
        activity_layout.addWidget(self._activity_log, 1)

        main_layout.addWidget(activity_frame)

        # Welcome
        self._append_output("Microsoft Windows [Version 10.0.19041.1]\n", "#64748b")
        self._append_output("Copyright (C) Microsoft Corporation. All rights reserved.\n\n", "#64748b")
        self._log_activity("CMD session started. TAB to autocomplete.")

    def _log_activity(self, message):
        """Log activity with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._activity_log.append(f"[{timestamp}] {message}")
        self._activity.append((timestamp, message))

    def _start_cmd(self):
        """Start CMD process"""
        if self._process:
            try:
                self._process.kill()
                self._process.waitForFinished(500)
            except:
                pass
            self._process.deleteLater()
            self._process = None

        self._process = QProcess(self)
        self._process.setProgram("cmd.exe")
        self._process.setArguments(["/K", "cd /D " + self._fs.get_current_path()])

        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.stateChanged.connect(self._on_state_changed)
        self._process.start()

        self._update_path_display()

    def _restart_cmd(self):
        """Restart CMD"""
        self._output.clear()
        self._log_activity("Session restarted")
        self._start_cmd()

    def _on_state_changed(self, state):
        """Handle state changes"""
        if state == QProcess.NotRunning:
            self._append_output("\n[CMD session ended]\n", "#ef4444")
            self._input.setEnabled(False)
            self._status_dot.setStyleSheet("color: #ef4444;")
            self._log_activity("Session ended")
        elif state == QProcess.Running:
            self._input.setEnabled(True)
            self._input.setFocus()
            self._status_dot.setStyleSheet("color: #10b981;")
            self._log_activity("Session active")

    def _on_stdout(self):
        """Handle stdout from CMD"""
        if not self._process:
            return
        data = self._process.readAllStandardOutput()
        if data.size() > 0:
            try:
                text = str(data, encoding='utf-8')
            except:
                text = str(data, encoding='utf-8', errors='replace')
            self._append_output(text, "#00ab84")

    def _on_stderr(self):
        """Handle stderr from CMD"""
        if not self._process:
            return
        data = self._process.readAllStandardError()
        if data.size() > 0:
            try:
                text = str(data, encoding='utf-8')
            except:
                text = str(data, encoding='utf-8', errors='replace')
            self._append_output(text, "#ef4444")

    def _append_output(self, text, color="#00ab84"):
        """Append text to output"""
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self._output.setTextCursor(cursor)
        self._output.ensureCursorVisible()

    def _clear_output(self):
        """Clear output"""
        self._output.clear()
        self._log_activity("Output cleared")

    def _copy_output(self):
        """Copy output to clipboard"""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self._output.toPlainText())
        self._log_activity("Output copied")

    def _update_path_display(self):
        """Update path display and prompt"""
        path = self._fs.get_current_path()
        self._path_label.setText(path)
        self._update_prompt_label()

    def _update_prompt_label(self):
        """Update the prompt label with current drive"""
        if hasattr(self, '_prompt_label'):
            path = self._fs.get_current_path()
            if len(path) >= 2 and path[1] == ':':
                drive = path[0].upper()
                self._prompt_label.setText(drive + ":>")
            else:
                self._prompt_label.setText("C:>")

    def _execute_command(self):
        """Execute CMD command"""
        command = self._input.text().strip()
        self._input.clear()

        # Reset TAB state when executing
        self._input._reset_tab_state()

        if not command:
            return

        self._input.add_to_history(command)
        self._log_activity("$ " + command)

        if not self._process or self._process.state() != QProcess.Running:
            self._append_output("CMD not running. Click Restart.\n", "#ef4444")
            self._log_activity("Error: Not running")
            return

        # Handle cls
        if command.lower() == 'cls':
            self._clear_output()
            return

        # Handle drive letter change (C:, D:, E:, etc.)
        if self._is_drive_change(command):
            self._handle_drive_change(command)
            drive = self._get_current_drive()
            self._append_output(drive + "> " + command + "\n", "#3b82f6")
            try:
                self._process.write((command + "\r\n").encode('utf-8'))
            except Exception as e:
                self._append_output(f"Error: {str(e)}\n", "#ef4444")
            self._update_path_display()
            return

        # Handle cd - sync with filesystem
        if command.lower().startswith('cd ') or command.lower() == 'cd':
            self._handle_cd(command)

        # Echo command to output
        drive = self._get_current_drive()
        self._append_output(drive + "> " + command + "\n", "#3b82f6")

        # Send to CMD
        try:
            self._process.write((command + "\r\n").encode('utf-8'))
        except Exception as e:
            self._append_output(f"Error: {str(e)}\n", "#ef4444")

        self._update_path_display()

    def _get_current_drive(self):
        """Get current drive letter"""
        path = self._fs.get_current_path()
        if len(path) >= 2 and path[1] == ':':
            return path[0].upper()
        return "C"

    def _handle_cd(self, command):
        """Handle cd command - sync filesystem"""
        parts = command.strip().split(maxsplit=1)
        path = parts[1] if len(parts) > 1 else ""

        success, error = self._fs.change_directory(path)

        if success:
            if self._process and self._process.state() == QProcess.Running:
                new_cwd = self._fs.get_current_path()
                cd_cmd = f"cd /D {new_cwd}\r\n"
                self._process.write(cd_cmd.encode('utf-8'))
            self._update_path_display()
            self._log_activity("cd: " + self._fs.get_current_path())
        else:
            self._append_output(f"cd: {error}\n", "#ef4444")
            self._log_activity("cd error: " + error)

    def _is_drive_change(self, command):
        """Check if command is a drive change (C:, D:, etc.)"""
        cmd = command.strip().upper()
        if len(cmd) >= 2 and cmd[1] == ':' and cmd[0].isalpha():
            return True
        return False

    def _handle_drive_change(self, command):
        """Handle drive change command - sync filesystem"""
        cmd = command.strip().upper()
        drive = cmd[0]

        drive_path = drive + ":\\"
        success, error = self._fs.change_directory(drive_path)

        if success:
            self._log_activity("Drive changed to " + drive + ":")
        else:
            self._append_output(f"Drive change failed: {error}\n", "#ef4444")
            self._log_activity("Drive error: " + error)

    def update_data(self, data):
        """Handle data updates"""
        self._update_path_display()