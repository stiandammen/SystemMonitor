"""
System Monitor - Software Updater
Asynchronous update check, download, and installation for packaged Windows MSI builds
"""
import os
import sys
import json
import urllib.request
import urllib.error
import subprocess
import tempfile
from PyQt6.QtCore import QThread, pyqtSignal
from systemmonitor import __version__
from systemmonitor.utils.logger import log_info, log_error, log_warning, LogCategory

# GitHub repository configuration
GITHUB_OWNER = "stiandammen"
GITHUB_REPO = "SystemMonitor"


def get_latest_release_url() -> str:
    """Build the GitHub API URL for the latest release"""
    return f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"


def is_newer_version(current: str, remote: str) -> bool:
    """Compare version strings (e.g. '2.0.0' vs 'v2.1.0')"""
    try:
        c_clean = current.strip().lower().lstrip('v')
        r_clean = remote.strip().lower().lstrip('v')
        
        c_parts = [int(x) for x in c_clean.split('.')]
        r_parts = [int(x) for x in r_clean.split('.')]
        
        # Pad lists to equal length
        max_len = max(len(c_parts), len(r_parts))
        c_parts += [0] * (max_len - len(c_parts))
        r_parts += [0] * (max_len - len(r_parts))
        
        return r_parts > c_parts
    except Exception as e:
        log_error(LogCategory.APP, f"Error comparing versions {current} and {remote}: {e}")
        return False


class UpdateCheckerThread(QThread):
    """Asynchronous worker to check GitHub for new releases"""
    check_finished = pyqtSignal(bool, dict)  # (update_available, release_data)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        url = get_latest_release_url()
        log_info(LogCategory.APP, f"Checking for updates at {url}")
        
        try:
            # Set User-Agent to avoid HTTP 403 Forbidden from GitHub API
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'SystemMonitor-Updater'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    remote_version = data.get("tag_name", "0.0.0")
                    
                    update_available = is_newer_version(__version__, remote_version)
                    
                    # Find EXE (preferred Setup.exe) or MSI asset in release assets
                    update_url = ""
                    update_name = ""
                    for asset in data.get("assets", []):
                        name = asset.get("name", "")
                        if name.endswith(".exe"):
                            update_url = asset.get("browser_download_url", "")
                            update_name = name
                            break
                    
                    if not update_url:
                        # Fallback to MSI if no EXE was found
                        for asset in data.get("assets", []):
                            name = asset.get("name", "")
                            if name.endswith(".msi"):
                                update_url = asset.get("browser_download_url", "")
                                update_name = name
                                break
                    
                    update_info = {
                        "version": remote_version,
                        "release_notes": data.get("body", "No release notes available."),
                        "html_url": data.get("html_url", ""),
                        "msi_url": update_url,
                        "msi_name": update_name
                    }
                    
                    log_info(LogCategory.APP, f"Update check finished. Available: {update_available}. Latest: {remote_version}")
                    self.check_finished.emit(update_available, update_info)
                else:
                    log_error(LogCategory.APP, f"GitHub API returned status {response.status}")
                    self.check_finished.emit(False, {"error": f"Server returned status {response.status}"})
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # 404 means no releases are published yet on this repository
                log_warning(LogCategory.APP, f"No releases published on GitHub repository yet (HTTP 404).")
                self.check_finished.emit(False, {})
            else:
                log_error(LogCategory.APP, f"HTTP Error checking for updates: {e}")
                self.check_finished.emit(False, {"error": f"HTTP {e.code}: {e.reason}"})
        except Exception as e:
            log_error(LogCategory.APP, f"Error checking for updates: {e}")
            self.check_finished.emit(False, {"error": str(e)})


class UpdateDownloaderThread(QThread):
    """Asynchronous worker to download the MSI installer from GitHub"""
    progress = pyqtSignal(int)                         # Percent complete (0-100)
    finished = pyqtSignal(bool, str, str)              # (success, file_path, error_message)

    def __init__(self, download_url: str, filename: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.filename = filename
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        log_info(LogCategory.APP, f"Starting download from {self.download_url}")
        try:
            # Prepare destination file in Temp directory
            temp_dir = tempfile.gettempdir()
            dest_path = os.path.join(temp_dir, self.filename)
            
            # Request setup
            req = urllib.request.Request(
                self.download_url,
                headers={'User-Agent': 'SystemMonitor-Updater'}
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                total_size = int(response.info().get('Content-Length', 0))
                downloaded = 0
                block_size = 8192
                
                with open(dest_path, 'wb') as f:
                    while True:
                        if self._is_cancelled:
                            log_info(LogCategory.APP, "Download cancelled by user.")
                            self.finished.emit(False, "", "Download cancelled")
                            return
                            
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        
                        f.write(buffer)
                        downloaded += len(buffer)
                        
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(percent)
                            
            log_info(LogCategory.APP, f"Download complete: {dest_path}")
            self.finished.emit(True, dest_path, "")
            
        except Exception as e:
            log_error(LogCategory.APP, f"Download failed: {e}")
            self.finished.emit(False, "", str(e))


def run_msi_installer(file_path: str):
    """Launches the downloaded installer (.exe or .msi) and closes the application"""
    log_info(LogCategory.APP, f"Launching installer: {file_path}")
    try:
        if file_path.lower().endswith(".msi"):
            cmd = f'msiexec.exe /i "{file_path}" /qb /norestart'
        else:
            # For Setup.exe, run it directly in detached mode
            cmd = f'"{file_path}"'
        
        # Start as a completely detached background process
        subprocess.Popen(
            cmd,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
        
        # Exit SystemMonitor immediately so the installer can replace the files
        log_info(LogCategory.APP, "Exiting SystemMonitor for update installation...")
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
        sys.exit(0)
    except Exception as e:
        log_error(LogCategory.APP, f"Failed to execute installer: {e}")
