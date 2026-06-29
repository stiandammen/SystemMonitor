"""Windows autostart management using Task Scheduler.

This implementation uses Windows Task Scheduler instead of the Registry 'Run' key.
This is necessary because the app requires Administrator privileges (UAC).
Windows block apps with UAC requirements from starting via the Registry.
Task Scheduler allows us to bypass this by creating a task that runs with 
'Highest Privileges' at user logon.
"""
import os
import sys
import subprocess
import platform

class AutostartManager:
    """Manages whether SystemMonitor launches automatically at sign-in using Task Scheduler."""

    TASK_NAME = "SystemMonitorAutostart"

    @classmethod
    def _get_exe_path(cls) -> str:
        """Returns the absolute path to the executable or script."""
        if getattr(sys, 'frozen', False):
            return os.path.abspath(sys.executable)
        return os.path.abspath(sys.argv[0])

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if the scheduled task exists."""
        if platform.system() != 'Windows':
            return False
            
        try:
            # Check if task exists using schtasks
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", cls.TASK_NAME],
                capture_output=True, text=True, creationflags=0x08000000
            )
            return result.returncode == 0
        except Exception:
            return False

    @classmethod
    def enable(cls) -> bool:
        """Create a scheduled task to run with highest privileges at logon."""
        if platform.system() != 'Windows':
            return False
            
        exe_path = cls._get_exe_path()
        # We use PowerShell to create the task because it allows setting 'Highest' principal easily
        ps_command = (
            f"$action = New-ScheduledTaskAction -Execute '{exe_path}'; "
            f"$trigger = New-ScheduledTaskTrigger -AtLogOn; "
            f"$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest; "
            f"$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0; "
            f"Register-ScheduledTask -TaskName '{cls.TASK_NAME}' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force"
        )
        
        try:
            # Note: Creating/Registering a task with 'Highest' usually requires being admin themselves
            # which our app already is.
            result = subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command", ps_command],
                capture_output=True, text=True, creationflags=0x08000000
            )
            return result.returncode == 0
        except Exception:
            return False

    @classmethod
    def disable(cls) -> bool:
        """Remove the scheduled task."""
        if platform.system() != 'Windows':
            return True
            
        try:
            result = subprocess.run(
                ["schtasks", "/Delete", "/TN", cls.TASK_NAME, "/F"],
                capture_output=True, text=True, creationflags=0x08000000
            )
            return result.returncode == 0 or "not found" in result.stderr.lower()
        except Exception:
            return False

    @classmethod
    def toggle(cls) -> bool:
        """Flip the current autostart state."""
        if cls.is_enabled():
            return not cls.disable()
        return cls.enable()
