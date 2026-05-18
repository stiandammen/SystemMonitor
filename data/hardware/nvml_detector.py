"""
NVML-based NVIDIA GPU Detector
Uses NVIDIA Management Library for detailed NVIDIA GPU information
"""
import time
import logging
import platform
from typing import List, Dict, Any, Optional
from .gpu_detector import GPUDetector
from .gpu_info import GPUInfo, GPUVendor, GPUType


class NVMLDetector(GPUDetector):
    """Detect NVIDIA GPUs using NVML (NVIDIA Management Library)"""

    def __init__(self):
        super().__init__()
        self._nvml_available = False
        self._nvml_handle = None
        self._device_count = 0
        self._init_nvml()

    def _init_nvml(self):
        """Initialize NVML"""
        try:
            import pynvml
            pynvml.nvmlInit()
            self._nvml = pynvml
            self._nvml_available = True
            self._device_count = self._nvml.nvmlDeviceGetCount()
            self.logger.info(f"NVML initialized successfully - found {self._device_count} NVIDIA GPU(s)")
        except ImportError:
            self.logger.warning("NVML (pynvml) module not available")
            self._nvml_available = False
        except Exception as e:
            self.logger.error(f"Failed to initialize NVML: {e}")
            self._nvml_available = False

    def is_available(self) -> bool:
        """Check if NVML detection is available"""
        return self._nvml_available

    def detect(self) -> List[GPUInfo]:
        """Detect NVIDIA GPUs using NVML"""
        if not self.is_available():
            return []

        gpus = []
        try:
            for i in range(self._device_count):
                try:
                    handle = self._nvml.nvmlDeviceGetHandleByIndex(i)
                    gpu_info = self._parse_nvml_device(handle, i)
                    if gpu_info:
                        gpus.append(gpu_info)
                except Exception as e:
                    self.logger.warning(f"Error parsing NVIDIA GPU {i}: {e}")
                    continue

            self.logger.info(f"NVML detector found {len(gpus)} NVIDIA GPU(s)")
            return gpus

        except Exception as e:
            self.logger.error(f"Error during NVML detection: {e}", exc_info=True)
            return []

    def _parse_nvml_device(self, handle, index: int) -> Optional[GPUInfo]:
        """Parse an NVML device handle"""
        try:
            # Basic identification
            name = self._nvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode('utf-8')

            # Get UUID for persistent identification
            uuid = self._nvml.nvmlDeviceGetUUID(handle)
            if isinstance(uuid, bytes):
                uuid = uuid.decode('utf-8')

            # Get GPU utilization
            try:
                utilization = self._nvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_util = utilization.gpu
                memory_util = utilization.memory
            except:
                gpu_util = 0
                memory_util = 0

            # Get memory information
            try:
                mem_info = self._nvml.nvmlDeviceGetMemoryInfo(handle)
                vram_total_mb = mem_info.total / (1024 * 1024)
                vram_used_mb = mem_info.used / (1024 * 1024)
                vram_free_mb = mem_info.free / (1024 * 1024)
                vram_percent = (vram_used_mb / vram_total_mb * 100) if vram_total_mb > 0 else 0
            except:
                vram_total_mb = vram_used_mb = vram_free_mb = vram_percent = 0

            # Get temperature
            try:
                temp = self._nvml.nvmlDeviceGetTemperature(handle, self._nvml.NVML_TEMPERATURE_GPU)
            except:
                temp = None

            # Get power usage
            try:
                power = self._nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert mW to W
            except:
                power = None

            try:
                power_limit = self._nvml.nvmlDeviceGetPowerManagementLimitConstraints(handle)
                power_limit_watts = power_limit[1] / 1000.0  # Max power limit in W
            except:
                power_limit_watts = None

            # Get fan speed
            try:
                fan_speed = self._nvml.nvmlDeviceGetFanSpeed(handle)
            except:
                fan_speed = None

            # Get clock speeds
            try:
                graphics_clock = self._nvml.nvmlDeviceGetClockInfo(handle, self._nvml.NVML_CLOCK_GRAPHICS)
                mem_clock = self._nvml.nvmlDeviceGetClockInfo(handle, self._nvml.NVML_CLOCK_MEM)
                sm_clock = self._nvml.nvmlDeviceGetClockInfo(handle, self._nvml.NVML_CLOCK_SM)
            except:
                graphics_clock = mem_clock = sm_clock = 0

            # Get compute capabilities
            try:
                # Try to get CUDA cores (this is approximate based on architecture)
                cuda_cores = self._get_cuda_cores_from_name(name)
            except:
                cuda_cores = None

            # Get PCI information
            try:
                pci_info = self._nvml.nvmlDeviceGetPCIInfo(handle)
                pci_bus_id = f"{pci_info.bus:02x}:{pci_info.device:02x}.{pci_info.function:02x}"
            except:
                pci_bus_id = ""

            # Determine GPU type (NVIDIA discrete GPUs are typically dedicated)
            gpu_type = GPUType.DEDICATED
            # Check for virtual GPUs or cloud instances
            if any(x in name.lower() for x in ['tesla t4', 'tesla v100', 'a100', 'grid']):
                gpu_type = GPUType.SERVER

            # Get driver version
            try:
                driver_version = self._nvml.nvmlSystemGetDriverVersion()
                if isinstance(driver_version, bytes):
                    driver_version = driver_version.decode('utf-8')
            except:
                driver_version = "Unknown"

            # Get BIOS version (VBIOS)
            try:
                vbios_version = self._nvml.nvmlDeviceGetVbiosVersion(handle)
                if isinstance(vbios_version, bytes):
                    vbios_version = vbios_version.decode('utf-8')
            except:
                vbios_version = "Unknown"

            # Create GPU info object
            gpu_info = GPUInfo(
                name=name,
                vendor=GPUVendor.NVIDIA,
                device_id=uuid,
                uuid=uuid,
                vram_total_mb=vram_total_mb,
                vram_used_mb=vram_used_mb,
                vram_free_mb=vram_free_mb,
                vram_percent=vram_percent,
                memory_clock_mhz=mem_clock,
                core_clock_mhz=graphics_clock,
                core_clock_boost_mhz=sm_clock,  # Approximation
                gpu_utilization_percent=gpu_util,
                memory_utilization_percent=memory_util,
                temperature_celsius=temp,
                power_draw_watts=power,
                power_limit_watts=power_limit_watts,
                fan_speed_percent=fan_speed,
                driver_version=driver_version,
                bios_version=vbios_version,
                pci_bus=pci_bus_id,
                cuda_cores=cuda_cores,
                gpu_type=gpu_type,
                detector_source="NVML",
                is_available=True
            )

            return gpu_info

        except Exception as e:
            self.logger.error(f"Error parsing NVML device {index}: {e}", exc_info=True)
            return None

    def _get_cuda_cores_from_name(self, name: str) -> Optional[int]:
        """Approximate CUDA cores based on GPU name"""
        name_lower = name.lower()

        # RTX 40 series (Ada Lovelace)
        if '4090' in name_lower:
            return 16384
        elif '4080' in name_lower:
            return 9728
        elif '4070 ti' in name_lower or '4070ti' in name_lower:
            return 7680
        elif '4070' in name_lower:
            return 5888
        elif '4060' in name_lower:
            return 3072
        elif '4050' in name_lower:
            return 2560

        # RTX 30 series (Ampere)
        elif '3090' in name_lower:
            return 10496
        elif '3080' in name_lower:
            return 8704
        elif '3070 ti' in name_lower or '3070ti' in name_lower:
            return 6144
        elif '3070' in name_lower:
            return 5888
        elif '3060 ti' in name_lower or '3060ti' in name_lower:
            return 4864
        elif '3060' in name_lower:
            return 3584
        elif '3050' in name_lower:
            return 2560

        # RTX 20 series (Turing)
        elif '2080 ti' in name_lower or '2080ti' in name_lower:
            return 4352
        elif '2080' in name_lower:
            return 3072
        elif '2070 super' in name_lower or '2070super' in name_lower:
            return 2560
        elif '2070' in name_lower:
            return 2304
        elif '2060 super' in name_lower or '2060super' in name_lower:
            return 2176
        elif '2060' in name_lower:
            return 1920

        # GTX 16 series (Turing)
        elif '1660 ti' in name_lower or '1660ti' in name_lower:
            return 1536
        elif '1660' in name_lower:
            return 1408
        elif '1650 super' in name_lower or '1650super' in name_lower:
            return 1280
        elif '1650' in name_lower:
            return 1024

        # Could add more approximations, but return None for unknown
        return None