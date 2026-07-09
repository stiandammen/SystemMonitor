"""
System Monitor - Custom EXE Setup Installer & Uninstaller
Runs 100% without administrator privileges and bypasses MSI group policy blocks.
"""
import os
import sys
import shutil
from win32com.client import Dispatch
import winreg
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QProgressBar, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from systemmonitor import __version__ as VERSION

APP_NAME = "System Monitor"
PUBLISHER = "System Monitor Team"
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\SystemMonitor"


def get_default_install_dir() -> str:
    """Default install directory in Local AppData (no admin permissions required)"""
    return os.path.join(os.environ["LOCALAPPDATA"], "Programs", "System Monitor")


def create_shortcut(target_path: str, shortcut_path: str):
    """Creates a Windows shortcut using WScript.Shell"""
    try:
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.WorkingDirectory = os.path.dirname(target_path)
        shortcut.IconLocation = f"{target_path},0"
        shortcut.save()
    except Exception as e:
        print(f"Error creating shortcut: {e}")


def register_uninstall(install_dir: str, exe_path: str):
    """Registers the application in Add/Remove Programs (HKCU)"""
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        # Point uninstall to the uninstaller.exe we will place in the install folder
        uninstaller_path = os.path.join(install_dir, "uninstall.exe")
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller_path}"')
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, exe_path)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Error registering uninstall: {e}")


def unregister_uninstall():
    """Removes the application from Add/Remove Programs (HKCU)"""
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_KEY)
    except Exception as e:
        print(f"Error removing registry: {e}")


class InstallWorker(QThread):
    """Asynchronous worker to copy files and create shortcuts"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, install_dir: str, create_desktop: bool = True, create_startmenu: bool = True):
        super().__init__()
        self.install_dir = install_dir
        self.create_desktop = create_desktop
        self.create_startmenu = create_startmenu

    def run(self):
        try:
            # 1. Create installation directory
            self.progress.emit(10, "Creating directory...")
            os.makedirs(self.install_dir, exist_ok=True)
            
            # Locate embedded resources unpacked by PyInstaller
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            source_exe = os.path.join(base_path, "SystemMonitor.exe")
            
            if not os.path.exists(source_exe):
                self.finished.emit(False, f"Source executable not found in installer assets:\n{source_exe}")
                return
                
            dest_exe = os.path.join(self.install_dir, "SystemMonitor.exe")
            
            # 2. Copy the main executable
            self.progress.emit(30, "Copying application file...")
            shutil.copy2(source_exe, dest_exe)
            
            # 3. Create uninstaller (copy of this installer executable itself)
            self.progress.emit(50, "Creating uninstaller...")
            installer_src = sys.argv[0]
            uninstaller_dest = os.path.join(self.install_dir, "uninstall.exe")
            if installer_src.endswith(".exe"):
                shutil.copy2(installer_src, uninstaller_dest)
            else:
                # If running raw python script, copy a stub
                with open(uninstaller_dest, 'w') as f:
                    f.write("# Stub uninstaller")
                    
            # 4. Create shortcuts
            self.progress.emit(70, "Configuring shortcuts...")
            
            # Paths to shortcuts
            desktop_dir = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            desktop_lnk = os.path.join(desktop_dir, f"{APP_NAME}.lnk")
            
            start_menu_dir = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs')
            start_lnk = os.path.join(start_menu_dir, f"{APP_NAME}.lnk")
            
            # Clean up old shortcuts first (so unchecked state works correctly)
            if os.path.exists(desktop_lnk):
                try: os.remove(desktop_lnk)
                except Exception: pass
            if os.path.exists(start_lnk):
                try: os.remove(start_lnk)
                except Exception: pass
            
            # Desktop shortcut
            if self.create_desktop:
                create_shortcut(dest_exe, desktop_lnk)
            
            # Start Menu shortcut
            if self.create_startmenu:
                os.makedirs(start_menu_dir, exist_ok=True)
                create_shortcut(dest_exe, start_lnk)
            
            # 5. Register uninstall in registry
            self.progress.emit(90, "Registering with Windows...")
            register_uninstall(self.install_dir, dest_exe)
            
            self.progress.emit(100, "Installation complete!")
            self.finished.emit(True, "")
            
        except Exception as e:
            self.finished.emit(False, str(e))


class InstallerWindow(QMainWindow):
    """Beautiful, modern installer window styled matching System Monitor's dark theme"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} Setup")
        self.setFixedSize(500, 320)
        self.init_ui()

    def init_ui(self):
        # Apply dark theme stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0d1117;
            }
            QLabel {
                color: #c9d1d9;
                font-family: 'Segoe UI';
            }
            QLineEdit {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 6px;
                color: #c9d1d9;
                padding: 6px 12px;
                font-family: 'Segoe UI';
            }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 6px;
                color: #c9d1d9;
                padding: 6px 16px;
                font-family: 'Segoe UI';
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #8b949e;
            }
            QPushButton#accent {
                background-color: #10b981;
                border: 1px solid #10b981;
                color: #0d1117;
            }
            QPushButton#accent:hover {
                background-color: #059669;
                border-color: #059669;
            }
            QProgressBar {
                border: 1px solid #30363d;
                border-radius: 6px;
                background-color: #161b22;
                text-align: center;
                color: #c9d1d9;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 5px;
            }
            QCheckBox {
                color: #c9d1d9;
                font-family: 'Segoe UI';
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Set window icon from bundled assets
        try:
            from PyQt6.QtGui import QIcon
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "icon.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Title Label
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        self.title_lbl = QLabel(f"Install {APP_NAME}")
        self.title_lbl.setFont(title_font)
        self.title_lbl.setStyleSheet("color: #10b981;")
        layout.addWidget(self.title_lbl)

        # Description Label
        self.desc_lbl = QLabel(
            "This installer will place System Monitor in your local User folder.\n"
            "No administrator rights or system changes are required."
        )
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl)

        # Path Selection Layout
        self.path_widget = QWidget()
        path_layout = QHBoxLayout(self.path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        
        self.path_input = QLineEdit(get_default_install_dir())
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_path)
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_btn)
        layout.addWidget(self.path_widget)

        # Shortcuts Checkboxes Layout
        self.shortcuts_widget = QWidget()
        shortcuts_layout = QVBoxLayout(self.shortcuts_widget)
        shortcuts_layout.setContentsMargins(0, 0, 0, 0)
        shortcuts_layout.setSpacing(6)
        
        self.desktop_chk = QCheckBox("Lag snarvei på Skrivebordet (Create Desktop shortcut)")
        self.desktop_chk.setChecked(True)
        self.startmenu_chk = QCheckBox("Lag snarvei i Start-menyen (Create Start Menu shortcut)")
        self.startmenu_chk.setChecked(True)
        
        shortcuts_layout.addWidget(self.desktop_chk)
        shortcuts_layout.addWidget(self.startmenu_chk)
        layout.addWidget(self.shortcuts_widget)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()

        # Buttons Layout
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        
        self.install_btn = QPushButton("Install")
        self.install_btn.setObjectName("accent")
        self.install_btn.clicked.connect(self.start_install)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.install_btn)
        layout.addWidget(btn_widget)

    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Installation Folder", self.path_input.text()
        )
        if directory:
            # Ensure we append 'System Monitor' folder
            if not directory.endswith(APP_NAME):
                directory = os.path.join(directory, APP_NAME)
            self.path_input.setText(directory)

    def start_install(self):
        install_dir = self.path_input.text().strip()
        if not install_dir:
            return
            
        self.path_widget.setVisible(False)
        self.shortcuts_widget.setVisible(False)
        self.install_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.desc_lbl.setText("Copying files, please wait...")
        
        self.worker = InstallWorker(
            install_dir,
            self.desktop_chk.isChecked(),
            self.startmenu_chk.isChecked()
        )
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.install_finished)
        self.worker.start()

    def update_progress(self, val: int, status: str):
        self.progress_bar.setValue(val)
        self.desc_lbl.setText(status)

    def install_finished(self, success: bool, error_msg: str):
        if success:
            msg = f"{APP_NAME} was installed successfully!\n"
            created = []
            if self.desktop_chk.isChecked():
                created.append("Desktop")
            if self.startmenu_chk.isChecked():
                created.append("Start Menu")
            if created:
                msg += f"Shortcuts have been created on your {', '.join(created)}."
            else:
                msg += "No shortcuts were created."
                
            QMessageBox.information(
                self, "Success", msg, QMessageBox.StandardButton.Ok
            )
            self.close()
        else:
            QMessageBox.critical(
                self, "Installation Failed",
                f"An error occurred during installation:\n{error_msg}",
                QMessageBox.StandardButton.Ok
            )
            self.path_widget.setVisible(True)
            self.shortcuts_widget.setVisible(True)
            self.progress_bar.setVisible(False)
            self.install_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)


def run_uninstaller():
    """Performs clean uninstallation of files, shortcuts, and registry entries"""
    # Locate where uninstaller is running from (this should be the install directory)
    install_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    # Simple check to make sure we don't delete system folders by mistake
    if not install_dir.endswith(APP_NAME) and not install_dir.endswith("System Monitor"):
        print("Safety check failed. Uninstaller must run from the install folder.")
        return

    print(f"Uninstalling {APP_NAME} from: {install_dir}")
    
    # 0. Terminate any running instances of the application to unlock files
    try:
        import subprocess
        # 0x08000000 is CREATE_NO_WINDOW
        subprocess.run(
            'taskkill /f /im SystemMonitor.exe',
            shell=True,
            creationflags=0x08000000
        )
    except Exception:
        pass
    
    # 1. Delete Shortcuts
    # Desktop
    desktop_dir = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    desktop_lnk = os.path.join(desktop_dir, f"{APP_NAME}.lnk")
    if os.path.exists(desktop_lnk):
        try: os.remove(desktop_lnk)
        except Exception: pass
        
    # Start Menu
    start_menu_dir = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs')
    start_lnk = os.path.join(start_menu_dir, f"{APP_NAME}.lnk")
    if os.path.exists(start_lnk):
        try: os.remove(start_lnk)
        except Exception: pass
        
    # 2. Delete Registry entries
    unregister_uninstall()
    
    # 3. Change current working directory to TEMP so the uninstaller process does not lock the directory
    try:
        os.chdir(os.environ["TEMP"])
    except Exception:
        pass
        
    # 4. Schedule deletion of the install folder itself
    # Since uninstall.exe is currently running from inside the install folder, Windows won't let it delete itself directly.
    # We spawn a quick cmd script to delete it after this process exits.
    temp_bat = os.path.join(os.environ["TEMP"], "cleanup_sysmon_uninstall.bat")
    
    # The batch script loops until the directory is completely deleted, then deletes itself.
    bat_content = f"""@echo off
set /a count=0
:loop
rmdir /s /q "{install_dir}"
if exist "{install_dir}" (
    set /a count+=1
    if %count% geq 10 goto end
    timeout /t 1 /nobreak > NUL
    goto loop
)
:end
del "%~f0"
"""
    try:
        with open(temp_bat, 'w', encoding='utf-8') as f:
            f.write(bat_content)
            
        # Run the cleanup batch script detached
        subprocess_flags = 0x08000000 # CREATE_NO_WINDOW
        import subprocess
        subprocess.Popen(
            f'cmd.exe /c "{temp_bat}"',
            shell=True,
            creationflags=subprocess_flags
        )
        print("Cleanup scheduled. Uninstallation complete.")
    except Exception as e:
        print(f"Failed to write cleanup script: {e}")


def main():
    # If run with '--uninstall' or if the executable name is 'uninstall.exe', run uninstall process
    exe_name = os.path.basename(sys.argv[0]).lower()
    if "--uninstall" in sys.argv or exe_name == "uninstall.exe":
        # Headless console uninstallation
        run_uninstaller()
        sys.exit(0)
        
    # Otherwise run the graphical installer
    app = QApplication(sys.argv)
    app.setApplicationName(f"{APP_NAME} Setup")
    window = InstallerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
