"""
Autocomplete module for PowerShell terminal
Håndterer Tab-autocomplete for filer og mapper
Bruker filesystem modulen for å få korrekt cwd
"""
import os
from typing import List, Tuple, Optional

from filesystem import get_filesystem


class AutocompleteEngine:
    """
    Autocomplete engine for file and folder completion
    Bruker FileSystem for å vite gjeldende directory
    """

    def __init__(self):
        self._cache = {}

    def get_completions(self, prefix: str, include_files: bool = True) -> List[str]:
        """
        Finn alle mapper/filer som matcher prefix

        Args:
            prefix: Det brukeren har skrevet (f.eks. "cd t" → "t")
            include_files: Inkluder filer i tillegg til mapper

        Returns:
            Liste med matchende mapper/filer sortert alfabetisk
        """
        fs = get_filesystem()

        if not prefix:
            items = fs.list_directory()
            return self._format_items(items, include_files)

        # Parse path og search pattern
        search_dir, partial = self._parse_prefix(prefix, fs)

        # Finn matcher
        items = fs.list_directory(search_dir)

        # Filtrer på partial match
        filtered = []
        for name, is_dir in items:
            if name.lower().startswith(partial.lower()):
                filtered.append((name, is_dir))

        return self._format_items(filtered, include_files)

    def _parse_prefix(self, prefix: str, fs) -> Tuple[str, str]:
        """
        Parse et prefix og returner (search_dir, partial_name)

        Args:
            prefix: Det brukeren skriver etter "cd "
            fs: FileSystem instans

        Returns:
            (directory_to_search, partial_name_to_match)
        """
        # Normaliser separators
        clean = prefix.replace('/', '\\')

        if not clean:
            return fs.get_current_path(), ""

        if '\\' in clean:
            parts = clean.rsplit('\\', 1)
            if clean.endswith('\\'):
                search_dir = parts[0] if parts[0] else fs.get_current_path()
                return search_dir, ""
            else:
                search_dir = parts[0] if parts[0] else fs.get_current_path()
                partial = parts[1]
                return search_dir, partial
        else:
            return fs.get_current_path(), clean

    def _format_items(self, items: List[Tuple[str, bool]], include_files: bool) -> List[str]:
        """
        Formater items for visning

        Args:
            items: Liste med (navn, er_mappe) tupler
            include_files: Inkluder filer?

        Returns:
            Liste med formaterte strenger
        """
        results = []

        for name, is_dir in items:
            if is_dir:
                results.append(name + '\\')
            elif include_files:
                results.append(name)

        return sorted(results, key=str.lower)

    def clear_cache(self):
        """Fjern autocomplete cache"""
        self._cache = {}


# Singleton instance
_autocomplete_engine = None


def get_autocomplete_engine() -> AutocompleteEngine:
    """Hent singleton autocomplete engine instance"""
    global _autocomplete_engine
    if _autocomplete_engine is None:
        _autocomplete_engine = AutocompleteEngine()
    return _autocomplete_engine