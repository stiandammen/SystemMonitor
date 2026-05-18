"""
Intel GPU Detector
Uses WMI and other methods for Intel GPU detection
"""
import time
import logging
import platform
from typing import List, Dict, Any, Optional
from .gpu_detector import GPUDetector
from .gpu_info import GPUInfo, GPUVendor, GPUType


class IntelDetector(GPUDetector):
    """Detect Intel GPUs using WMI and other methods"""

    def __init__(self):
        super().__init__()
        self._wmi_available = False
        self._wmi_connection = None
        self._init_wmi()

    def _init_wmi(self):
        """Initialize WMI connection placeholder"""
        # Don't initialize WMI connection here - do it per detection call for thread safety
        pass

    def _get_wmi_connection(self):
        """Get a thread-safe WMI connection"""
        if platform.system() != "Windows":
            return None

        try:
            import wmi
            return wmi.WMI()
        except ImportError:
            self.logger.debug("WMI module not available")
            return None
        except Exception as e:
            self.logger.debug(f"Failed to create WMI connection: {e}")
            return None

    def is_available(self) -> bool:
        """Check if Intel detection is available"""
        # Basic availability - we can always try WMI on Windows
        if platform.system() != "Windows":
            return False
        try:
            import wmi
            # Try to create a connection to test availability
            wmi.WMI()
            return True
        except ImportError:
            return False
        except Exception:
            return False

    def detect(self) -> List[GPUInfo]:
        """Detect Intel GPUs using WMI"""
        if not self.is_available():
            return []

        gpus = []
        try:
            # Get thread-safe WMI connection
            wmi_connection = self._get_wmi_connection()
            if not wmi_connection:
                return []

            # Get video controllers and filter for Intel
            video_controllers = wmi_connection.Win32_VideoController()

            for controller in video_controllers:
                try:
                    name = getattr(controller, 'Name', '') or ""
                    if not name:
                        continue

                    # Check if this is an Intel GPU
                    name_lower = name.lower()
                    if any(x in name_lower for x in ['intel', 'iris', 'uhd', 'hd graphics']):
                        gpu_info = self._parse_intel_video_controller(controller)
                        if gpu_info:
                            gpus.append(gpu_info)
                except Exception as e:
                    self.logger.warning(f"Error parsing Intel video controller: {e}")
                    continue

            self.logger.info(f"Intel detector found {len(gpus)} Intel GPU(s)")
            return gpus

        except Exception as e:
            self.logger.error(f"Error during Intel detection: {e}", exc_info=True)
            return []

    def _parse_intel_video_controller(self, controller) -> Optional[GPUInfo]:
        """Parse a WMI Win32_VideoController object for Intel GPU"""
        try:
            # Basic identification
            name = getattr(controller, 'Name', '') or "Unknown Intel GPU"
            if not name.strip():
                name = "Unknown Intel GPU"

            # Device ID
            device_id = getattr(controller, 'DeviceID', '') or ""
            if device_id.startswith("\\\\.\\"):
                device_id = device_id[4:]  # Remove \\.\ prefix

            # VRAM information
            adapter_ram = getattr(controller, 'AdapterRAM', 0) or 0
            vram_total_mb = adapter_ram / (1024 * 1024) if adapter_ram > 0 else 0.0

            # Driver version
            driver_version = getattr(controller, 'DriverVersion', '') or "Unknown"
            driver_date = getattr(controller, 'DriverDate', '') or "Unknown"

            # Determine if it's integrated (most Intel GPUs are integrated)
            gpu_type = GPUType.INTEGRATED
            # Some newer Intel discrete GPUs (Arc) might be dedicated
            if any(x in name.lower() for x in ['arc', 'xe-hpg', 'xe2']):
                gpu_type = GPUType.DEDICATED

            # Create GPU info object
            gpu_info = GPUInfo(
                name=name.strip(),
                vendor=GPUVendor.INTEL,
                device_id=device_id,
                vram_total_mb=vram_total_mb,
                driver_version=driver_version,
                gpu_type=gpu_type,
                bios_version=getattr(controller, 'BIOSVersion', '') or "Unknown",
                detector_source="WMI_Intel"
            )

            # Add PnP ID if available
            pnp_device_id = getattr(controller, 'PNPDeviceID', '') or ""
            if pnp_device_id:
                gpu_info.raw_data['pnp_device_id'] = pnp_device_id

            # Try to get more specific Intel information
            self._enhance_intel_info(gpu_info, controller)

            return gpu_info

        except Exception as e:
            self.logger.warning(f"Error parsing Intel video controller: {e}")
            return None

    def _enhance_intel_info(self, gpu_info: GPUInfo, controller):
        """Enhance Intel GPU info with additional details"""
        try:
            # Try to get current clock speeds from WMI performance counters
            # This is limited but we can try
            name = gpu_info.name.lower()

            # Estimate specs based on Intel GPU name patterns
            if 'iris xe' in name or 'iris_xe' in name:
                gpu_info.core_clock_mhz = 1300  # Typical Iris Xe max
                gpu_info.vram_total_mb = max(gpu_info.vram_total_mb, 64)  # Shared memory
            elif 'uhd 630' in name:
                gpu_info.core_clock_mhz = 1200
                gpu_info.vram_total_mb = max(gpu_info.vram_total_mb, 64)
            elif 'uhd 620' in name:
                gpu_info.core_clock_mhz = 1150
                gpu_info.vram_total_mb = max(gpu_info.vram_total_mb, 64)
            elif 'hd 630' in name:
                gpu_info.core_clock_mhz = 1100
                gpu_info.vram_total_mb = max(gpu_info.vram_total_mb, 64)
            elif 'arc' in name:
                # Intel Arc discrete GPUs
                gpu_info.gpu_type = GPUType.DEDICATED
                # Arc specs would need more detailed detection
                if 'a770' in name:
                    gpu_info.core_clock_mhz = 2100
                    gpu_info.vram_total_mb = 16384  # 16GB
                elif 'a750' in name:
                    gpu_info.core_clock_mhz = 2050
                    gpu_info.vram_total_mb = 8192   # 8GB
                elif 'a580' in name:
                    gpu_info.core_clock_mhz = 1900
                    gpu_info.vram_total_mb = 8192   # 8GB
                elif 'a380' in name:
                    gpu_info.core_clock_mhz = 2000
                    gpu_info.vram_total_mb = 6144   # 6GB

            # Try to get driver date in better format
            driver_date = getattr(controller, 'DriverDate', '')
            if driver_date:
                try:
                    # WMI dates come in yyyymmddHHMMSS.mmmmmms+/-zzz format
                    if len(driver_date) >= 8:
                        formatted_date = f"{driver_date[0:4]}-{driver_date[4:6]}-{driver_date[6:8]}"
                        gpu_info.driver_date = formatted_date
                except:
                    gpu_info.driver_date = str(driver_date)

        except Exception as e:
            self.logger.debug(f"Could not enhance Intel info: {e}")
