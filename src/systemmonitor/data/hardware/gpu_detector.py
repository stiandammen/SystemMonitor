"""
GPU Detector Interface
Abstract base class for all GPU detection methods
"""
import time
import logging
from abc import ABC, abstractmethod
from systemmonitor.typing import List, Dict, Any, Optional
from .gpu_info import GPUInfo, GPUVendor, GPUType


class GPUDetector(ABC):
    """Abstract base class for GPU detection methods"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"GPUDetector.{self.name}")
        self._last_scan_time = 0
        self._cache_ttl = 0.5  # Cache results for 0.5 seconds for live updates
        self._cached_results: List[GPUInfo] = []
        self._is_available = False

    @abstractmethod
    def detect(self) -> List[GPUInfo]:
        """
        Detect GPUs using this specific method

        Returns:
            List of GPUInfo objects representing detected GPUs
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this detection method is available on the system

        Returns:
            True if the detector can be used, False otherwise
        """
        pass

    def get_cached_detect(self) -> List[GPUInfo]:
        """
        Get cached detection results if still valid, otherwise detect anew

        Returns:
            List of GPUInfo objects
        """
        current_time = time.time()
        if (current_time - self._last_scan_time) < self._cache_ttl and self._cached_results:
            self.logger.debug(f"Using cached results from {self.name}")
            return self._cached_results.copy()

        if not self.is_available():
            self.logger.debug(f"{self.name} is not available")
            return []

        try:
            self.logger.debug(f"Running detection with {self.name}")
            results = self.detect()
            self._cached_results = results
            self._last_scan_time = current_time

            # Mark which detector found each GPU
            for gpu in results:
                if not gpu.detector_source:
                    gpu.detector_source = self.name

            return results.copy()
        except Exception as e:
            self.logger.error(f"Error in {self.name} detection: {e}", exc_info=True)
            return []

    def clear_cache(self):
        """Clear cached detection results"""
        self._cached_results.clear()
        self._last_scan_time = 0

    def get_detector_info(self) -> Dict[str, Any]:
        """Get information about this detector"""
        return {
            'name': self.name,
            'available': self.is_available(),
            'last_scan': self._last_scan_time,
            'cached_count': len(self._cached_results),
            'cache_ttl': self._cache_ttl
        }
