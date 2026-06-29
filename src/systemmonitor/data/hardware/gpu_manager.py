"""
GPU Manager
Orchestrates GPU detection using multiple backends with intelligent fallback
"""
import time
import logging
from systemmonitor.typing_ext import List, Dict, Any, Optional
from .gpu_detector import GPUDetector
from .gpu_info import GPUInfo, GPUVendor, GPUType
from .wmi_detector import WMIDetector
from .nvml_detector import NVMLDetector
from .amd_detector import ADLDetector
from .adl2_detector import ADL2Detector
from .nvidia_smi_detector import NvidiaSMIDetector
from .intel_detector import IntelDetector


class GPUManager:
    """Manages GPU detection using multiple backends with fallback chain"""

    def __init__(self):
        self.logger = logging.getLogger("GPUManager")
        self._detectors: List[GPUDetector] = []
        self._last_scan_time = 0
        self._cache_ttl = 0.5  # Cache results for 0.5 seconds for live updates
        self._cached_gpus: List[GPUInfo] = []
        self._initialized = False

        # Initialize detectors in priority order
        self._initialize_detectors()

    def _initialize_detectors(self):
        """Initialize all detection backends in priority order"""
        try:
            self.logger.info("Initializing GPU detection backends...")

            # Priority 1: NVML (NVIDIA-specific, detailed info)
            nvml_detector = NVMLDetector()
            if nvml_detector.is_available():
                self._detectors.append(nvml_detector)
                self.logger.info("✓ NVML detector initialized")
            else:
                self.logger.warning("✗ NVML detector not available")
                # Fallback: nvidia-smi subprocess (no pynvml required)
                smi_detector = NvidiaSMIDetector()
                if smi_detector.is_available():
                    self._detectors.append(smi_detector)
                    self.logger.info("✓ nvidia-smi fallback detector initialized")
                else:
                    self.logger.warning("✗ nvidia-smi fallback not available")

            # Priority 2: WMI (broad compatibility, good for basic info and fallback)
            wmi_detector = WMIDetector()
            if wmi_detector.is_available():
                self._detectors.append(wmi_detector)
                self.logger.info("✓ WMI detector initialized")
            else:
                self.logger.warning("✗ WMI detector not available")

            # Priority 3: ADL2 (AMD - newer API with comprehensive sensor data)
            adl2_detector = ADL2Detector()
            if adl2_detector.is_available():
                self._detectors.append(adl2_detector)
                self.logger.info("✓ ADL2 detector initialized")
            else:
                self.logger.warning("✗ ADL2 detector not available")

            # Priority 4: ADL (AMD - older API, additional compatibility fallback)
            adl_detector = ADLDetector()
            if adl_detector.is_available():
                self._detectors.append(adl_detector)
                self.logger.info("✓ ADL detector initialized")
            else:
                self.logger.warning("✗ ADL detector not available")

            # Priority 5: Intel detector (WMI-based with Intel-specific enhancements)
            intel_detector = IntelDetector()
            if intel_detector.is_available():
                self._detectors.append(intel_detector)
                self.logger.info("✓ Intel detector initialized")
            else:
                self.logger.warning("✗ Intel detector not available")

            self.logger.info(f"Initialized {len(self._detectors)} GPU detection backends")
            self._initialized = True

        except Exception as e:
            self.logger.error(f"Error initializing GPU detection backends: {e}", exc_info=True)
            self._initialized = False

    def detect_gpus(self) -> List[GPUInfo]:
        """
        Detect all GPUs using available backends with intelligent merging

        Returns:
            List of GPUInfo objects representing all detected GPUs
        """
        if not self._initialized:
            self._initialize_detectors()

        current_time = time.time()
        
        # We periodically force a full re-scan to catch eGPUs/hardware changes
        # while still using the cache for high-frequency calls.
        force_rescan = (current_time - self._last_scan_time) >= 15.0

        if not force_rescan and self._cached_gpus:
            return [gpu.copy() for gpu in self._cached_gpus]

        self.logger.debug("Starting GPU detection across all backends...")
        all_gpus = []

        # Run each detector and collect results
        for detector in self._detectors:
            try:
                self.logger.debug(f"Running {detector.name} detector...")
                start_time = time.time()
                detector_gpus = detector.detect()
                elapsed = time.time() - start_time

                self.logger.debug(f"{detector.name} found {len(detector_gpus)} GPU(s) in {elapsed:.2f}s")

                # Merge results, avoiding duplicates
                for gpu in detector_gpus:
                    if self._is_unique_gpu(gpu, all_gpus):
                        all_gpus.append(gpu)
                    else:
                        # Merge with existing GPU to enhance information
                        self._merge_gpu_info(gpu, all_gpus)

            except Exception as e:
                self.logger.error(f"Error running {detector.name} detector: {e}", exc_info=True)

        # Post-process GPUs to enhance information
        self._post_process_gpus(all_gpus)

        # Cache results
        self._cached_gpus = [gpu.copy() for gpu in all_gpus]
        self._last_scan_time = current_time

        self.logger.info(f"GPU detection complete: found {len(all_gpus)} unique GPU(s)")
        for i, gpu in enumerate(all_gpus):
            self.logger.info(f"  GPU {i+1}: {gpu.name} ({gpu.vendor.value}) - {gpu.vram_total_mb:.0f}MB VRAM")

        return all_gpus

    def _is_unique_gpu(self, gpu: GPUInfo, existing_gpus: List[GPUInfo]) -> bool:
        """Check if a GPU is unique compared to existing list"""
        for existing in existing_gpus:
            # Compare by device ID if available
            if gpu.device_id and existing.device_id:
                if gpu.device_id == existing.device_id:
                    return False

            # Compare by UUID if available
            if gpu.uuid and existing.uuid:
                if gpu.uuid == existing.uuid:
                    return False

            # Compare by name and vendor as fallback
            if (gpu.name.lower() == existing.name.lower() and
                gpu.vendor == existing.vendor):
                # Additional check for VRAM similarity
                if abs(gpu.vram_total_mb - existing.vram_total_mb) < 100:  # Within 100MB
                    return False

        return True

    def _merge_gpu_info(self, new_gpu: GPUInfo, existing_gpus: List[GPUInfo]):
        """Merge new GPU information with existing GPU to enhance data"""
        for existing in existing_gpus:
            # Match by device ID
            if (new_gpu.device_id and existing.device_id and
                new_gpu.device_id == existing.device_id):
                self._merge_gpu_fields(new_gpu, existing)
                return

            # Match by UUID
            if (new_gpu.uuid and existing.uuid and
                new_gpu.uuid == existing.uuid):
                self._merge_gpu_fields(new_gpu, existing)
                return

            # Match by name and vendor
            if (new_gpu.name.lower() == existing.name.lower() and
                new_gpu.vendor == existing.vendor):
                self._merge_gpu_fields(new_gpu, existing)
                return

    def _merge_gpu_fields(self, new_gpu: GPUInfo, existing_gpu: GPUInfo):
        """Merge fields from new GPU into existing GPU, preferring non-empty values"""
        # List of fields to merge - prefer new value if existing is empty/default
        fields_to_merge = [
            'name', 'vram_total_mb', 'vram_used_mb', 'vram_free_mb', 'vram_percent',
            'memory_clock_mhz', 'core_clock_mhz', 'core_clock_boost_mhz',
            'gpu_utilization_percent', 'memory_utilization_percent',
            'temperature_celsius', 'hotspot_temp_celsius', 'memory_temp_celsius',
            'power_draw_watts', 'power_limit_watts', 'fan_speed_percent', 'fan_speed_rpm',
            'driver_version', 'driver_date', 'bios_version',
            'pci_bus', 'pci_generation', 'pci_link_width',
            'cuda_cores', 'opencl_version', 'vulkan_support',
            'max_resolution', 'max_monitors', 'uuid', 'serial_number'
        ]

        for field in fields_to_merge:
            new_value = getattr(new_gpu, field, None)
            existing_value = getattr(existing_gpu, field, None)

            # If existing value is empty/zero/default and new value is meaningful, use new value
            if self._is_better_value(new_value, existing_value, field):
                setattr(existing_gpu, field, new_value)

        # Update detector source to indicate multiple sources
        if new_gpu.detector_source and new_gpu.detector_source not in existing_gpu.detector_source:
            if existing_gpu.detector_source:
                existing_gpu.detector_source += f"+{new_gpu.detector_source}"
            else:
                existing_gpu.detector_source = new_gpu.detector_source

        # Update timestamp
        existing_gpu.last_updated = max(existing_gpu.last_updated, new_gpu.last_updated)

    def _is_better_value(self, new_val, existing_val, field_name: str) -> bool:
        """Determine if new value is better than existing value"""
        if new_val is None:
            return False

        # For numeric fields, 0 or empty might be default
        if isinstance(new_val, (int, float)):
            if existing_val is None:
                return True
            if isinstance(existing_val, (int, float)):
                # For utilization/temperature, higher might be better (more recent reading)
                if field_name in ['gpu_utilization_percent', 'memory_utilization_percent',
                                'temperature_celsius', 'hotspot_temp_celsius', 'memory_temp_celsius',
                                'power_draw_watts', 'fan_speed_percent']:
                    # Prefer non-zero values as they indicate active monitoring
                    if existing_val == 0 and new_val != 0:
                        return True
                    # Otherwise prefer newer/more recent data (hard to determine, so prefer new if significantly different)
                    if abs(new_val - existing_val) > 0.1:  # Significant difference
                        return True
                # For clock speeds, memory sizes, etc. prefer non-zero
                elif field_name in ['vram_total_mb', 'core_clock_mhz', 'memory_clock_mhz']:
                    if existing_val == 0 and new_val > 0:
                        return True
                    # A significantly larger VRAM reading wins: WMI AdapterRAM is a
                    # 32-bit field that caps at ~4 GB; registry-based readers (ADL2)
                    # return the correct 64-bit value for larger cards.
                    if field_name == 'vram_total_mb' and new_val > existing_val * 1.4:
                        return True
                # For most other fields, prefer new if existing is default/zero
                elif existing_val == 0 or existing_val == "" or existing_val is None:
                    return True

        # For string fields, prefer non-empty
        elif isinstance(new_val, str):
            if not existing_val or existing_val.strip() == "":
                return new_val.strip() != ""
            # Prefer longer/more detailed strings
            if len(new_val.strip()) > len(existing_val.strip()):
                return True

        # For boolean fields, prefer True if existing is False
        elif isinstance(new_val, bool):
            if not existing_val and new_val:
                return True

        return False

    def _post_process_gpus(self, gpus: List[GPUInfo]):
        """Post-process GPU list to enhance and validate data"""
        for gpu in gpus:
            # Ensure VRAM values are consistent
            if gpu.vram_total_mb > 0:
                if gpu.vram_used_mb > gpu.vram_total_mb:
                    gpu.vram_used_mb = gpu.vram_total_mb
                if gpu.vram_free_mb > gpu.vram_total_mb:
                    gpu.vram_free_mb = gpu.vram_total_mb
                # Recalculate percentage if needed
                if gpu.vram_total_mb > 0:
                    calculated_percent = (gpu.vram_used_mb / gpu.vram_total_mb) * 100
                    if gpu.vram_percent == 0 or abs(gpu.vram_percent - calculated_percent) > 1:
                        gpu.vram_percent = min(100.0, max(0.0, calculated_percent))

            # Ensure utilization percentages are in valid range
            if gpu.gpu_utilization_percent < 0:
                gpu.gpu_utilization_percent = 0
            elif gpu.gpu_utilization_percent > 100:
                gpu.gpu_utilization_percent = 100

            if gpu.memory_utilization_percent < 0:
                gpu.memory_utilization_percent = 0
            elif gpu.memory_utilization_percent > 100:
                gpu.memory_utilization_percent = 100

            # Set last updated timestamp
            if gpu.last_updated == 0:
                gpu.last_updated = time.time()

    def get_gpu_count(self) -> int:
        """Get the number of detected GPUs"""
        gpus = self.detect_gpus()
        return len(gpus)

    def get_gpu(self, index: int) -> Optional[GPUInfo]:
        """Get a specific GPU by index"""
        gpus = self.detect_gpus()
        if 0 <= index < len(gpus):
            return gpus[index].copy()
        return None

    def get_gpus(self) -> List[GPUInfo]:
        """Get all detected GPUs"""
        gpus = self.detect_gpus()
        return [gpu.copy() for gpu in gpus]

    def clear_cache(self):
        """Clear detection cache"""
        self._cached_gpus.clear()
        self._last_scan_time = 0
        for detector in self._detectors:
            detector.clear_cache()

    def get_detector_status(self) -> Dict[str, Any]:
        """Get status of all detection backends"""
        status = {
            'manager_initialized': self._initialized,
            'detector_count': len(self._detectors),
            'cached_gpu_count': len(self._cached_gpus),
            'cache_age_seconds': time.time() - self._last_scan_time if self._cached_gpus else 0,
            'cache_ttl': self._cache_ttl,
            'detectors': []
        }

        for detector in self._detectors:
            detector_info = detector.get_detector_info()
            status['detectors'].append(detector_info)

        return status
