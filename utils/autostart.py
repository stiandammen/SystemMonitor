"""
Windows autostart management
Handle Windows registry for startup programs
"""
import os
import sys
from pathlib import Path


class AutostartManager:
    """Manage Windows autostart via Registry"""
    
    REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "SystemMonitor"
    
    @staticmethod
    def is_enabled() -> bool:
        """Check if autostart is enabled"""
        if os.name != 'nt':
            return False
        
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AutostartManager.REGISTRY_KEY)
            try:
                value, _ = winreg.QueryValueEx(key, AutostartManager.APP_NAME)
                winreg.CloseKey(key)
                return value is not None
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False
    
    @staticmethod
    def enable() -> bool:
        """Enable autostart"""
        if os.name != 'nt':
            return False
        
        try:
            import winreg
            
            # Get executable path
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                exe_path = sys.executable
            else:
                # Running as script
                exe_path = sys.executable
                script_path = os.path.abspath(sys.argv[0])
                # For Python scripts, we need to use pythonw.exe for silent startup
                pythonw = Path(exe_path).parent / "pythonw.exe"
                if pythonw.exists():
                    exe_path = f'"{pythonw}" "{script_path}"'
                else:
                    exe_path = f'"{exe_path}" "{script_path}"'
            
            # Add to registry
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                AutostartManager.REGISTRY_KEY,
                0,
                winreg.KEY_WRITE
            )
            winreg.SetValueEx(key, AutostartManager.APP_NAME, 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            print(f"Failed to enable autostart: {e}")
            return False
    
    @staticmethod
    def disable() -> bool:
        """Disable autostart"""
        if os.name != 'nt':
            return False
        
        try:
            import winreg
            
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                AutostartManager.REGISTRY_KEY,
                0,
                winreg.KEY_WRITE
            )
            try:
                winreg.DeleteValue(key, AutostartManager.APP_NAME)
            except FileNotFoundError:
                pass  # Already disabled
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            print(f"Failed to disable autostart: {e}")
            return False
    
    @staticmethod
    def toggle() -> bool:
        """Toggle autostart state"""
        if AutostartManager.is_enabled():
            return AutostartManager.disable()
        else:
            return AutostartManager.enable()
