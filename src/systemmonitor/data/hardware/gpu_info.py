"""
Enhanced GPU Information Data Class
Contains comprehensive information about GPUs
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class GPUType(Enum):
    """Types of GPUs"""
    DEDICATED = "Dedicated"
    INTEGRATED = "Integrated"
    VIRTUAL = "Virtual"
    EXTERNAL = "External"
    SERVER = "Server"
    HYBRID = "Hybrid"
    UNKNOWN = "Unknown"


class GPUVendor(Enum):
    """GPU Vendors"""
    NVIDIA = "NVIDIA"
    AMD = "AMD"
    INTEL = "Intel"
    QUALCOMM = "Qualcomm"
    APPLE = "Apple"
    MICROSOFT = "Microsoft"  # For Hyper-V/VirtualBox
    VMWARE = "VMware"
    PARALLELS = "Parallels"
    UNKNOWN = "Unknown"


@dataclass
class GPUInfo:
    """Comprehensive GPU information"""
    # Basic Identification
    name: str = "Unknown GPU"
    vendor: GPUVendor = GPUVendor.UNKNOWN
    device_id: str = ""
    subsystem_id: str = ""
    revision: str = ""

    # Hardware Information
    gpu_type: GPUType = GPUType.UNKNOWN
    architecture: str = ""  # e.g., "Ampere", "RDNA 2", "Xe"
    process_size: str = ""  # e.g., "8nm", "6nm"

    # Memory Information
    vram_total_mb: float = 0.0
    vram_used_mb: float = 0.0
    vram_free_mb: float = 0.0
    vram_percent: float = 0.0
    memory_clock_mhz: float = 0.0
    memory_type: str = ""  # GDDR6, HBM2, etc.
    memory_bus_width: int = 0  # bits

    # GPU Clock Information
    core_clock_mhz: float = 0.0
    core_clock_boost_mhz: float = 0.0
    core_clock_base_mhz: float = 0.0

    # Usage Information
    gpu_utilization_percent: float = 0.0
    memory_utilization_percent: float = 0.0

    # Temperature Information
    temperature_celsius: Optional[float] = None
    hotspot_temp_celsius: Optional[float] = None
    memory_temp_celsius: Optional[float] = None

    # Power Information
    power_draw_watts: Optional[float] = None
    power_limit_watts: Optional[float] = None
    power_efficiency: Optional[float] = None  # Performance per watt

    # Fan Information
    fan_speed_percent: Optional[float] = None
    fan_speed_rpm: Optional[float] = None

    # Driver Information
    driver_version: str = "Unknown"
    driver_date: str = "Unknown"
    driver_model: str = "Unknown"
    whql_certified: bool = False

    # BIOS/Firmware
    bios_version: str = "Unknown"
    bios_date: str = "Unknown"

    # PCI Express Information
    pci_bus: str = ""  # e.g., "PCIe 4.0 x16"
    pci_generation: int = 0  # 1, 2, 3, 4, 5
    pci_link_width: int = 0  # x1, x2, x4, x8, x16
    pci_max_bandwidth_gbps: float = 0.0
    pci_slot: str = ""  # Physical slot information

    # Compute Capabilities
    cuda_cores: Optional[int] = None
    stream_processors: Optional[int] = None
    opencl_version: str = "Unknown"
    vulkan_support: bool = False
    directx_version: str = "Unknown"
    shader_model: str = "Unknown"

    # Display Capabilities
    max_resolution: str = "Unknown"
    max_monitors: int = 0
    display_outputs: List[str] = field(default_factory=list)

    # Virtualization Information
    is_virtualized: bool = False
    virtualization_type: str = "Unknown"  # Hyper-V, VMware, etc.
    hypervisor_vendor: str = "Unknown"

    # Identifiers
    uuid: str = ""  # Persistent unique identifier
    serial_number: str = ""  # Where available

    # Additional Information
    detector_source: str = ""  # Which detection method found this GPU
    is_available: bool = False
    last_updated: float = 0.0

    # Raw data from detectors (for debugging)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, list):
                result[key] = value.copy()
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GPUInfo':
        """Create from dictionary"""
        # Handle enum conversion
        if 'vendor' in data and isinstance(data['vendor'], str):
            try:
                data['vendor'] = GPUVendor(data['vendor'])
            except ValueError:
                data['vendor'] = GPUVendor.UNKNOWN

        if 'gpu_type' in data and isinstance(data['gpu_type'], str):
            try:
                data['gpu_type'] = GPUType(data['gpu_type'])
            except ValueError:
                data['gpu_type'] = GPUType.UNKNOWN

        return cls(**data)

    def copy(self) -> 'GPUInfo':
        """Create a copy of this GPUInfo object"""
        return GPUInfo.from_dict(self.to_dict())