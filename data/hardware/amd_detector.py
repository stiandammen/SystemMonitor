"""
AMD GPU Detector
Uses AMD ADL and other methods for AMD GPU detection
"""
import time
import logging
import platform
import ctypes
import os
from typing import List, Dict, Any, Optional
from .gpu_detector import GPUDetector
from .gpu_info import GPUInfo, GPUVendor, GPUType


class ADLDetector(GPUDetector):
    """Detect AMD GPUs using AMD Display Library (ADL)"""

    def __init__(self):
        super().__init__()
        self._adl_available = False
        self._adl_lib = None
        self._adl_context = None
        self._init_adl()

    def _init_adl(self):
        """Initialize ADL library"""
        if platform.system() != "Windows":
            self.logger.info("ADL detector only available on Windows")
            return

        try:
            # Try to load ADL library
            windir = os.environ.get("WINDIR", "C:\\Windows")
            adl_path = os.path.join(windir, "System32", "atiadlxx.dll")

            if not os.path.exists(adl_path):
                # Try alternative path
                adl_path = os.path.join(windir, "System32", "atiadlxy.dll")

            if not os.path.exists(adl_path):
                self.logger.warning("ADL library not found")
                self._adl_available = False
                return

            self._adl_lib = ctypes.CDLL(adl_path)
            self.logger.info(f"Loaded ADL library from {adl_path}")

            # Define ADL structures and functions
            self._define_adl_structures()
            self._setup_adl_functions()

            # Initialize ADL
            if self._init_adl_context():
                self._adl_available = True
                self.logger.info("ADL initialized successfully")
            else:
                self.logger.error("Failed to initialize ADL context")
                self._adl_available = False

        except Exception as e:
            self.logger.error(f"Failed to initialize ADL: {e}", exc_info=True)
            self._adl_available = False

    def _define_adl_structures(self):
        """Define ADL structures"""
        try:
            # ADL_Main_Malloc callback type
            self.ADL_MAIN_MALLOC = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_int)

            # ADLTM Temperature
            class ADLTemperature(ctypes.Structure):
                _fields_ = [
                    ("iSize", ctypes.c_int),
                    ("iTemperatureType", ctypes.c_int),
                    ("iTemperature", ctypes.c_int),
                ]
            self.ADLTemperature = ADLTemperature

            # ADLOD5 Current Activity (for usage)
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
            self.ADLOD5CurrentActivity = ADLOD5CurrentActivity

            # ADL Adapter Info
            class ADLAdapterInfo(ctypes.Structure):
                _fields_ = [
                    ("iSize", ctypes.c_int),
                    ("iAdapterIndex", ctypes.c_int),
                    ("udiDeviceID", ctypes.c_ubyte * 8),
                    ("udiVendorID", ctypes.c_ushort),
                    ("udiSubSystemID", ctypes.c_ushort),
                    ("udiSubSystemVendorID", ctypes.c_ushort),
                    ("uiExecOffset", ctypes.c_uint),
                    ("uiAtomBiosOffset", ctypes.c_uint),
                    ("ciDriverNameExt", ctypes.c_char * 32),
                ]
            self.ADLAdapterInfo = ADLAdapterInfo

            # ADL Display DisplayInfo
            class ADLDisplayDisplayInfo(ctypes.Structure):
                _fields_ = [
                    ("iSize", ctypes.c_int),
                    ("iDisplayLogicalIndex", ctypes.c_int),
                    ("iDisplayPhysicalIndex", ctypes.c_int),
                    ("displayName", ctypes.c_char * 32),
                    ("displayOutputName", ctypes.c_char * 32),
                    ("displayOutputMode", ctypes.c_char * 32),
                ]
            self.ADLDisplayDisplayInfo = ADLDisplayDisplayInfo

        except Exception as e:
            self.logger.warning(f"Could not define ADL structures: {e}")

    def _setup_adl_functions(self):
        """Setup ADL function pointers"""
        try:
            # ADL_Main_Control_Create
            self.ADL_Main_Control_Create = getattr(
                self._adl_lib, "ADL_Main_Control_Create", None
            )
            if self.ADL_Main_Control_Create:
                self.ADL_Main_Control_Create.argtypes = [self.ADL_MAIN_MALLOC, ctypes.c_int]
                self.ADL_Main_Control_Create.restype = ctypes.c_int

            # ADL_Adapter_NumberOfAdapters_Get
            self.ADL_Adapter_NumberOfAdapters_Get = getattr(
                self._adl_lib, "ADL_Adapter_NumberOfAdapters_Get", None
            )
            if self.ADL_Adapter_NumberOfAdapters_Get:
                self.ADL_Adapter_NumberOfAdapters_Get.argtypes = [ctypes.POINTER(ctypes.c_int)]
                self.ADL_Adapter_NumberOfAdapters_Get.restype = ctypes.c_int

            # ADL_Adapter_AD2nd_Info_Get
            self.ADL_Adapter_AD2nd_Info_Get = getattr(
                self._adl_lib, "ADL_Adapter_AD2nd_Info_Get", None
            )
            if self.ADL_Adapter_AD2nd_Info_Get:
                self.ADL_Adapter_AD2nd_Info_Get.argtypes = [ctypes.c_int, ctypes.POINTER(self.ADLAdapterInfo)]
                self.ADL_Adapter_AD2nd_Info_Get.restype = ctypes.c_int

            # ADL_Overdrive5_Temperature_Get
            self.ADL_Overdrive5_Temperature_Get = getattr(
                self._adl_lib, "ADL_Overdrive5_Temperature_Get", None
            )
            if self.ADL_Overdrive5_Temperature_Get:
                self.ADL_Overdrive5_Temperature_Get.argtypes = [ctypes.c_int, ctypes.POINTER(self.ADLTemperature)]
                self.ADL_Overdrive5_Temperature_Get.restype = ctypes.c_int

            # ADL_Overdrive6_Temperature_Get (newer)
            self.ADL_Overdrive6_Temperature_Get = getattr(
                self._adl_lib, "ADL_Overdrive6_Temperature_Get", None
            )
            if self.ADL_Overdrive6_Temperature_Get:
                self.ADL_Overdrive6_Temperature_Get.argtypes = [ctypes.c_int, ctypes.POINTER(self.ADLTemperature)]
                self.ADL_Overdrive6_Temperature_Get.restype = ctypes.c_int

            # ADL_Overdrive5_CurrentActivity_Get
            self.ADL_Overdrive5_CurrentActivity_Get = getattr(
                self._adl_lib, "ADL_Overdrive5_CurrentActivity_Get", None
            )
            if self.ADL_Overdrive5_CurrentActivity_Get:
                self.ADL_Overdrive5_CurrentActivity_Get.argtypes = [ctypes.c_int, ctypes.POINTER(self.ADLOD5CurrentActivity)]
                self.ADL_Overdrive5_CurrentActivity_Get.restype = ctypes.c_int

            # ADL_Adapter_Name_Get
            self.ADL_Adapter_Name_Get = getattr(
                self._adl_lib, "ADL_Adapter_Name_Get", None
            )
            if self.ADL_Adapter_Name_Get:
                self.ADL_Adapter_Name_Get.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char)]
                self.ADL_Adapter_Name_Get.restype = ctypes.c_int

            # ADL_Adapter_Active_Get
            self.ADL_Adapter_Active_Get = getattr(
                self._adl_lib, "ADL_Adapter_Active_Get", None
            )
            if self.ADL_Adapter_Active_Get:
                self.ADL_Adapter_Active_Get.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
                self.ADL_Adapter_Active_Get.restype = ctypes.c_int

            # ADL_Adapter_VideoBiosInfo_Get
            self.ADL_Adapter_VideoBiosInfo_Get = getattr(
                self._adl_lib, "ADL_Adapter_VideoBiosInfo_Get", None
            )
            if self.ADL_Adapter_VideoBiosInfo_Get:
                self.ADL_Adapter_VideoBiosInfo_Get.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_ubyte * 256)]
                self.ADL_Adapter_VideoBiosInfo_Get.restype = ctypes.c_int

        except Exception as e:
            self.logger.warning(f"Could not setup ADL functions: {e}")

    def _malloc_callback(self, size):
        """ADL memory allocation callback"""
        try:
            return ctypes.pythonapi.PyMem_Malloc(size)
        except:
            return None

    def _init_adl_context(self) -> bool:
        """Initialize ADL context"""
        try:
            if not self.ADL_Main_Control_Create:
                return False

            # Create malloc callback
            malloc_callback = self.ADL_MAIN_MALLOC(self._malloc_callback)

            # Initialize ADL with enum=1 (try both 0 and 1)
            result = self.ADL_Main_Control_Create(malloc_callback, 1)
            if result != 0:
                result = self.ADL_Main_Control_Create(malloc_callback, 0)
                if result != 0:
                    self.logger.error(f"ADL_Main_Control_Create failed with result {result}")
                    return False

            # Get number of adapters
            adapter_count = ctypes.c_int()
            result = self.ADL_Adapter_NumberOfAdapters_Get(ctypes.byref(adapter_count))
            if result != 0:
                self.logger.error(f"ADL_Adapter_NumberOfAdapters_Get failed with result {result}")
                return False

            self._adapter_count = adapter_count.value
            self.logger.info(f"ADL found {self._adapter_count} AMD adapter(s)")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing ADL context: {e}")
            return False

    def is_available(self) -> bool:
        """Check if ADL detection is available"""
        return self._adl_available and self._adl_lib is not None

    def detect(self) -> List[GPUInfo]:
        """Detect AMD GPUs using ADL"""
        if not self.is_available():
            return []

        gpus = []
        try:
            for i in range(self._adapter_count):
                try:
                    gpu_info = self._parse_adl_adapter(i)
                    if gpu_info:
                        gpus.append(gpu_info)
                except Exception as e:
                    self.logger.warning(f"Error parsing AMD adapter {i}: {e}")
                    continue

            self.logger.info(f"ADL detector found {len(gpus)} AMD GPU(s)")
            return gpus

        except Exception as e:
            self.logger.error(f"Error during ADL detection: {e}", exc_info=True)
            return []

    def _parse_adl_adapter(self, adapter_index: int) -> Optional[GPUInfo]:
        """Parse an ADL adapter"""
        try:
            # Get adapter name
            name_buffer = ctypes.create_string_buffer(256)
            result = self.ADL_Adapter_Name_Get(adapter_index, name_buffer)
            if result != 0:
                self.logger.warning(f"ADL_Adapter_Name_Get failed for adapter {adapter_index}")
                name = b"Unknown AMD GPU"
            else:
                name = name_buffer.value

            if isinstance(name, bytes):
                name = name.decode('utf-8', errors='ignore').strip()
            if not name:
                name = "Unknown AMD GPU"

            # Check if adapter is active
            active = ctypes.c_int()
            result = self.ADL_Adapter_Active_Get(adapter_index, ctypes.byref(active))
            if result != 0 or active.value == 0:
                # Adapter not active, skip or mark as inactive
                pass

            # Get adapter info
            adapter_info = self.ADLAdapterInfo()
            adapter_info.iSize = ctypes.sizeof(self.ADLAdapterInfo)
            result = self.ADL_Adapter_AD2nd_Info_Get(adapter_index, ctypes.byref(adapter_info))
            if result != 0:
                self.logger.warning(f"ADL_Adapter_AD2nd_Info_Get failed for adapter {adapter_index}")

            # Get temperature (try Overdrive6 first, then Overdrive5)
            temperature = None
            try:
                temp_struct = self.ADLTemperature()
                temp_struct.iSize = ctypes.sizeof(self.ADLTemperature)
                temp_struct.iTemperatureType = 0  # GPU Temperature

                # Try Overdrive6 first
                if self.ADL_Overdrive6_Temperature_Get:
                    result = self.ADL_Overdrive6_Temperature_Get(adapter_index, ctypes.byref(temp_struct))
                    if result == 0:
                        temperature = temp_struct.iTemperature / 1000.0  # Convert from millidegrees
                    else:
                        # Try Overdrive5
                        if self.ADL_Overdrive5_Temperature_Get:
                            result = self.ADL_Overdrive5_Temperature_Get(adapter_index, ctypes.byref(temp_struct))
                            if result == 0:
                                temperature = temp_struct.iTemperature / 1000.0
            except:
                pass

            # Get current activity (usage)
            activity_percent = 0
            try:
                activity = self.ADLOD5CurrentActivity()
                activity.iSize = ctypes.sizeof(self.ADLOD5CurrentActivity)
                result = self.ADL_Overdrive5_CurrentActivity_Get(adapter_index, ctypes.byref(activity))
                if result == 0:
                    activity_percent = activity.iActivityPercent
            except:
                pass

            # Get clock speeds
            engine_clock = 0
            memory_clock = 0
            try:
                activity = self.ADLOD5CurrentActivity()
                activity.iSize = ctypes.sizeof(self.ADLOD5CurrentActivity)
                result = self.ADL_Overdrive5_CurrentActivity_Get(adapter_index, ctypes.byref(activity))
                if result == 0:
                    engine_clock = activity.iEngineClock  # in MHz
                    memory_clock = activity.iMemoryClock  # in MHz
            except:
                pass

            # Get VRAM size (approximate from adapter info or other methods)
            vram_mb = 0
            # This is tricky with ADL alone - we might need to combine with WMI

            # Create GPU info object
            gpu_info = GPUInfo(
                name=name,
                vendor=GPUVendor.AMD,
                device_id=f"ADL_{adapter_index}",  # Will enhance with PnP ID later
                vram_total_mb=vram_mb,
                gpu_utilization_percent=float(activity_percent),
                memory_clock_mhz=float(memory_clock),
                core_clock_mhz=float(engine_clock),
                temperature_celsius=temperature,
                gpu_type=GPUType.DEDICATED,  # Assume dedicated, can enhance later
                detector_source="ADL",
                is_available=True
            )

            # Enhance with WMI data for better information
            self._enhance_with_wmi_data(gpu_info, adapter_index)

            return gpu_info

        except Exception as e:
            self.logger.error(f"Error parsing AMD adapter {adapter_index}: {e}", exc_info=True)
            return None

    def _enhance_with_wmi_data(self, gpu_info: GPUInfo, adapter_index: int):
        """Enhance AMD GPU info with WMI data"""
        try:
            import wmi
            wmi_conn = wmi.WMI()

            # Try to match ADL adapter with WMI video controller
            for controller in wmi_conn.Win32_VideoController():
                name = getattr(controller, 'Name', '') or ""
                if gpu_info.name.lower() in name.lower() or any(x in name.lower() for x in ['amd', 'radeon']):
                    # Found potential match, enhance the data
                    adapter_ram = getattr(controller, 'AdapterRAM', 0) or 0
                    if adapter_ram > 0:
                        gpu_info.vram_total_mb = adapter_ram / (1024 * 1024)

                    driver_version = getattr(controller, 'DriverVersion', '') or "Unknown"
                    if driver_version != "Unknown":
                        gpu_info.driver_version = driver_version

                    device_id = getattr(controller, 'DeviceID', '') or ""
                    if device_id:
                        gpu_info.device_id = device_id.replace("\\\\.\\", "")

                    pnp_device_id = getattr(controller, 'PNPDeviceID', '') or ""
                    if pnp_device_id:
                        gpu_info.raw_data['pnp_device_id'] = pnp_device_id

                    break

        except ImportError:
            pass  # WMI not available
        except Exception as e:
            self.logger.debug(f"Could not enhance with WMI data: {e}")
