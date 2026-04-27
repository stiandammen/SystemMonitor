"""
Filesystem module for PowerShell terminal
Håndterer cwd, diskbytte, path parsing og navigasjon
"""
import os
import platform
from typing import Optional, List, Tuple


class FileSystem:
    """
    Håndterer filsystem-navigasjon med støtte for:
    - cd kommandoer (relativ og absolutt)
    - Diskbytte (Windows)
    - Path parsing og validering
    """

    def __init__(self):
        self._current_path = os.path.expanduser("~")
        self._disk_paths = {}  # Lagrer cwd per disk på Windows
        self._initialize_filesystem()

    def _initialize_filesystem(self):
        """Initialiser filsystem med riktig startsti"""
        if platform.system() == "Windows":
            self._current_path = os.path.expanduser("~")
            disk = self._get_disk_letter(self._current_path)
            self._disk_paths[disk] = self._current_path
        else:
            self._current_path = os.path.expanduser("~")

    def _get_disk_letter(self, path: str) -> str:
        """Hent diskbokstav fra en path på Windows"""
        if platform.system() == "Windows" and len(path) >= 2:
            return path[0].upper()
        return ""

    def get_current_path(self) -> str:
        """Hent nåværende arbeidsmappe"""
        return self._current_path

    def get_current_directory_name(self) -> str:
        """Hent bare mappenavnet til nåværende path"""
        return os.path.basename(self._current_path)

    def change_directory(self, path: str) -> Tuple[bool, str]:
        """
        Endre nåværende mappe

        Args:
            path: Mappen å navigere til

        Returns:
            (success, message)
        """
        if not path or path.strip() == "":
            return self._go_home()

        path = path.strip()
        original_path = path

        # Håndter Windows diskbytte (f.eks. C: → C:\)
        if platform.system() == "Windows" and len(path) == 2 and path[1] == ':':
            path = path[0] + ":\\"

        # Parse og valider path
        new_path, error = self._resolve_path(path)

        if error:
            return False, error

        # Sjekk at path eksisterer
        if not os.path.isdir(new_path):
            return False, "Path not found: " + original_path

        # Sjekk tilgang
        if not os.access(new_path, os.R_OK):
            return False, "Access denied: " + original_path

        # Oppdater current path
        if platform.system() == "Windows":
            disk = self._get_disk_letter(new_path)
            if disk:
                self._disk_paths[disk] = new_path
                self._current_path = new_path
            else:
                self._current_path = new_path
        else:
            self._current_path = new_path

        # Oppdater faktisk cwd for prosessen
        try:
            os.chdir(self._current_path)
        except:
            pass

        return True, ""

    def _resolve_path(self, path: str) -> Tuple[str, str]:
        """
        Resolve en path til absolutt path

        Args:
            path: Relative eller absolutte path

        Returns:
            (resolved_path, error_message)
        """
        # Normaliser path separators
        path = path.replace('/', '\\')

        # Håndter absolutte paths på Windows (C:\...)
        if platform.system() == "Windows":
            if len(path) >= 2 and path[1] == ':':
                if len(path) == 2:
                    path = path + '\\'
                return os.path.abspath(path), ""

        # Håndter root på Windows
        if platform.system() == "Windows" and path == '\\':
            disk = self._get_disk_letter(self._current_path)
            if disk:
                return disk + ":\\", ""

        # Håndter ..
        if path == "..":
            parent = os.path.dirname(self._current_path)
            if platform.system() == "Windows":
                if len(parent) >= 2 and parent[1] == ':':
                    return parent, ""
            if parent == self._current_path:
                return self._current_path, ""
            return parent, ""

        # Håndter .
        if path == ".":
            return self._current_path, ""

        # Bygg absolutt path fra current
        if not os.path.isabs(path):
            path = os.path.join(self._current_path, path)

        # Normaliser (fjern .. og .)
        abs_path = os.path.normpath(path)

        return abs_path, ""

    def _go_home(self) -> Tuple[bool, str]:
        """Gå til brukerens hjemmemappe"""
        self._current_path = os.path.expanduser("~")
        try:
            os.chdir(self._current_path)
        except:
            pass
        return True, ""

    def get_drives(self) -> List[str]:
        """
        Hent liste over tilgjengelige disker (kun Windows)

        Returns:
            Liste med diskbokstaver, f.eks. ['C', 'D', 'E']
        """
        if platform.system() != "Windows":
            return ["/"]

        drives = []

        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            path = letter + ":\\"
            if os.path.isdir(path):
                drives.append(letter + ":")

        return drives

    def list_directory(self, path: str = "") -> List[Tuple[str, bool]]:
        """
        List innholdet i en mappe

        Args:
            path: Mappe å liste (tom = nåværende mappe)

        Returns:
            Liste med (navn, er_mappe) tupler
        """
        if not path:
            list_path = self._current_path
        else:
            resolved, _ = self._resolve_path(path)
            if os.path.isdir(resolved):
                list_path = resolved
            else:
                list_path = self._current_path

        items = []
        try:
            for item in os.listdir(list_path):
                full_path = os.path.join(list_path, item)
                is_dir = os.path.isdir(full_path)
                items.append((item, is_dir))
        except:
            pass

        # Sorter: mapper først, deretter alfabetisk
        items.sort(key=lambda x: (not x[1], x[0].lower()))
        return items

    def path_exists(self, path: str) -> bool:
        """Sjekk om en path eksisterer"""
        resolved, _ = self._resolve_path(path)
        return os.path.exists(resolved)

    def is_directory(self, path: str) -> bool:
        """Sjekk om en path er en mappe"""
        resolved, _ = self._resolve_path(path)
        return os.path.isdir(resolved)


# Singleton instance
_filesystem = None


def get_filesystem() -> FileSystem:
    """Hent singleton filesystem instance"""
    global _filesystem
    if _filesystem is None:
        _filesystem = FileSystem()
    return _filesystem