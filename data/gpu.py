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
        self._hwinfo_shm_available = False
        self._wintmp_available = False
        self._wintmp_module = None
        self._gpu_count = 0
        self._gpu_info: Optional[GPUInfo] = None
        self._gpu_device_ids: List[str] = []
        self._gpu_vendor: Optional[str] = None
        self._wmi_cache: Dict[str, Any] = {}
        self._wmi_cache_time: float = 0
        self._wmi_cache_ttl: float = 10.0
        self._adl_info_cache: Optional[GPUInfo] = None
        self._hwinfo_shm_handle = None
        self._hwinfo_shm_mapping = None
        self._initialized = False

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
        # On Windows, try WinTmp first as it provides the most accurate temps
        if platform.system() == "Windows":
            if self._try_wintmp():
                # WinTmp succeeded - but still need to check for better load/memory sources
                pass  # Fall through to check for NVML/ADL for load/memory data

        # Try NVML (NVIDIA Management Library)
        if self._try_nvml():
            # Supplement with WinTmp for better temperature data
            if platform.system() == "Windows":
                self._try_wintmp()
            return

        # Try ADL (AMD Display Library) - also sets up PDH fallback
        if self._try_adl():
            # Supplement with WinTmp for hotspot/memory temp
            if platform.system() == "Windows":
                self._try_wintmp()
            return

        # Try GPUtil as fallback (mostly NVIDIA, some AMD support)
        if self._try_gputil():
            return

        # Try WMI as last resort (Windows only, basic info)
        if platform.system() == "Windows":
            if self._try_wmi():
                return

        # Try HWiNFO shared memory as final fallback (works for any GPU HWiNFO monitors)
        if platform.system() == "Windows":
            if self._try_hwinfo_shm():
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
            self._pdh_gpu_counters = []  # Multiple GPU counters

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

            # Add GPU utilization counter (works reliably)
            hCounter = ctypes.c_void_p()
            result = pdh.PdhAddCounterW(
                hQuery,
                r'\\GPU Engine(*)\\Utilization Percentage',
                0,
                ctypes.byref(hCounter)
            )
            if result == 0:
                self._pdh_gpu_counters.append(hCounter)

            # Add more GPU counters that may be available on AMD GPUs
            # Try AMD-specific perf counters
            amd_counters = [
                (r'\\GPU Adapter ID(*)\\GPU Utilization Percentage', None),
                (r'\\GPU Performance Statistics(*)\\GPU Utilization', None),
                (r'\\GPU Telemetry(*)\\Temperature', None),
                (r'\\GPU Telemetry(*)\\GPU Core Temperature', None),
            ]

            for counter_path, _ in amd_counters:
                try:
                    hCounter = ctypes.c_void_p()
                    result = pdh.PdhAddCounterW(hQuery, counter_path, 0, ctypes.byref(hCounter))
                    if result == 0:
                        self._pdh_gpu_counters.append(hCounter)
                except:
                    pass

            # Try localized temperature counter (Norwegian Windows)
            try:
                hTempCounter = ctypes.c_void_p()
                result = pdh.PdhAddCounterW(
                    hQuery,
                    r'\\Temperatursoneinformasjon(*)\\Temperatur',
                    0,
                    ctypes.byref(hTempCounter)
                )
                if result == 0:
                    self._pdh_temp_counter = hTempCounter
            except:
                pass

            # Try English temperature counter
            try:
                hTempCounter = ctypes.c_void_p()
                result = pdh.PdhAddCounterW(
                    hQuery,
                    r'\\Thermal Zone Information(*)\\Temperature',
                    0,
                    ctypes.byref(hTempCounter)
                )
                if result == 0:
                    self._pdh_temp_counter = hTempCounter
            except:
                pass

            # Collect initial data
            if self._pdh_query:
                pdh.PdhCollectQueryData(self._pdh_query)

            self._pdh_available = True
            return

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
                        wmi_vram = 0
                        driver = parts[2].strip() if len(parts) > 2 else "N/A"
                        if len(parts) > 1 and parts[1].strip():
                            try:
                                wmi_vram = int(parts[1].strip()) / (1024**2)  # Convert to MB
                            except:
                                pass
                        if name:
                            # Correct VRAM for known AMD GPUs where WMI reports wrong value
                            vram = self._correct_amd_vram(name, wmi_vram)
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

    def _correct_amd_vram(self, name: str, wmi_vram_mb: float) -> float:
        """Correct known AMD GPU VRAM values where WMI reports incorrect values"""
        # WMI AdapterRAM often reports wrong values for newer AMD GPUs
        # RX 9070 XT has 16GB but WMI may report ~4GB
        name_lower = name.lower()

        if 'rx 9070 xt' in name_lower or 'rx 9070' in name_lower:
            return 16384  # 16GB for RX 9070 series
        elif 'rx 7900' in name_lower:
            return 24576  # 24GB for RX 7900 series
        elif 'rx 7800' in name_lower or 'rx 7700' in name_lower:
            return 16384  # 16GB for RX 7800/7700 series
        elif 'rx 6900' in name_lower or 'rx 6700' in name_lower:
            return 16384  # 16GB for RX 6900/6700 series

        # Return WMI value if not a known case
        return wmi_vram_mb

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

    def _try_hwinfo_shm(self) -> bool:
        """Try to read GPU data via HWiNFO shared memory"""
        try:
            import ctypes

            # HWiNFO shared memory names (V2 format)
            HWINFO_NAMES = [
                "HWiNFO32_Sens", "HWiNFO64_Sens",
                "HWiNFO32_V2", "HWiNFO64_V2",
                "HWiNFO32_V3", "HWiNFO64_V3",
                "HWiNFO32_V4", "HWiNFO64_V4",
                "HWiNFO32_V5", "HWiNFO64_V5",
                "HWiNFO_SENS_SM2",  # New V2 sensor shared memory
            ]

            kernel32 = ctypes.windll.kernel32
            handle = None
            found_name = None

            for name in HWINFO_NAMES:
                handle = kernel32.OpenFileMappingW(0x0004, False, name)
                if handle:
                    found_name = name
                    break

            if not handle:
                return False

            try:
                mapping = kernel32.MapViewOfFile(handle, 0x0004, 0, 0, 65536)
            finally:
                kernel32.CloseHandle(handle)

            if not mapping:
                return False

            # Read header magic to verify HWiNFO signature
            magic = ctypes.c_uint32()
            ctypes.memmove(ctypes.addressof(magic), mapping, 4)

            # Check for valid HWiNFO magic (little-endian: 'SIWH' = 0x53495748)
            if magic.value not in (0x53495748, 0x48574953):
                kernel32.UnmapViewOfFile(mapping)
                return False

            self._hwinfo_shm_available = True
            self._hwinfo_shm_handle = handle
            self._hwinfo_shm_mapping = mapping
            self._gpu_count = 1

            # Detect GPU info from shared memory or WMI fallback
            self._gpu_info = self._detect_hwinfo_shm() or self._detect_adl() or GPUInfo(
                vendor="AMD", name="AMD GPU (HWiNFO)", vram_mb=0, driver_version="N/A"
            )
            self._gpu_vendor = self._extract_vendor(self._gpu_info.name)

            return True
        except Exception as e:
            self._hwinfo_shm_available = False
            return False

    def _try_wintmp(self) -> bool:
        """Try to initialize WinTmp (LibreHardwareMonitorLib) backend"""
        try:
            import os
            import sys
            import importlib.util

            # Find WinTmp module - look in same directory as this file first
            base_dir = os.path.dirname(os.path.abspath(__file__))
            wintmp_path = os.path.join(base_dir, 'WinTmp')

            if not os.path.isdir(wintmp_path):
                return False

            init_path = os.path.join(wintmp_path, '__init__.py')
            if not os.path.isfile(init_path):
                return False

            # Load module from the specific path
            spec = importlib.util.spec_from_file_location("WinTmp", init_path)
            if spec is None or spec.loader is None:
                return False

            wintmp = importlib.util.module_from_spec(spec)
            sys.modules['WinTmp'] = wintmp
            spec.loader.exec_module(wintmp)

            # Test that it works by calling a function
            _ = wintmp.GPU_Temp()

            self._wintmp_available = True
            self._wintmp_module = wintmp
            return True
        except Exception as e:
            self._wintmp_available = False
            self._wintmp_module = None
            return False

    def _get_wintmp_temps(self) -> tuple:
        """Get GPU temperatures from WinTmp module.

        Returns:
            tuple: (core_temp, hotspot_temp, memory_temp)
        """
        temp = None
        hotspot_temp = None
        memory_temp = None

        try:
            if hasattr(self, '_wintmp_module') and self._wintmp_module:
                all_temps = self._wintmp_module._all_temps()
                for key, val in all_temps.items():
                    if val is None:
                        continue
                    if "GPU Core" in key or "GPU Temperature" in key:
                        if temp is None:
                            temp = val
                    elif "Hot Spot" in key or "GPU Hot Spot" in key:
                        if hotspot_temp is None:
                            hotspot_temp = val
                    elif "GPU Memory" in key or "Memory Temperature" in key:
                        if memory_temp is None:
                            memory_temp = val
        except Exception:
            pass

        return temp, hotspot_temp, memory_temp

    def _collect_via_perf_counters(self) -> Dict[str, Any]:
        """Collect GPU metrics via Windows Performance Counters.

        Returns:
            dict: Contains 'load', 'memory_used', 'memory_total', 'memory_percent'
        """
        result = {
            'load': None,
            'memory_used': None,
            'memory_total': None,
            'memory_percent': None
        }

        try:
            output = self._get_wmi_command(
                "perf_counters_load",
                """Get-CimInstance Win32_PerfFormattedData_GpuPerformanceCounters_GpuEngine |
                    Where-Object { $_.Name -match 'engtype_3D' } |
                    Select-Object -First 1 |
                    ForEach-Object { $_.UtilizationPercentage }"""
            )
            if output.strip():
                try:
                    result['load'] = float(output.strip())
                except ValueError:
                    pass
        except:
            pass

        # Get dedicated memory usage
        try:
            output = self._get_wmi_command(
                "perf_counters_mem",
                """Get-CimInstance Win32_PerfFormattedData_GpuPerformanceCounters_GpuAdapterMemory |
                    Select-Object -First 1 |
                    ForEach-Object { $_.DedicatedUsage }"""
            )
            if output.strip():
                try:
                    result['memory_used'] = float(output.strip()) / (1024**3)  # Convert to GB
                except ValueError:
                    pass
        except:
            pass

        return result

    def _detect_hwinfo_shm(self) -> Optional[GPUInfo]:
        """Detect GPU info from HWiNFO shared memory"""
        try:
            entries = self._read_hwinfo_entries()
            for entry in entries:
                # Look for GPU-related sensors
                name_lower = entry.get('name', '').lower()
                if any(x in name_lower for x in ['gpu', 'radeon', 'rx 9070', 'graphics']):
                    return GPUInfo(
                        vendor="AMD",
                        name=entry.get('name', 'AMD GPU'),
                        vram_mb=0,  # Would need to find VRAM entry
                        driver_version="N/A",
                        index=0
                    )
        except:
            pass
        return None

    def _read_hwinfo_entries(self) -> List[Dict]:
        """Read all sensor entries from HWiNFO shared memory"""
        entries = []
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            mapping = self._hwinfo_shm_mapping
            if not mapping:
                return entries

            # Read header
            class HWiNFOHeader(ctypes.Structure):
                _fields_ = [
                    ("magic", ctypes.c_uint32),
                    ("version", ctypes.c_uint32),
                    ("version2", ctypes.c_uint32),
                    ("last_update", ctypes.c_int64),
                    ("sensor_offset", ctypes.c_uint32),
                    ("sensor_size", ctypes.c_uint32),
                    ("sensor_count", ctypes.c_uint32),
                    ("entry_offset", ctypes.c_uint32),
                    ("entry_size", ctypes.c_uint32),
                    ("entry_count", ctypes.c_uint32),
                ]

            header = HWiNFOHeader()
            ctypes.memmove(ctypes.addressof(header), mapping, ctypes.sizeof(HWiNFOHeader))

            if header.magic not in (0x53495748, 0x48574953):
                return entries

            # Sensor type enum values
            SENSOR_TEMPERATURE = 1

            # Read entries
            entry_start = mapping + header.entry_offset
            for i in range(min(header.entry_count, 256)):  # Limit to 256 entries
                try:
                    entry_base = entry_start + (i * header.entry_size)
                    sensor_index = ctypes.c_uint32()
                    entry_type = ctypes.c_uint32()
                    name_buf = ctypes.create_string_buffer(128)
                    value = ctypes.c_double()

                    # Read sensor_index at offset 4
                    ctypes.memmove(ctypes.addressof(sensor_index), entry_base + 4, 4)
                    # Read type at offset 0
                    ctypes.memmove(ctypes.addressof(entry_type), entry_base, 4)
                    # Read name at offset 12 (128 bytes)
                    ctypes.memmove(name_buf, entry_base + 12, 128)
                    # Read value at offset 152
                    ctypes.memmove(ctypes.addressof(value), entry_base + 152, 8)

                    name = name_buf.value.decode('utf-8', errors='ignore').rstrip('\x00')

                    if entry_type.value == SENSOR_TEMPERATURE and value.value > 0:
                        entries.append({
                            'sensor_index': sensor_index.value,
                            'type': 'Temperature',
                            'name': name,
                            'value': value.value,
                        })
                except Exception:
                    continue

        except Exception:
            pass
        return entries

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
            self._hwinfo_shm_available = False
            self._wintmp_available = False
            self._wintmp_module = None
            if self._hwinfo_shm_mapping:
                try:
                    import ctypes
                    ctypes.windll.kernel32.UnmapViewOfFile(self._hwinfo_shm_mapping)
                except:
                    pass
                self._hwinfo_shm_mapping = None
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
        if not self._initialized:
            return False
        return self._nvml_available or self._adl_available or self._gputil_available or self._wmi_available or self._hwinfo_shm_available or self._wintmp_available

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
        # Lazy initialization on first collect - avoids blocking startup
        if not self._initialized:
            self._init_backends()
            self._initialized = True

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
            elif self._hwinfo_shm_available:
                return self._collect_hwinfo_shm()
            elif self._wintmp_available:
                return self._collect_wintmp()
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

        # Try to get hotspot and memory temp from WinTmp if available
        hotspot_temp = None
        memory_temp = None
        if self._wintmp_available:
            temp, hotspot_temp, memory_temp = self._get_wintmp_temps()
            if temp is not None and temp > 0:
                temp = temp  # Keep NVML temp if already set

        return {
            'available': True,
            'name': name,
            'vendor': 'NVIDIA',
            'load': util.gpu,
            'memory_used': mem.used / (1024**3),
            'memory_total': mem.total / (1024**3),
            'memory_percent': (mem.used / mem.total) * 100 if mem.total > 0 else 0,
            'temperature': temp,
            'hotspot_temp': hotspot_temp,
            'memory_temp': memory_temp,
            'power': power,
            'fan_speed': fan,
        }

    def _collect_adl(self) -> Dict[str, Any]:
        """Collect using ADL for AMD GPUs"""
        try:
            # Use cached info if available, only detect once
            if self._adl_info_cache is None:
                self._adl_info_cache = self._detect_adl()
            info = self._adl_info_cache

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

            # Try PDH metrics as fallback
            pdh_temp, pdh_load = self._collect_pdh_metrics()
            if temp is None and pdh_temp is not None:
                temp = pdh_temp
            if load is None and pdh_load is not None:
                load = pdh_load

            # Try WMI as fallback for AMD GPU metrics (better for newer GPUs)
            if temp is None or load is None:
                wmi_temp, wmi_load = self._get_wmi_gpu_metrics()
                if temp is None and wmi_temp is not None:
                    temp = wmi_temp
                if load is None and wmi_load is not None:
                    load = wmi_load

            # Try WinTmp for better temperature data (includes hotspot and memory temp)
            hotspot_temp = None
            memory_temp = None
            if self._wintmp_available:
                wintmp_temp, hotspot_temp, memory_temp = self._get_wintmp_temps()
                if temp is None and wintmp_temp is not None:
                    temp = wintmp_temp

            return {
                'available': True,
                'name': info.name,
                'vendor': 'AMD',
                'load': load,
                'memory_used': None,
                'memory_total': info.vram_mb / 1024 if info.vram_mb else None,
                'memory_percent': None,
                'temperature': temp,
                'hotspot_temp': hotspot_temp,
                'memory_temp': memory_temp,
                'power': power,
                'fan_speed': fan,
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def _get_wmi_gpu_metrics(self):
        """Get GPU metrics via WMI - more reliable for newer AMD GPUs"""
        temp = None
        load = None
        try:
            output = self._get_wmi_command(
                "wmi_gpu_metrics",
                """Get-CimInstance Win32_PerfFormattedData_GpuPerformanceCounters_GpuEngine |
                    Where-Object { $_.Name -match '0' } |
                    Select-Object -First 1 |
                    ForEach-Object { $_.UtilizationPercentage }"""
            )
            if output.strip():
                try:
                    load = float(output.strip())
                except ValueError:
                    pass
        except:
            pass

        # Try thermal counter via WMI
        try:
            output = self._get_wmi_command(
                "wmi_gpu_temp",
                """Get-CimInstance MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue |
                    Select-Object -First 1 |
                    ForEach-Object { $_.CurrentTemperature }"""
            )
            if output.strip():
                try:
                    temp_k = float(output.strip())
                    temp = temp_k / 10 - 273.15
                except ValueError:
                    pass
        except:
            pass

        return temp, load

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

            # Get GPU utilization from all GPU counters
            for counter in self._pdh_gpu_counters:
                if counter:
                    try:
                        gpu_value = self._PDH_FMT_COUNTERVALUE()
                        result = pdh.PdhGetFormattedCounterValue(
                            counter,
                            self._PDH_FMT_DOUBLE,
                            0,
                            ctypes.byref(gpu_value)
                        )
                        if result == 0 and gpu_value.CStatus == 0 and 0 <= gpu_value.doubleValue <= 100:
                            load = gpu_value.doubleValue
                            break  # Got valid load
                    except:
                        continue

            # Get temperature from thermal zone
            if self._pdh_temp_counter:
                try:
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
            'hotspot_temp': None,
            'memory_temp': None,
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

                    # Try to get load via perf counters
                    load = None
                    perf_data = self._collect_via_perf_counters()
                    load = perf_data.get('load')

                    # Try to get temps via WinTmp if available
                    temp = None
                    hotspot_temp = None
                    memory_temp = None
                    if self._wintmp_available:
                        temp, hotspot_temp, memory_temp = self._get_wintmp_temps()

                    return {
                        'available': True,
                        'name': name,
                        'vendor': self._extract_vendor(name),
                        'load': load,
                        'memory_used': None,
                        'memory_total': vram,
                        'memory_percent': None,
                        'temperature': temp,
                        'hotspot_temp': hotspot_temp,
                        'memory_temp': memory_temp,
                        'power': None,
                        'fan_speed': None,
                    }
        except:
            pass
        return {'available': False}

    def _collect_hwinfo_shm(self) -> Dict[str, Any]:
        """Collect GPU metrics via HWiNFO shared memory"""
        try:
            entries = self._read_hwinfo_entries()

            # Find GPU temperature (look for common GPU temp sensor names)
            gpu_temp = None
            gpu_load = None
            gpu_power = None
            gpu_fan = None

            for entry in entries:
                name_lower = entry.get('name', '').lower()
                value = entry.get('value', 0)

                # GPU temperature sensors (various naming conventions)
                if any(x in name_lower for x in ['gpu temp', 'gpu temperature', 'hotspot', 'junction']):
                    if 'hotspot' in name_lower or 'junction' in name_lower:
                        if gpu_temp is None:
                            gpu_temp = value
                    elif 30 < value < 110:  # Reasonable GPU temp range
                        gpu_temp = value

                # GPU load/usage
                elif any(x in name_lower for x in ['gpu load', 'gpu usage', 'gpu utilization', 'engine']):
                    if 0 <= value <= 100:
                        gpu_load = value

                # GPU power
                elif any(x in name_lower for x in ['gpu power', 'total board power', 'board power']):
                    if 0 < value < 500:
                        gpu_power = value

                # GPU fan
                elif any(x in name_lower for x in ['fan', 'fan speed']):
                    if 0 <= value <= 100:
                        gpu_fan = value

            # If we didn't find specific GPU temp, try first temperature entry
            if gpu_temp is None:
                for entry in entries:
                    if entry.get('type') == 'Temperature' and 30 < entry.get('value', 0) < 110:
                        gpu_temp = entry.get('value')
                        break

            return {
                'available': True,
                'name': self._gpu_info.name if self._gpu_info else 'AMD GPU (HWiNFO)',
                'vendor': 'AMD',
                'load': gpu_load,
                'memory_used': None,
                'memory_total': self._gpu_info.vram_mb / 1024 if self._gpu_info and self._gpu_info.vram_mb else None,
                'memory_percent': None,
                'temperature': gpu_temp,
                'hotspot_temp': None,
                'memory_temp': None,
                'power': gpu_power,
                'fan_speed': gpu_fan,
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def _collect_wintmp(self) -> Dict[str, Any]:
        """Collect GPU data purely via WinTmp/LibreHardwareMonitorLib"""
        try:
            # Get temperatures from WinTmp
            temp, hotspot_temp, memory_temp = self._get_wintmp_temps()

            # Get load and memory via perf counters
            perf_data = self._collect_via_perf_counters()

            # Detect GPU info from WMI since WinTmp doesn't provide it
            info = self._detect_wintmp_info()

            return {
                'available': True,
                'name': info.name if info else 'GPU',
                'vendor': info.vendor if info else 'Unknown',
                'load': perf_data.get('load'),
                'memory_used': perf_data.get('memory_used'),
                'memory_total': perf_data.get('memory_total'),
                'memory_percent': perf_data.get('memory_percent'),
                'temperature': temp,
                'hotspot_temp': hotspot_temp,
                'memory_temp': memory_temp,
                'power': None,
                'fan_speed': None,
            }
        except Exception as e:
            return {'available': False, 'error': str(e)}

    def _detect_wintmp_info(self) -> Optional[GPUInfo]:
        """Detect GPU info via WMI for WinTmp standalone mode"""
        try:
            output = self._get_wmi_command(
                "wintmp_detect",
                "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Csv -NoTypeInformation"
            )
            lines = [l.strip().replace('"', '') for l in output.strip().split("\n") if l.strip()]
            for line in lines[1:]:  # Skip header
                parts = line.split(",")
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
                            vendor=self._extract_vendor(name),
                            name=name,
                            vram_mb=vram,
                            driver_version=driver,
                            index=0
                        )
        except:
            pass
        return None

    def __del__(self):
        """Cleanup shared memory mapping"""
        try:
            if self._hwinfo_shm_mapping:
                import ctypes
                ctypes.windll.kernel32.UnmapViewOfFile(self._hwinfo_shm_mapping)
        except:
            pass
