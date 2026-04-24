"""
GPU Data Collector
Supports NVIDIA GPUs via NVML or GPUtil
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class GPUInfo:
    """Static GPU information"""
    vendor: str
    name: str
    vram_mb: float
    driver_version: str
    index: int = 0


@dataclass
class GPUMetrics:
    """GPU metrics snapshot"""
    load_percent: float
    vram_used_mb: float
    vram_total_mb: float
    power_draw_w: float
    fan_speed_rpm: int
    temperature_c: float


class GPUCollector:
    """Collect GPU usage and information"""

    def __init__(self):
        self._nvml_available = False
        self._gputil_available = False
        self._gpu_count = 0
        self._gpu_info: Optional[GPUInfo] = None
        self._init_backends()

    def _init_backends(self):
        """Initialize GPU backends"""
        # Try NVML (NVIDIA Management Library)
        try:
            import pynvml
            pynvml.nvmlInit()
            self._nvml_available = True
            self._gpu_count = pynvml.nvmlDeviceGetCount()
            self._gpu_info = self._detect_nvidia()
        except:
            pass

        # Try GPUtil as fallback
        if not self._nvml_available:
            try:
                import GPUtil
                self._gputil_available = True
                self._gpu_count = len(GPUtil.getGPUs())
                self._gpu_info = self._detect_gputil()
            except:
                pass

    def _detect_nvidia(self) -> GPUInfo:
        """Detect NVIDIA GPU info via NVML"""
        import pynvml
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            name = pynvml.nvmlDeviceGetName(handle)
            if isinstance(name, bytes):
                name = name.decode('utf-8')
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            driver = pynvml.nvmlSystemGetDriverVersion()
            if isinstance(driver, bytes):
                driver = driver.decode('utf-8')
            return GPUInfo(
                vendor="NVIDIA",
                name=name,
                vram_mb=mem.total / (1024**2),
                driver_version=driver,
                index=0
            )
        except Exception:
            return GPUInfo(vendor="Unknown", name="Unknown GPU", vram_mb=0, driver_version="N/A")

    def _detect_gputil(self) -> GPUInfo:
        """Detect GPU info via GPUtil"""
        import GPUtil
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                return GPUInfo(
                    vendor=self._extract_vendor(gpu.name),
                    name=gpu.name,
                    vram_mb=gpu.memoryTotal,
                    driver_version="N/A"
                )
        except Exception:
            pass
        return GPUInfo(vendor="Unknown", name="Unknown GPU", vram_mb=0, driver_version="N/A")

    def _extract_vendor(self, name: str) -> str:
        """Extract vendor from GPU name"""
        name_lower = name.lower()
        if "nvidia" in name_lower or "geforce" in name_lower or "rtx" in name_lower:
            return "NVIDIA"
        elif "amd" in name_lower or "radeon" in name_lower:
            return "AMD"
        elif "intel" in name_lower:
            return "Intel"
        return "Unknown"

    def is_available(self) -> bool:
        """Check if GPU monitoring is available"""
        return self._nvml_available or self._gputil_available

    def get_info(self) -> GPUInfo:
        """Get static GPU information"""
        if self._gpu_info is None:
            return GPUInfo(vendor="Unknown", name="Unknown GPU", vram_mb=0, driver_version="N/A")
        return self._gpu_info

    def collect(self) -> Dict[str, Any]:
        """Collect GPU data"""
        if not self.is_available():
            return {'available': False}

        try:
            if self._nvml_available:
                return self._collect_nvml()
            elif self._gputil_available:
                return self._collect_gputil()
            else:
                return {'available': False}

        except Exception as e:
            print(f"GPU collect error: {e}")
            return {'available': False, 'error': str(e)}

    def _collect_nvml(self) -> Dict[str, Any]:
        """Collect using NVML"""
        import pynvml

        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode('utf-8')

        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)

        temp = None
        try:
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        except:
            pass

        power = None
        try:
            power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
        except:
            pass

        fan = None
        try:
            fan = pynvml.nvmlDeviceGetFanSpeed(handle)
        except:
            pass

        return {
            'available': True,
            'name': name,
            'load': util.gpu,
            'memory_used': mem.used / (1024**3),
            'memory_total': mem.total / (1024**3),
            'memory_percent': (mem.used / mem.total) * 100 if mem.total > 0 else 0,
            'temperature': temp,
            'power': power,
            'fan_speed': fan,
        }

    def _collect_gputil(self) -> Dict[str, Any]:
        """Collect using GPUtil"""
        import GPUtil

        gpus = GPUtil.getGPUs()
        if not gpus:
            return {'available': False}

        gpu = gpus[0]

        return {
            'available': True,
            'name': gpu.name,
            'load': gpu.load * 100,
            'memory_used': gpu.memoryUsed / 1024,
            'memory_total': gpu.memoryTotal / 1024,
            'memory_percent': (gpu.memoryUsed / gpu.memoryTotal) * 100 if gpu.memoryTotal > 0 else 0,
            'temperature': gpu.temperature,
            'power': None,
            'fan_speed': None,
        }
