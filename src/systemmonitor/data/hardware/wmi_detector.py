"""
WMI-based GPU Detector
Uses Windows Management Instrumentation for GPU detection
"""
import time
import logging
import platform
from typing import List, Dict, Any, Optional
from .gpu_detector import GPUDetector
from .gpu_info import GPUInfo, GPUVendor, GPUType
from systemmonitor.utils.opencl_vram import get_vram_via_opencl


class WMIDetector(GPUDetector):
    """Detect GPUs using Windows Management Instrumentation"""

    def __init__(self):
        super().__init__()
        self._wmi_available = False
        # Don't initialize WMI connection here - do it per detection call for thread safety

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
        """Check if WMI detection is available"""
        self.logger.debug("Checking WMI availability")
        if platform.system() != "Windows":
            self.logger.debug("WMI not available: not Windows")
            return False
        try:
            import wmi
            # Try to create a connection to test availability
            wmi.WMI()
            self.logger.debug("WMI availability check passed")
            return True
        except ImportError:
            self.logger.debug("WMI module not available")
            return False
        except Exception as e:
            self.logger.debug(f"WMI availability check failed: {e}")
            return False

    def detect(self) -> List[GPUInfo]:
        """Detect GPUs using WMI"""
        if not self.is_available():
            return []

        gpus = []
        try:
            # Get thread-safe WMI connection
            wmi_connection = self._get_wmi_connection()
            if not wmi_connection:
                return []

            # Get video controllers
            video_controllers = wmi_connection.Win32_VideoController()

            for controller in video_controllers:
                try:
                    gpu_info = self._parse_video_controller(controller)
                    if gpu_info and gpu_info.name != "Unknown GPU":
                        gpus.append(gpu_info)
                except Exception as e:
                    self.logger.warning(f"Error parsing WMI video controller: {e}")
                    continue

            # Also check for display devices for additional info
            self._enhance_with_display_devices(gpus, wmi_connection)

            self.logger.info(f"WMI detector found {len(gpus)} GPUs")
            return gpus

        except Exception as e:
            self.logger.error(f"Error during WMI detection: {e}", exc_info=True)
            return []

    def _parse_video_controller(self, controller) -> Optional[GPUInfo]:
        """Parse a WMI Win32_VideoController object"""
        try:
            # Basic identification
            name = getattr(controller, 'Name', '') or "Unknown GPU"
            if not name.strip():
                name = "Unknown GPU"

            # Extract vendor from name
            vendor = self._extract_vendor_from_name(name)

            # Device ID
            device_id = getattr(controller, 'DeviceID', '') or ""
            if device_id.startswith("\\\\.\\"):
                device_id = device_id[4:]  # Remove \\.\ prefix

            # VRAM information
            adapter_ram = getattr(controller, 'AdapterRAM', 0) or 0
            vram_total_mb = adapter_ram / (1024 * 1024) if adapter_ram > 0 else 0.0

            # If VRAM from WMI is 0 or unavailable, try to get it via OpenCL
            if vram_total_mb <= 0:
                name = getattr(controller, 'Name', '') or ""
                if name:
                    opencl_vram = get_vram_via_opencl(name)
                    if opencl_vram and opencl_vram > 0:
                        vram_total_mb = opencl_vram
                        self.logger.debug(f"Using OpenCL VRAM for {name}: {vram_total_mb:.0f} MB")

            # Driver version
            driver_version = getattr(controller, 'DriverVersion', '') or "Unknown"
            driver_date = getattr(controller, 'DriverDate', '') or "Unknown"

            # Determine GPU type
            gpu_type = self._determine_gpu_type(controller, name)

            # Create GPU info object
            gpu_info = GPUInfo(
                name=name.strip(),
                vendor=vendor,
                device_id=device_id,
                vram_total_mb=vram_total_mb,
                driver_version=driver_version,
                gpu_type=gpu_type,
                bios_version=getattr(controller, 'BIOSVersion', '') or "Unknown",
                detector_source="WMI"
            )

            # Add PnP ID if available
            pnp_device_id = getattr(controller, 'PNPDeviceID', '') or ""
            if pnp_device_id:
                gpu_info.raw_data['pnp_device_id'] = pnp_device_id

            # Add compatibility info
            compatibility_info = getattr(controller, 'CompatibilityInfo', '') or ""
            if compatibility_info:
                gpu_info.raw_data['compatibility_info'] = compatibility_info

            return gpu_info

        except Exception as e:
            self.logger.warning(f"Error parsing video controller: {e}")
            return None

    def _enhance_with_display_devices(self, gpus: List[GPUInfo], wmi_connection):
        """Enhance GPU info with data from Win32_VideoController and Win32_DisplayConfiguration"""
        try:
            # Get video controller details
            video_ctrls = {}
            for ctrl in wmi_connection.Win32_VideoController():
                if ctrl.DeviceID:
                    key = ctrl.DeviceID.replace("\\\\.\\", "")
                    video_ctrls[key] = ctrl

            # Enhance each GPU with additional info
            for gpu in gpus:
                if gpu.device_id in video_ctrls:
                    ctrl = video_ctrls[gpu.device_id]

                    # Update with additional information
                    if hasattr(ctrl, 'MaxRefreshRate') and ctrl.MaxRefreshRate:
                        gpu.raw_data['max_refresh_rate'] = ctrl.MaxRefreshRate

                    if hasattr(ctrl, 'MinRefreshRate') and ctrl.MinRefreshRate:
                        gpu.raw_data['min_refresh_rate'] = ctrl.MinRefreshRate

                    if hasattr(ctrl, 'MaxResolution') and ctrl.MaxResolution:
                        gpu.max_resolution = str(ctrl.MaxResolution)

                    if hasattr(ctrl, 'Monochrome'):
                        gpu.raw_data['is_monochrome'] = bool(ctrl.Monochrome)

                    if hasattr(ctrl, 'ColorTableEntries'):
                        gpu.raw_data['color_table_entries'] = ctrl.ColorTableEntries

        except Exception as e:
            self.logger.warning(f"Error enhancing with display devices: {e}")

    def _extract_vendor_from_name(self, name: str) -> GPUVendor:
        """Extract vendor from GPU name"""
        if not name:
            return GPUVendor.UNKNOWN

        name_lower = name.lower()

        if any(x in name_lower for x in ['nvidia', 'geforce', 'rtx', 'gtx', 'quadro', 'tesla']):
            return GPUVendor.NVIDIA
        elif any(x in name_lower for x in ['amd', 'radeon', 'rx', 'firepro', 'firegl', 'ati']):
            return GPUVendor.AMD
        elif any(x in name_lower for x in ['intel', 'iris', 'uhd', 'hd graphics']):
            return GPUVendor.INTEL
        elif any(x in name_lower for x in ['qualcomm', 'adreno']):
            return GPUVendor.QUALCOMM
        elif any(x in name_lower for x in ['apple', 'm1', 'm2', 'silicon']):
            return GPUVendor.APPLE
        elif any(x in name_lower for x in ['microsoft', 'hyper-v', 'vmware', 'virtualbox', 'parallels']):
            if 'hyper-v' in name_lower:
                return GPUVendor.MICROSOFT
            elif 'vmware' in name_lower:
                return GPUVendor.VMWARE
            elif 'virtualbox' in name_lower:
                return GPUVendor.MICROSOFT  # VirtualBox often shows as Microsoft
            elif 'parallels' in name_lower:
                return GPUVendor.PARALLELS
            else:
                return GPUVendor.MICROSOFT

        return GPUVendor.UNKNOWN

    def _determine_gpu_type(self, controller, name: str) -> GPUType:
        """Determine if GPU is dedicated, integrated, virtual, etc."""
        name_lower = name.lower() if name else ""

        # Check for virtualization indicators
        virtual_indicators = [
            'virtual', 'vmware', 'virtualbox', 'hyper-v', 'parallels',
            'microsoft basic display adapter', 'std. vga graphics adapter',
            'rdp', 'remote desktop'
        ]

        if any(indicator in name_lower for indicator in virtual_indicators):
            return GPUType.VIRTUAL

        # Check for server/datacenter GPUs
        server_indicators = ['tesla', 'datacenter', 'server', 'firepro s', 'radeon pro']
        if any(indicator in name_lower for indicator in server_indicators):
            return GPUType.SERVER

        # Check for integrated graphics
        integrated_indicators = [
            'intel hd graphics', 'intel iris', 'intel uhd', 'amd Radeon(TM) Graphics',
            'amd graphics', 'integrated graphics', 'graphics'
        ]

        # Some integrated graphics have specific names in WMI
        if any(indicator in name_lower for indicator in integrated_indicators):
            # Additional check: if it's Intel and not a discrete GPU
            if 'intel' in name_lower and not any(disc in name_lower for disc in ['iris xe max', 'iris plus']):
                return GPUType.INTEGRATED

        # Default to dedicated for discrete GPUs
        # We could enhance this with more sophisticated detection
        return GPUType.DEDICATED

    def _get_pci_info(self, device_id: str) -> Dict[str, Any]:
        """Get PCI information for a device"""
        pci_info = {}
        try:
            # Query Win32_PnPEntity for PCI info
            query = f'WHERE DeviceID LIKE "%{device_id}%" AND PNPClass = "Display"'
            pnp_entities = self._wmi_connection.Win32_PnPEntity(query)

            for entity in pnp_entities:
                if hasattr(entity, 'PNPDeviceID'):
                    pnp_id = entity.PNPDeviceID
                    if 'PCI' in pnp_id.upper():
                        # Extract PCI information from PNPDeviceID
                        # Format: PCI\\VEN_xxxx&DEV_xxxx&SUBSYS_xxxx&REV_xx\\...
                        parts = pnp_id.split('&')
                        for part in parts:
                            if part.startswith('VEN_'):
                                pci_info['pci_vendor_id'] = part[4:]
                            elif part.startswith('DEV_'):
                                pci_info['pci_device_id'] = part[4:]
                            elif part.startswith('SUBSYS_'):
                                pci_info['pci_subsystem_id'] = part[7:]
                            elif part.startswith('REV_'):
                                pci_info['pci_revision_id'] = part[4:]

        except Exception as e:
            self.logger.debug(f"Could not get PCI info: {e}")

        return pci_info
