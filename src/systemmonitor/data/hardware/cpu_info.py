"""
CPU Information Data Class
Holds the static facts CPUManager derives about the installed processor
"""
import dataclasses
from dataclasses import dataclass
from systemmonitor.typing_ext import Optional, Dict, Any
from systemmonitor.enums import Enum


class CPUVendor(Enum):
    """CPU Vendors"""
    INTEL = "Intel"
    AMD = "AMD"
    ARM = "ARM"
    APPLE = "Apple"
    UNKNOWN = "Unknown"


@dataclass
class CPUInfo:
    """Static CPU identification and core topology"""

    # Identification
    name: str = "Unknown CPU"
    raw_name: str = ""  # Uncleaned string as returned by WMI/PowerShell, kept for debugging
    vendor: CPUVendor = CPUVendor.UNKNOWN
    architecture: str = ""  # e.g. "AMD64"

    # Core topology
    physical_cores: int = 0
    logical_cores: int = 0

    # Hybrid (P-core/E-core) topology - populated only for designs that have one
    # (Intel 12th gen "Alder Lake" and newer)
    performance_cores: Optional[int] = None
    efficiency_cores: Optional[int] = None
    has_hybrid_architecture: bool = False

    # Bookkeeping
    last_updated: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {}
        for key, value in self.__dict__.items():
            result[key] = value.value if isinstance(value, Enum) else value
        return result

    def copy(self) -> 'CPUInfo':
        """Create a shallow copy of this CPUInfo object"""
        return dataclasses.replace(self)
