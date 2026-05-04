"""
GPU Data Collector
Supports NVIDIA GPUs via NVML, AMD GPUs via ADL, and GPUtil as fallback
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import subprocess
import platform
import ctypes


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
        # Cache for WMI/PowerShell results (avoids expensive subprocess calls)
        self._wmi_cache: Dict[str, Any] = {}
        self._wmi_cache_time: float = 0
        self._wmi_cache_ttl: float = 10.0  # Cache WMI for 10 seconds
        self._init_backends()

    def _get_wmi_command(self, key: str, command: str, force_refresh: bool = False) -> str:
        """Get WMI command result with caching"""
        import time
        now = time.time()
        if not force_refresh and key in self._wmi_cache and (now - self._wmi_cache_time) < self._wmi_cache_ttl:
            return self._wmi_cache[key]
        try:
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout
            self._wmi_cache[key] = output
            self._wmi_cache_time = now
            return output
        except:
            return self._wmi_cache.get(key, "")

    def _init_backends(self):
        """Initialize GPU backends - tries NVIDIA, AMD, then GPUtil"""
        # Try NVML (NVIDIA Management Library)
        if self._try_nvml():
            return

        # Try ADL (AMD Display Library) - also sets up PDH fallback
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
            import ctypes
            import os

            # Try to load ADL library
            windir = os.environ.get("WINDIR", "C:\\Windows")
            adl_path = os.path.join(windir, "System32", "atiadlxx.dll")
            if not os.path.exists(adl_path):
                return False

            adl_lib = ctypes.CDLL(adl_path)

            # Define ADL structures
            class ADLTemperature(ctypes.Structure):
                _fields_ = [
                    ("iSize", ctypes.c_int),
                    ("iTemperatureType", ctypes.c_int),
                    ("iTemperature", ctypes.c_int),
                ]

            class ADLOD5CurrentActivity(ctypes.Structure):
                _fields_ = [
                    ("iSize", ctypes.c_int),
                    ("iEngineClock", ctypes.c_int),
                    ("iMemoryClock", ctypes.c_int),
                    ("iVddc", ctypes.c_int),
                    ("iActivityPercent", ctypes.c_int),
                    ("iCurrentPerformanceLevel", ctypes.c_int),
                    ("iCurrentBusSpeed", ctypes.c_int),
                    ("iCurrentBusLanes", ctypes.c_int),
                    ("iMaxBusLanes", ctypes.c_int),
                    ("iReserved", ctypes.c_int * 8),
                ]

            # ADL_Main_Malloc callback type
            ADL_MAIN_MALLOC = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_int)

            # Get ADL_Main_Control_Create
            adl_main_control_create = getattr(adl_lib, "ADL_Main_Control_Create", None)
            if adl_main_control_create is None:
                return False

            adl_main_control_create.argtypes = [ADL_MAIN_MALLOC, ctypes.c_int]
            adl_main_control_create.restype = ctypes.c_int

            # Create malloc callback
            @ADL_MAIN_MALLOC
            def my_malloc(size):
                import ctypes
                return ctypes.pythonapi.PyMem_Malloc(size)

            # Try to initialize ADL with enum=1 first
            result = adl_main_control_create(my_malloc, 1)
            if result != 0:
                # Try with enum=0
                result = adl_main_control_create(my_malloc, 0)
                if result != 0:
                    return False

            # Get temperature function - try Overdrive6 first as it may work on newer GPUs
            adl_temp_get = getattr(adl_lib, "ADL_Overdrive6_Temperature_Get", None)

            # Get activity function
            adl_activity_get = getattr(adl_lib, "ADL_Overdrive5_CurrentActivity_Get", None)

            # If no temp function, check for other temperature-related functions
            if adl_temp_get is None:
                adl_temp_get = getattr(adl_lib, "ADL_Overdrive5_Temperature_Get", None)

            if adl_temp_get is None and adl_activity_get is None:
                return False

            # Store ADL references for later use
            self._adl_lib = adl_lib
            self._adl_temp_get = adl_temp_get
            self._adl_activity_get = adl_activity_get
            self._ADLTemperature = ADLTemperature
            self._ADLOD5CurrentActivity = ADLOD5CurrentActivity

            self._adl_available = True
            self._gpu_count = 1
            self._gpu_device_ids = self._get_adl_device_ids()
            self._gpu_info = self._detect_adl()
            self._gpu_vendor = "AMD"

            # Try to set up PDH-based fallback for temperature (Windows thermal zone)
            self._init_pdh_fallback()

            return True
        except Exception as e:
            self._adl_available = False
            return False

    def _init_pdh_fallback(self):
        """Initialize PDH-based fallback for GPU metrics on Windows"""
        try:
            import ctypes
            from ctypes import wintypes

            self._pdh_available = False
            self._pdh_query = None
            self._pdh_gpu_counter = None
            self._pdh_temp_counter = None

            pdh = ctypes.windll.pdh

            class PDH_FMT_COUNTERVALUE(ctypes.Structure):
                _fields_ = [
                    ('CStatus', wintypes.DWORD),
                    ('pad', wintypes.DWORD),
                    ('doubleValue', ctypes.c_double),
                ]

            self._PDH_FMT_COUNTERVALUE = PDH_FMT_COUNTERVALUE
            self._PDH_FMT_DOUBLE = 0x00000200

            # Create a persistent query that stays open
            hQuery = ctypes.c_void_p()
            result = pdh.PdhOpenQueryW(None, 0, ctypes.byref(hQuery))
            if result != 0:
                return

            # Store the persistent query handle
            self._pdh_query = hQuery

            # Add GPU utilization counter
            hCounter = ctypes.c_void_p()
            result = pdh.PdhAddCounterW(
                hQuery,
                r'\\GPU Engine(*)\\Utilization Percentage',
                0,
                ctypes.byref(hCounter)
            )
            if result == 0:
                self._pdh_gpu_counter = hCounter

                # Add thermal zone temperature counter
                hTempCounter = ctypes.c_void_p()
                result = pdh.PdhAddCounterW(
                    hQuery,
                    r'\\Temperatursoneinformasjon(*)\\Temperatur',
                    0,
                    ctypes.byref(hTempCounter)
                )
                if result == 0:
                    self._pdh_temp_counter = hTempCounter
                    self._pdh_available = True

                    # Do initial collection
                    pdh.PdhCollectQueryData(self._pdh_query)
                    return

            # Failed, close query
            pdh.PdhCloseQuery(self._pdh_query)
            self._pdh_query = None
        except:
            pass

    def _get_adl_device_ids(self) -> List[str]:
        """Get AMD GPU device IDs"""
        ids = []
        try:
            if platform.system() == "Windows":
                # Use PowerShell to get AMD GPU device IDs (VEN_1002 = AMD) - cached
                output = self._get_wmi_command(
                    "adl_device_ids",
                    "Get-CimInstance Win32_VideoController | Where-Object { $_.PNPDeviceID -match 'VEN_1002' } | Select-Object -ExpandProperty PNPDeviceID"
                )
                for line in output.strip().split("\n"):
                    if line.strip():
                        ids.append(line.strip())
        except:
            pass
        return ids

    def _detect_adl(self) -> GPUInfo:
        """Detect AMD GPU info via ADL or WMI"""
        try:
            if platform.system() == "Windows":
                output = self._get_wmi_command(
                    "adl_detect",
                    "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Csv -NoTypeInformation"
                )
                lines = [l.strip() for l in output.strip().split("\n") if l.strip()]
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

            output = self._get_wmi_command(
                "wmi_basic",
                "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Csv -NoTypeInformation"
            )

            lines = [l.strip().replace('"', '') for l in output.strip().split("\n") if l.strip()]
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

            temp = None
            load = None
            fan = None
            power = None

            # Try to get temperature using ADL Overdrive 5/6
            if hasattr(self, '_adl_temp_get') and self._adl_temp_get:
                try:
                    temp_struct = self._ADLTemperature()
                    temp_struct.iSize = ctypes.sizeof(self._ADLTemperature)
                    temp_struct.iTemperatureType = 0  # 0 = GPU temperature
                    result = self._adl_temp_get(0, ctypes.byref(temp_struct))
                    if result == 0:
                        temp = temp_struct.iTemperature / 1000.0  # Convert from millidegrees
                except:
                    pass

            # Try to get current activity (load, memory, etc.)
            if hasattr(self, '_adl_activity_get') and self._adl_activity_get:
                try:
                    activity = self._ADLOD5CurrentActivity()
                    activity.iSize = ctypes.sizeof(self._ADLOD5CurrentActivity)
                    result = self._adl_activity_get(0, ctypes.byref(activity))
                    if result == 0:
                        load = activity.iActivityPercent
                except:
                    pass

            # Fallback: use PDH for GPU metrics if ADL didn't provide them
            if hasattr(self, '_pdh_available') and self._pdh_available:
                pdh_temp, pdh_load = self._collect_pdh_metrics()
                if temp is None and pdh_temp is not None:
                    temp = pdh_temp
                if load is None and pdh_load is not None:
                    load = pdh_load

            return {
                'available': True,
                'name': info.name,
                'vendor': 'AMD',
                'load': load,
                'memory_used': None,
                'memory_total': info.vram_mb / 1024 if info.vram_mb else None,
                'memory_percent': None,
                'temperature': temp,
                'power': power,
                'fan_speed': fan,
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def _collect_pdh_metrics(self):
        """Collect GPU metrics via PDH (Performance Data Helper)"""
        temp = None
        load = None
        try:
            import ctypes
            from ctypes import wintypes

            pdh = ctypes.windll.pdh

            # Collect query data using persistent handles
            if self._pdh_query:
                pdh.PdhCollectQueryData(self._pdh_query)

            # Get GPU utilization
            if self._pdh_gpu_counter:
                gpu_value = self._PDH_FMT_COUNTERVALUE()
                result = pdh.PdhGetFormattedCounterValue(
                    self._pdh_gpu_counter,
                    self._PDH_FMT_DOUBLE,
                    0,
                    ctypes.byref(gpu_value)
                )
                if result == 0 and gpu_value.CStatus == 0:
                    load = gpu_value.doubleValue

            # Get temperature from thermal zone
            if self._pdh_temp_counter:
                temp_value = self._PDH_FMT_COUNTERVALUE()
                result = pdh.PdhGetFormattedCounterValue(
                    self._pdh_temp_counter,
                    self._PDH_FMT_DOUBLE,
                    0,
                    ctypes.byref(temp_value)
                )
                if result == 0 and temp_value.CStatus == 0:
                    # Temperature is in Kelvin, convert to Celsius
                    temp_kelvin = temp_value.doubleValue
                    if temp_kelvin > 100:  # Reasonable temperature check
                        temp = temp_kelvin - 273.15
        except:
            pass
        return temp, load

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
            output = self._get_wmi_command(
                "wmi_collect",
                "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Csv -NoTypeInformation"
            )
            lines = [l.strip().replace('"', '') for l in output.strip().split("\n") if l.strip()]
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
