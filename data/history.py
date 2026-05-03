"""
Metric History - Ring buffer for time-series data
"""
from collections import deque
from typing import List, Tuple, Optional
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class DataPoint:
    """Single data point with timestamp and value"""
    timestamp: float
    value: float
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.timestamp, self.value)


class MetricHistory(QObject):
    """
    Ring buffer for storing time-series metric data
    Automatically maintains max size by removing oldest entries
    """
    
    data_added = pyqtSignal(str, float, float)  # metric_name, timestamp, value
    
    def __init__(self, max_points: int = 600):
        """
        Initialize metric history
        
        Args:
            max_points: Maximum number of data points to store (default 600 = 5 min @ 500ms)
        """
        super().__init__()
        self._max_points = max_points
        self._buffers: dict[str, deque] = {}
    
    def add_point(self, metric_name: str, timestamp: float, value: float):
        """Add a data point to the specified metric buffer"""
        if metric_name not in self._buffers:
            self._buffers[metric_name] = deque(maxlen=self._max_points)
        
        self._buffers[metric_name].append(DataPoint(timestamp, value))
        self.data_added.emit(metric_name, timestamp, value)
    
    def get_data(self, metric_name: str) -> List[Tuple[float, float]]:
        """Get all data points for a metric as list of (timestamp, value) tuples"""
        if metric_name not in self._buffers:
            return []
        
        return [point.to_tuple() for point in self._buffers[metric_name]]
    
    def get_latest(self, metric_name: str) -> Optional[DataPoint]:
        """Get the most recent data point for a metric"""
        if metric_name not in self._buffers or not self._buffers[metric_name]:
            return None
        
        return self._buffers[metric_name][-1]
    
    def get_latest_value(self, metric_name: str, default: float = 0.0) -> float:
        """Get the most recent value for a metric"""
        latest = self.get_latest(metric_name)
        return latest.value if latest else default
    
    def clear(self, metric_name: Optional[str] = None):
        """Clear history for a specific metric or all metrics"""
        if metric_name:
            if metric_name in self._buffers:
                self._buffers[metric_name].clear()
        else:
            self._buffers.clear()
    
    def get_metrics(self) -> List[str]:
        """Get list of all metric names"""
        return list(self._buffers.keys())
    
    def get_statistics(self, metric_name: str) -> dict:
        """Get statistics for a metric (min, max, avg)"""
        data = self.get_data(metric_name)
        if not data:
            return {'min': 0, 'max': 0, 'avg': 0, 'count': 0}
        
        values = [v for _, v in data]
        return {
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'count': len(values)
        }
