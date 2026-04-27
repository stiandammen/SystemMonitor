"""
Commands module for PowerShell terminal
Håndterer kommando-parsing og -kjøring
Bruker filesystem modulen for navigasjon
"""
import os
from typing import Tuple, Optional

from filesystem import get_filesystem


class CommandHandler:
    """
    Håndterer kommando-kjøring i terminal
    Bruker FileSystem for å håndtere cd og navigasjon
    """

    def __init__(self):
        self._fs = get_filesystem()

    def parse_and_execute(self, command: str) -> Tuple[bool, str]:
        """
        Parse og kjør en kommando

        Args:
            command: Full kommandolinje fra bruker

        Returns:
            (success, output_message)
        """
        if not command.strip():
            return False, ""

        parts = command.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        # Håndter ulike kommandoer
        if cmd == 'cd':
            return self._handle_cd(arg)
        elif cmd in ('dir', 'ls'):
            return self._handle_dir(arg)
        elif cmd == 'pwd':
            return True, self._fs.get_current_path()
        elif cmd in ('clear', 'cls'):
            return self._handle_clear()
        elif cmd == 'drives':
            return self._handle_drives()
        elif cmd == 'exit':
            return False, "exit"
        else:
            return True, ""

    def _handle_cd(self, path: str) -> Tuple[bool, str]:
        """
        Håndter cd kommando

        Args:
            path: Mappen å navigere til

        Returns:
            (success, error_message)
        """
        success, error = self._fs.change_directory(path)
        return success, error if error else ""

    def _handle_dir(self, path: str) -> Tuple[bool, str]:
        """
        Håndter dir/ls kommando

        Args:
            path: Mappe å liste (tom = current)

        Returns:
            (success, listing)
        """
        if not path:
            items = self._fs.list_directory()
        else:
            items = self._fs.list_directory(path)

        if not items:
            return True, "(empty directory)"

        output = []
        for name, is_dir in items:
            if is_dir:
                output.append(f"{name}/")
            else:
                output.append(name)

        return True, "\n".join(output)

    def _handle_clear(self) -> Tuple[bool, str]:
        """Håndter clear/cls kommando"""
        return True, "__clear__"

    def _handle_drives(self) -> Tuple[bool, str]:
        """Håndter drives kommando"""
        drives = self._fs.get_drives()
        if not drives:
            return True, "/"
        return True, "\n".join(drives)

    def get_powershell_command(self, command: str) -> str:
        """
        Konverter en kommando til PowerShell-kommando

        Args:
            command: Brukerens rå input

        Returns:
            PowerShell-kommandoen som skal kjøres
        """
        if not command.strip():
            return ""

        parts = command.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        # cd kommandoer
        if cmd == 'cd':
            if not arg:
                return "Set-Location $HOME"
            return f'Set-Location -LiteralPath "{arg}"'

        # dir/ls kommandoer
        if cmd in ('dir', 'ls'):
            if arg:
                return f'Get-ChildItem -Path "{arg}"'
            return "Get-ChildItem"

        # clear/cls
        if cmd in ('clear', 'cls'):
            return "Clear-Host"

        # pwd
        if cmd == 'pwd':
            return "Get-Location | Select-Object -ExpandProperty Path"

        # For alle andre kommandoer, send direkte
        return command


# Singleton instance
_command_handler = None


def get_command_handler() -> CommandHandler:
    """Hent singleton command handler instance"""
    global _command_handler
    if _command_handler is None:
        _command_handler = CommandHandler()
    return _command_handler