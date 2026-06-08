"""Data export utilities for SystemMonitor."""
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from PyQt6.QtCore import QObject, pyqtSignal


class DataExporter(QObject):
    """Export system data to various formats."""

    export_completed = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def export_snapshot(self, data: Dict[str, Any], filepath: str, format_type: str):
        """Export a single snapshot of data. format_type: 'csv', 'json', or 'txt'."""
        try:
            fmt = format_type.lower()
            if fmt == 'csv':
                self._export_csv(data, filepath)
            elif fmt == 'json':
                self._export_json(data, filepath)
            elif fmt == 'txt':
                self._export_txt(data, filepath)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            self.export_completed.emit(True, f"Data exported to {filepath}")
        except Exception as e:
            self.export_completed.emit(False, str(e))

    def _export_csv(self, data: Dict[str, Any], filepath: str):
        flat = self._flatten_dict(data)
        with Path(filepath).open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for k, v in flat.items():
                writer.writerow([k, v])

    def _export_json(self, data: Dict[str, Any], filepath: str):
        export_data = {'timestamp': datetime.now().isoformat(), 'data': data}
        with Path(filepath).open('w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)

    def _export_txt(self, data: Dict[str, Any], filepath: str):
        with Path(filepath).open('w', encoding='utf-8') as f:
            f.write('System Monitor Export\n')
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write('=' * 50 + '\n\n')
            self._write_dict_to_txt(f, data, 0)

    def _write_dict_to_txt(self, f, data: Dict[str, Any], indent: int):
        prefix = '  ' * indent
        for key, value in data.items():
            if isinstance(value, dict):
                f.write(f"{prefix}{key}:\n")
                self._write_dict_to_txt(f, value, indent + 1)
            elif isinstance(value, list):
                f.write(f"{prefix}{key}:\n")
                for item in value[:10]:
                    if isinstance(item, dict):
                        self._write_dict_to_txt(f, item, indent + 1)
                        f.write(f"{prefix}  ---\n")
                    else:
                        f.write(f"{prefix}  - {item}\n")
                if len(value) > 10:
                    f.write(f"{prefix}  ... and {len(value) - 10} more\n")
            else:
                f.write(f"{prefix}{key}: {value}\n")

    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key, sep).items())
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]", sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, value))
        return dict(items)
