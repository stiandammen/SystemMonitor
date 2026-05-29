"""
NVIDIA GPU Detector using nvidia-smi subprocess.
Used as a fallback when pynvml / nvidia-ml-py is not installed.
Provides clocks, temperatures, utilisation, VRAM, power and fan data.
"""
import subprocess
import time
import logging
from typing import List, Optional

from .gpu_detector import GPUDetector
from .gpu_info import GPUInfo, GPUVendor, GPUType


# nvidia-smi query fields in the order we request them
_QUERIES = [
    "name",
    "uuid",
    "driver_version",
    "clocks.gr",                  # core clock MHz
    "clocks.mem",                 # memory clock MHz
    "clocks.sm",                  # SM clock MHz
    "clocks.max.gr",              # max core clock
    "clocks.max.mem",             # max mem clock
    "temperature.gpu",            # °C
    "utilization.gpu",            # %
    "utilization.memory",         # %
    "memory.total",               # MiB
    "memory.used",                # MiB
    "memory.free",                # MiB
    "power.draw",                 # W
    "power.limit",                # W
    "fan.speed",                  # %
    "pcie.link.gen.current",      # PCIe generation
    "pcie.link.width.current",    # PCIe lane width
]


class NvidiaSMIDetector(GPUDetector):
    """Detect NVIDIA GPUs via the nvidia-smi command-line tool."""

    def __init__(self):
        super().__init__()
        self._available = self._probe()

    # ------------------------------------------------------------------
    # GPUDetector interface
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return self._available

    def detect(self) -> List[GPUInfo]:
        if not self._available:
            return []

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    f"--query-gpu={','.join(_QUERIES)}",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception as exc:
            self.logger.error(f"nvidia-smi subprocess failed: {exc}")
            return []

        if result.returncode != 0:
            self.logger.error(f"nvidia-smi error: {result.stderr.strip()}")
            return []

        gpus = []
        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            gpu = self._parse_line(line)
            if gpu:
                gpus.append(gpu)

        self.logger.info(f"nvidia-smi detector found {len(gpus)} NVIDIA GPU(s)")
        return gpus

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _probe(self) -> bool:
        """Return True if nvidia-smi is installed and finds at least one GPU."""
        try:
            r = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return r.returncode == 0 and bool(r.stdout.strip())
        except FileNotFoundError:
            return False
        except Exception:
            return False

    @staticmethod
    def _flt(val: str) -> Optional[float]:
        """Parse a float, returning None on error or negative sentinel values."""
        try:
            f = float(val.strip())
            return None if f < 0 else f
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _intv(val: str) -> Optional[int]:
        try:
            return int(val.strip())
        except (ValueError, TypeError):
            return None

    def _parse_line(self, line: str) -> Optional[GPUInfo]:
        vals = [v.strip() for v in line.split(",")]
        if len(vals) < len(_QUERIES):
            self.logger.warning(f"nvidia-smi line has too few columns: {line!r}")
            return None

        idx = {q: i for i, q in enumerate(_QUERIES)}

        def g(q: str) -> str:
            return vals[idx[q]]

        name = g("name")
        uuid = g("uuid")
        driver = g("driver_version")

        core_mhz = self._flt(g("clocks.gr"))
        mem_mhz = self._flt(g("clocks.mem"))
        core_max_mhz = self._flt(g("clocks.max.gr"))
        temp = self._flt(g("temperature.gpu"))
        gpu_use = self._flt(g("utilization.gpu"))
        mem_use = self._flt(g("utilization.memory"))
        mem_total = self._flt(g("memory.total"))
        mem_used = self._flt(g("memory.used"))
        mem_free = self._flt(g("memory.free"))
        power = self._flt(g("power.draw"))
        power_limit = self._flt(g("power.limit"))
        fan = self._flt(g("fan.speed"))
        pci_gen = self._intv(g("pcie.link.gen.current"))
        pci_width = self._intv(g("pcie.link.width.current"))

        vram_percent = 0.0
        if mem_total and mem_total > 0 and mem_used is not None:
            vram_percent = min(100.0, (mem_used / mem_total) * 100.0)

        pci_str = ""
        if pci_gen and pci_width:
            pci_str = f"PCIe Gen {pci_gen} x{pci_width}"

        try:
            return GPUInfo(
                name=name,
                vendor=GPUVendor.NVIDIA,
                gpu_type=GPUType.DEDICATED,
                uuid=uuid,
                device_id=uuid,
                core_clock_mhz=core_mhz or 0.0,
                core_clock_boost_mhz=core_max_mhz or 0.0,
                memory_clock_mhz=mem_mhz or 0.0,
                temperature_celsius=temp,
                gpu_utilization_percent=gpu_use or 0.0,
                memory_utilization_percent=mem_use or 0.0,
                vram_total_mb=mem_total or 0.0,
                vram_used_mb=mem_used or 0.0,
                vram_free_mb=mem_free or 0.0,
                vram_percent=vram_percent,
                power_draw_watts=power,
                power_limit_watts=power_limit,
                fan_speed_percent=fan,
                driver_version=driver if driver and driver != "N/A" else "Unknown",
                pci_bus=pci_str,
                pci_generation=pci_gen or 0,
                pci_link_width=pci_width or 0,
                detector_source="nvidia-smi",
                is_available=True,
                last_updated=time.time(),
            )
        except Exception as exc:
            self.logger.error(f"Error building GPUInfo from nvidia-smi: {exc}")
            return None
