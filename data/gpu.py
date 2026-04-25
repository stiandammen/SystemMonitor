"""
GPU Data Collector
Supports NVIDIA GPUs via NVML, AMD GPUs via ADL, and GPUtil as fallback
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import subprocess
import platform


@dataclass
class GPUInfo:
    """Static GPU information"""
    vendor: str
    name: str
    vram_mb: float
    driver_version: str
    index: int = 0


class GPUCollector:
    """Collect GPU usage and information"""

    def __init__(self):
        self._nvml_available = False
        self._adl_available = False
        self._gputil_available = False
        self._wmi_available = False
        self._gpu_count = 0
        self._gpu_info: Optional[GPUInfo] = None
        self._gpu_device_ids: List[str] = []  # Track GPU device IDs for change detection
        self._gpu_vendor: Optional[str] = None  # Track current GPU vendor
        self._init_backends()

    def _init_backends(self):
        """Initialize GPU backends - tries NVIDIA, AMD, then GPUtil"""
        # Try NVML (NVIDIA Management Library)
        if self._try_nvml():
            return

        # Try ADL (AMD Display Library)
        if self._try_adl():
            return

        # Try GPUtil as fallback (mostly NVIDIA, some AMD support)
        if self._try_gputil():
            return

        # Try WMI as last resort (Windows only, basic info)
        if platform.system() == "Windows":
            if self._try_wmi():
                return

    def _try_nvml(self) -> bool:
        """Try to initialize NVIDIA NVML backend"""
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=FutureWarning)
                import pynvml
            pynvml.nvmlInit()
            self._nvml_available = True
            self._gpu_count = pynvml.nvmlDeviceGetCount()
            self._gpu_device_ids = self._get_nvml_device_ids()
            self._gpu_info = self._detect_nvidia()
            self._gpu_vendor = "NVIDIA"
            return True
        except:
            self._nvml_available = False
            self._gpu_device_ids = []
            return False

    def _try_adl(self) -> bool:
        """Try to initialize AMD ADL backend"""
        try:
            from ctypes import cdll, c_int, c_char_p, pointer, Structure
            import ctypes

            # Try to load ADL library
            adl_lib = None
            if platform.system() == "Windows":
                import os
                windir = os.environ.get("WINDIR", "C:\\Windows")
                adl_path = os.path.join(windir, "System32", "atiadlxx.dll")
                if os.path.exists(adl_path):
                    adl_lib = ctypes.CDLL(adl_path)
                else:
                    adl_path = os.path.join(windir, "System32", "atiadlxy.dll")
                    if os.path.exists(adl_path):
                        adl_lib = ctypes.CDLL(adl_path)

            if adl_lib is None:
                return False

            # ADL basic functions we need
            ADL_OK = 0
            ADL_MAIN_MALLOC = 1

            class ADL_MEMORY_INFO(Structure):
                _fields_ = [
                    ("iSize", c_int),
                    ("iPhysicalMemorySize", c_int),
                ]

            class ADL_GPU_INFO(Structure):
                _fields_ = [
                    ("iSize", c_int),
                    ("iDeviceNumber", c_int),
                    ("iBusNumber", c_int),
                    ("iDeviceNumber", c_int),
                    ("iFunctionNumber", c_int),
                    ("iVendorID", c_int),
                    ("iAdapterID", c_int),
                    ("iExist", c_int),
                    ("strDriverPath", c_char_p),
                    ("strDriverPathExt", c_char_p),
                    ("strUGDriverPath", c_char_p),
                    ("ullOSDisplayMask", ctypes.c_ulonglong),
                ]

            # Simplified ADL detection - check if we can get basic info
            self._adl_available = True
            self._gpu_count = 1  # Assume single GPU unless we detect more
            self._gpu_device_ids = self._get_adl_device_ids()
            self._gpu_info = self._detect_adl()
            self._gpu_vendor = "AMD"
            return True
        except Exception as e:
            self._adl_available = False
            return False

    def _get_adl_device_ids(self) -> List[str]:
        """Get AMD GPU device IDs"""
        ids = []
        try:
            if platform.system() == "Windows":
                # Use PowerShell to get AMD GPU device IDs (VEN_1002 = AMD)
                result = subprocess.run(
                    ["powershell", "-Command",
                     "Get-CimInstance Win32_VideoController | Where-Object { $_.PNPDeviceID -match 'VEN_1002' } | Select-Object -ExpandProperty PNPDeviceID"],
                    capture_output=True, text=True, timeout=10
                )
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        ids.append(line.strip())
        except:
            pass
        return ids

    def _detect_adl(self) -> GPUInfo:
        """Detect AMD GPU info via ADL or WMI"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["powershell", "-Command",
                     "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Csv -NoTypeInformation"],
                    capture_output=True, text=True, timeout=10
                )
                lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
                for line in lines[1:]:  # Skip header
                    parts = line.replace('"', '').split(",")
                    if len(parts) >= 3:
                        name = parts[0].strip()
                        vram = 0
                        driver = parts[2].strip() if len(parts) > 2 else "N/A"
                        if len(parts) > 1 and parts[1].strip():
                            try:
                                vram = int(parts[1].strip()) / (1024**2)  # Convert to MB
                            except:
                                pass
                        if name:
                            return GPUInfo(
                                vendor="AMD",
                                name=name,
                                vram_mb=vram,
                                driver_version=driver,
                                index=0
                            )
        except:
            pass
        return GPUInfo(vendor="AMD", name="AMD GPU", vram_mb=0, driver_version="N/A")

    def _try_gputil(self) -> bool:
        """Try to initialize GPUtil fallback"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus and len(gpus) > 0:
                self._gputil_available = True
                self._gpu_count = len(gpus)
                self._gpu_info = self._detect_gputil()
                self._gpu_vendor = self._extract_vendor(self._gpu_info.name)
                self._gpu_device_ids = [f"gputil-{gpu.id}" for gpu in gpus]
                return True
        except:
            pass
        self._gputil_available = False
        return False

    def _try_wmi(self) -> bool:
        """Try WMI as last resort for basic GPU info"""
        try:
            if platform.system() != "Windows":
                return False

            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Csv -NoTypeInformation"],
                capture_output=True, text=True, timeout=10
            )

            lines = [l.strip().replace('"', '') for l in result.stdout.strip().split("\n") if l.strip()]
            for line in lines[1:]:  # Skip header
                parts = line.split(",")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    vram = 0
                    driver = "N/A"
                    if len(parts) > 1 and parts[1].strip():
                        try:
                            vram = int(parts[1].strip()) / (1024**2)  # Convert to MB
                        except:
                            pass
                    if len(parts) > 2:
                        driver = parts[2].strip()

                    self._wmi_available = True
                    self._gpu_count = 1
                    self._gpu_vendor = self._extract_vendor(name)
                    self._gpu_info = GPUInfo(
                        vendor=self._gpu_vendor or "Unknown",
                        name=name,
                        vram_mb=vram,
                        driver_version=driver,
                        index=0
                    )
                    return True
        except:
            pass
        self._wmi_available = False
        return False

    def _get_nvml_device_ids(self) -> List[str]:
        """Get list of NVIDIA GPU device IDs for change detection"""
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            import pynvml
        ids = []
        try:
            for i in range(pynvml.nvmlDeviceGetCount()):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                uuid = pynvml.nvmlDeviceGetUUID(handle)
                ids.append(uuid)
        except:
            pass
        return ids

    def _hardware_changed(self) -> bool:
        """Check if GPU hardware has changed"""
        if self._nvml_available:
            current_ids = self._get_nvml_device_ids()
            if current_ids != self._gpu_device_ids:
                return True
        elif self._adl_available:
            current_ids = self._get_adl_device_ids()
            if current_ids != self._gpu_device_ids:
                return True
        elif self._wmi_available:
            # WMI doesn't have persistent IDs, so we can't reliably detect changes
            pass
        return False

    def _reinit_if_changed(self):
        """Reinitialize if GPU hardware changed"""
        if self._hardware_changed():
            self._nvml_available = False
            self._adl_available = False
            self._gputil_available = False
            self._wmi_available = False
            self._gpu_count = 0
            self._gpu_info = None
            self._gpu_device_ids = []
            self._gpu_vendor = None
            self._init_backends()

    def _detect_nvidia(self) -> GPUInfo:
        """Detect NVIDIA GPU info via NVML"""
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
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
            return GPUInfo(vendor="NVIDIA", name="NVIDIA GPU", vram_mb=0, driver_version="N/A")

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
        if "nvidia" in name_lower or "geforce" in name_lower or "rtx" in name_lower or "quadro" in name_lower:
            return "NVIDIA"
        elif "amd" in name_lower or "radeon" in name_lower or "ati" in name_lower:
            return "AMD"
        elif "intel" in name_lower:
            return "Intel"
        return "Unknown"

    def is_available(self) -> bool:
        """Check if GPU monitoring is available"""
        return self._nvml_available or self._adl_available or self._gputil_available or self._wmi_available

    def get_info(self) -> GPUInfo:
        """Get static GPU information"""
        if self._gpu_info is None:
            return GPUInfo(vendor="Unknown", name="Unknown GPU", vram_mb=0, driver_version="N/A")
        return self._gpu_info

    def get_vendor(self) -> str:
        """Get current GPU vendor"""
        return self._gpu_vendor or "Unknown"

    def collect(self) -> Dict[str, Any]:
        """Collect GPU data"""
        self._reinit_if_changed()
        if not self.is_available():
            return {'available': False}

        try:
            if self._nvml_available:
                return self._collect_nvml()
            elif self._adl_available:
                return self._collect_adl()
            elif self._gputil_available:
                return self._collect_gputil()
            elif self._wmi_available:
                return self._collect_wmi()
            else:
                return {'available': False}
        except Exception as e:
            print(f"GPU collect error: {e}")
            return {'available': False, 'error': str(e)}

    def _collect_nvml(self) -> Dict[str, Any]:
        """Collect using NVML"""
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
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
            'vendor': 'NVIDIA',
            'load': util.gpu,
            'memory_used': mem.used / (1024**3),
            'memory_total': mem.total / (1024**3),
            'memory_percent': (mem.used / mem.total) * 100 if mem.total > 0 else 0,
            'temperature': temp,
            'power': power,
            'fan_speed': fan,
        }

    def _collect_adl(self) -> Dict[str, Any]:
        """Collect using ADL for AMD GPUs"""
        try:
            info = self._detect_adl()
            return {
                'available': True,
                'name': info.name,
                'vendor': 'AMD',
                'load': None,  # ADL limited info without more complex setup
                'memory_used': None,
                'memory_total': info.vram_mb / 1024 if info.vram_mb else None,
                'memory_percent': None,
                'temperature': None,  # Would need ADL temperature calls
                'power': None,
                'fan_speed': None,
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def _collect_gputil(self) -> Dict[str, Any]:
        """Collect using GPUtil"""
        import GPUtil

        gpus = GPUtil.getGPUs()
        if not gpus:
            return {'available': False}

        gpu = gpus[0]
        vendor = self._extract_vendor(gpu.name)

        return {
            'available': True,
            'name': gpu.name,
            'vendor': vendor,
            'load': gpu.load * 100,
            'memory_used': gpu.memoryUsed / 1024,
            'memory_total': gpu.memoryTotal / 1024,
            'memory_percent': (gpu.memoryUsed / gpu.memoryTotal) * 100 if gpu.memoryTotal > 0 else 0,
            'temperature': gpu.temperature,
            'power': None,
            'fan_speed': None,
        }

    def _collect_wmi(self) -> Dict[str, Any]:
        """Collect basic GPU info via WMI"""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Csv -NoTypeInformation"],
                capture_output=True, text=True, timeout=10
            )
            lines = [l.strip().replace('"', '') for l in result.stdout.strip().split("\n") if l.strip()]
            for line in lines[1:]:  # Skip header
                parts = line.split(",")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    vram = 0
                    if len(parts) > 1 and parts[1].strip():
                        try:
                            vram = int(parts[1].strip()) / (1024**3)  # GB
                        except:
                            pass
                    return {
                        'available': True,
                        'name': name,
                        'vendor': self._extract_vendor(name),
                        'load': None,
                        'memory_used': None,
                        'memory_total': vram,
                        'memory_percent': None,
                        'temperature': None,
                        'power': None,
                        'fan_speed': None,
                    }
        except:
            pass
        return {'available': False}
