"""
CPU Manager
Centralizes CPU detection - mirroring GPUManager's approach of giving the
rest of the app one professional, cached source of truth instead of
scattered psutil/WMI/PowerShell calls. Handles:
  * Name cleanup (stripping the "(R)"/"(TM)"/"CPU" noise PowerShell returns)
  * Temperature fallback chain (psutil sensors -> WMI thermal zone -> HWiNFO)
  * P-core/E-core topology identification (Intel 12th gen+ hybrid designs)
"""
import re
import time
import logging
import platform
import subprocess

from systemmonitor.typing_ext import Optional
from .cpu_info import CPUInfo, CPUVendor


class CPUManager:
    """Detects and caches CPU identity, topology and temperature"""

    # "Intel(R) Core(TM) i9-12900K CPU @ 3.20GHz" -> "Intel Core i9-12900K @ 3.20GHz"
    _NAME_NOISE = re.compile(r'\((?:R|TM|C)\)', re.IGNORECASE)
    _NAME_CPU_WORD = re.compile(r'\bCPU\b', re.IGNORECASE)
    _WHITESPACE = re.compile(r'\s+')

    # Matches the model number in Intel Core names, e.g. "i9-12900K" -> "12900",
    # "i7-9700K" -> "9700". The generation is everything but the last 3 (SKU) digits.
    _INTEL_MODEL_PATTERN = re.compile(r'\bi[3579]-(\d{4,5})')

    # psutil sensor keys that may carry the package/CPU temperature, in priority order
    _PSUTIL_SENSOR_KEYS = ['coretemp', 'cpu_thermal', 'k10temp', 'zenpower', 'cpu', 'cpu0']

    def __init__(self):
        self.logger = logging.getLogger("CPUManager")
        self._cache_ttl = 30.0  # static info essentially never changes between scans
        self._cached_info: Optional[CPUInfo] = None
        self._last_scan_time = 0.0

    # ------------------------------------------------------------------
    # Static info (name, vendor, core topology)
    # ------------------------------------------------------------------

    def get_info(self) -> CPUInfo:
        """Get cached static CPU information (name, vendor, core topology)"""
        now = time.time()
        if self._cached_info is not None and (now - self._last_scan_time) < self._cache_ttl:
            return self._cached_info.copy()

        info = self._detect_info()
        self._cached_info = info
        self._last_scan_time = now
        return info.copy()

    def get_name(self) -> str:
        """Convenience accessor for the cleaned CPU name"""
        return self.get_info().name

    def clear_cache(self):
        """Clear cached static info, forcing the next get_info() to re-detect"""
        self._cached_info = None
        self._last_scan_time = 0.0

    def _detect_info(self) -> CPUInfo:
        import psutil

        physical = psutil.cpu_count(logical=False) or 1
        logical = psutil.cpu_count(logical=True) or physical

        raw_name = self._fetch_raw_name()
        name = self._clean_name(raw_name)
        vendor = self._detect_vendor(name)

        performance, efficiency, hybrid = self._detect_hybrid_topology(name, vendor, physical, logical)

        return CPUInfo(
            name=name,
            raw_name=raw_name,
            vendor=vendor,
            architecture=platform.machine(),
            physical_cores=physical,
            logical_cores=logical,
            performance_cores=performance,
            efficiency_cores=efficiency,
            has_hybrid_architecture=hybrid,
            last_updated=time.time(),
        )

    def _fetch_raw_name(self) -> str:
        """Get the raw CPU name string. WMI/Win32_Processor is the most
        complete source on Windows; platform.processor() is the cross-platform fallback."""
        if platform.system() == 'Windows':
            try:
                result = subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
                    capture_output=True, text=True, timeout=5, creationflags=0x08000000
                )
                name = result.stdout.strip()
                if name:
                    return name
            except Exception:
                pass

        return platform.processor() or "Unknown CPU"

    def _clean_name(self, raw_name: str) -> str:
        """Strip the registration-mark and "CPU" noise PowerShell/WMI return,
        e.g. "Intel(R) Core(TM) i9-12900K CPU @ 3.20GHz" -> "Intel Core i9-12900K @ 3.20GHz"."""
        if not raw_name:
            return "Unknown CPU"

        name = self._NAME_NOISE.sub('', raw_name)
        name = self._NAME_CPU_WORD.sub('', name)
        name = self._WHITESPACE.sub(' ', name).strip(' -')
        return name or "Unknown CPU"

    def _detect_vendor(self, name: str) -> CPUVendor:
        upper = name.upper()
        if 'INTEL' in upper:
            return CPUVendor.INTEL
        if 'AMD' in upper or 'RYZEN' in upper or 'EPYC' in upper or 'THREADRIPPER' in upper:
            return CPUVendor.AMD
        if 'APPLE' in upper:
            return CPUVendor.APPLE
        if 'ARM' in upper or 'QUALCOMM' in upper or 'SNAPDRAGON' in upper:
            return CPUVendor.ARM
        return CPUVendor.UNKNOWN

    def _detect_hybrid_topology(self, name: str, vendor: CPUVendor, physical: int, logical: int):
        """Identify Performance-core / Efficiency-core counts for hybrid designs.

        Intel's 12th-gen+ ("Alder Lake"/"Raptor Lake"/"Core Ultra") hybrid layouts
        pair Hyper-Threaded P-cores (2 threads each) with single-threaded E-cores.
        That asymmetry is exactly what lets the split be derived arithmetically
        from the core/thread counts alone, without any vendor API:

            physical = P + E
            logical  = 2*P + E      (only P-cores contribute a 2nd thread)
            =>  P = logical - physical
            =>  E = physical - P

        Returns (performance_cores, efficiency_cores, is_hybrid).
        """
        if vendor != CPUVendor.INTEL or physical <= 0 or logical <= physical:
            return None, None, False

        if not self._is_hybrid_capable_generation(name):
            return None, None, False

        performance = logical - physical
        efficiency = physical - performance
        if performance <= 0 or efficiency < 0:
            return None, None, False

        return performance, efficiency, True

    def _is_hybrid_capable_generation(self, name: str) -> bool:
        """P/E-core hybrid layouts began with Intel's 12th generation
        ("Alder Lake") and continue through "Core Ultra" (Meteor Lake+),
        which dropped the "i3/i5/i7/i9-NNNNN" naming scheme entirely."""
        if 'CORE ULTRA' in name.upper():
            return True

        match = self._INTEL_MODEL_PATTERN.search(name)
        if not match:
            return False

        digits = match.group(1)
        try:
            # The model number is "<generation><3-digit SKU>", e.g. "12900" -> gen 12, "9700" -> gen 9
            generation = int(digits[:-3])
        except ValueError:
            return False

        return generation >= 12

    # ------------------------------------------------------------------
    # Temperature fallback chain: psutil sensors -> WMI thermal zone -> HWiNFO
    # ------------------------------------------------------------------

    def get_temperature(self) -> Optional[float]:
        """Get the current CPU temperature in Celsius, trying progressively
        less direct sources until one returns a usable reading."""
        temp = self._read_psutil_temperature()
        if temp is not None:
            return temp

        temp = self._read_wmi_temperature()
        if temp is not None:
            return temp

        return self._read_hwinfo_temperature()

    def _read_psutil_temperature(self) -> Optional[float]:
        """Most direct source - exposed by the kernel/ACPI on platforms psutil supports"""
        import psutil

        if not hasattr(psutil, 'sensors_temperatures'):
            return None

        try:
            temps = psutil.sensors_temperatures()
        except Exception:
            return None

        if not temps:
            return None

        for key in self._PSUTIL_SENSOR_KEYS:
            entries = temps.get(key)
            if not entries:
                continue
            for entry in entries:
                current = getattr(entry, 'current', None)
                if current is not None:
                    return float(current)

        return None

    def _read_wmi_temperature(self) -> Optional[float]:
        """Windows fallback via the ACPI thermal zone WMI class (reports
        tenths of a Kelvin - needs conversion to Celsius)"""
        if platform.system() != 'Windows':
            return None

        try:
            result = subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-NoProfile", "-Command",
                 "(Get-CimInstance MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | "
                 "Select-Object -First 1).CurrentTemperature"],
                capture_output=True, text=True, timeout=3, creationflags=0x08000000
            )
            value = result.stdout.strip()
            if value:
                temp_tenths_kelvin = float(value)
                return temp_tenths_kelvin / 10 - 273.15
        except Exception:
            pass

        return None

    def _read_hwinfo_temperature(self) -> Optional[float]:
        """Last resort - read the CPU package temperature out of HWiNFO's
        shared memory segment (only populated while HWiNFO is running with
        "Shared Memory Support" enabled in its settings)"""
        import ctypes

        # HWiNFO shared memory signatures (V1-V4)
        HWINFO_SIGNATURES = [
            b"HWiNFO",     # V1/V2 64-bit
            b"HWiNFO32",   # V1/V2 32-bit
            b"HWiNFO_V",   # V3/V4 signature prefix
            b"HWiNFO32_V", # V3/V4 32-bit
        ]

        # HWiNFO shared memory names (newer versions use _V2, _V3, _V4)
        HWINFO_NAMES = [
            "HWiNFO32_Sens", "HWiNFO64_Sens",
            "HWiNFO32_V2", "HWiNFO64_V2",
            "HWiNFO32_V3", "HWiNFO64_V3",
            "HWiNFO32_V4", "HWiNFO64_V4",
        ]

        try:
            kernel32 = ctypes.windll.kernel32

            handle = None
            for name in HWINFO_NAMES:
                handle = kernel32.OpenFileMappingW(0x0004, False, name)
                if handle:
                    break

            if not handle:
                return None

            try:
                mapping = kernel32.MapViewOfFile(handle, 0x0004, 0, 0, 8192)
            finally:
                kernel32.CloseHandle(handle)

            if not mapping:
                return None

            try:
                # Read signature (16 bytes to be safe)
                sig = ctypes.create_string_buffer(16)
                ctypes.memmove(sig, mapping, 16)

                if not any(sig.raw[:len(s)] == s for s in HWINFO_SIGNATURES):
                    return None

                # Different HWiNFO versions store temperature data at different offsets -
                # try the common ones, validating against a plausible CPU temperature range
                for offset in [0x30, 0x34, 0x38, 0x40, 0x44, 0x48, 0x50, 0x60, 0x80, 0x100]:
                    try:
                        temp_raw = ctypes.c_float()
                        ctypes.memmove(ctypes.addressof(temp_raw), mapping + offset, 4)
                        temp = temp_raw.value
                        # Valid CPU temperature range: 0-125°C (some systems show up to 125°C under load)
                        if 0 < temp < 125:
                            return temp
                    except Exception:
                        continue

                # Some Intel/AMD layouts store it higher up instead
                for offset in [0xB0, 0xB4, 0xB8, 0xBC, 0xC0, 0xC4]:
                    try:
                        temp_raw = ctypes.c_float()
                        ctypes.memmove(ctypes.addressof(temp_raw), mapping + offset, 4)
                        temp = temp_raw.value
                        if 20 < temp < 100:  # CPUs rarely run below 20°C
                            return temp
                    except Exception:
                        continue

                return None
            finally:
                if mapping:
                    kernel32.UnmapViewOfFile(mapping)
        except Exception:
            return None
