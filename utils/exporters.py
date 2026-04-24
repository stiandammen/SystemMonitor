"""
Data export utilities
Export system data to CSV, JSON, or TXT formats
"""
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from .constants import ExportFormat
from core.signals import signal_bus


class DataExporter(QObject):
    """Export system data to various formats"""
    
    export_progress = pyqtSignal(int)  # Progress percentage
    export_completed = pyqtSignal(bool, str)  # Success, message
    
    def __init__(self):
        super().__init__()
    
    def export_snapshot(self, data: Dict[str, Any], filepath: str, format_type: str):
        """Export a single snapshot of data"""
        try:
            if format_type == ExportFormat.CSV.value:
                self._export_csv(data, filepath)
            elif format_type == ExportFormat.JSON.value:
                self._export_json(data, filepath)
            elif format_type == ExportFormat.TXT.value:
                self._export_txt(data, filepath)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            self.export_completed.emit(True, f"Exported to {filepath}")
            signal_bus.export_completed.emit(True, f"Exported to {filepath}")
            
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self.export_completed.emit(False, error_msg)
            signal_bus.export_completed.emit(False, error_msg)
    
    def _export_csv(self, data: Dict[str, Any], filepath: str):
        """Export data to CSV format"""
        # Flatten nested dictionaries
        flat_data = self._flatten_dict(data)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for key, value in flat_data.items():
                writer.writerow([key, value])
    
    def _export_json(self, data: Dict[str, Any], filepath: str):
        """Export data to JSON format"""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def _export_txt(self, data: Dict[str, Any], filepath: str):
        """Export data to plain text format"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"System Monitor Export\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            self._write_dict_to_txt(f, data, 0)
    
    def _write_dict_to_txt(self, f, data: Dict[str, Any], indent: int):
        """Recursively write dictionary to text file"""
        prefix = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                f.write(f"{prefix}{key}:\n")
                self._write_dict_to_txt(f, value, indent + 1)
            elif isinstance(value, list):
                f.write(f"{prefix}{key}:\n")
                for item in value[:10]:  # Limit to first 10 items
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
        """Flatten nested dictionary"""
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
    
    def export_processes(self, processes: List[Dict[str, Any]], filepath: str, format_type: str):
        """Export process list"""
        try:
            if format_type == ExportFormat.CSV.value:
                if processes:
                    with open(filepath, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=processes[0].keys())
                        writer.writeheader()
                        writer.writerows(processes)
            
            elif format_type == ExportFormat.JSON.value:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'processes': processes
                    }, f, indent=2, default=str)
            
            elif format_type == ExportFormat.TXT.value:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Process List Export\n")
                    f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total Processes: {len(processes)}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    for proc in processes:
                        for key, value in proc.items():
                            f.write(f"{key}: {value}\n")
                        f.write("-" * 40 + "\n")
            
            self.export_completed.emit(True, f"Exported {len(processes)} processes to {filepath}")
            
        except Exception as e:
            self.export_completed.emit(False, f"Export failed: {str(e)}")
    
    @staticmethod
    def get_default_filename(format_type: str) -> str:
        """Generate default filename with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"system_monitor_{timestamp}.{format_type}"
