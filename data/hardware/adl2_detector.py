"""
AMD GPU Detector using ADL2 API
Uses ADL2_New_QueryPMLogData_Get for comprehensive sensor data.
Supports edge, hotspot and memory temperatures, fan RPM/%, PCIe info,
voltage, and registry-based VRAM (correct for cards > 4 GB).
"""
import ctypes
import os
import platform
import time
import logging
from ctypes import c_int, c_void_p, CFUNCTYPE, Structure, POINTER
from typing import Dict, List, Optional

from .gpu_detector import GPUDetector
from .gpu_info import GPUInfo, GPUVendor, GPUType


# PMLog sensor indices (from AMD ADL SDK)
_PMLOG_IDX = {
    "gfx_mhz":      1,
    "mem_mhz":      2,
    "temp_edge":    8,
    "temp_mem":     9,
    "fan_rpm":      14,
    "fan_pct":      15,
    "gpu_use":      19,
    "mem_use":      20,
    "gfx_mv":       21,
    "temp_hotspot": 27,
    "bus_speed":    40,
    "bus_lanes":    41,
}


class _Sensor(Structure):
    _fields_ = [("supported", c_int), ("value", c_int)]


class _PMLogData(Structure):
    _fields_ = [
        ("ulLastUpdated", c_int),
        ("sensors", _Sensor * 256),
    ]


class ADL2Detector(GPUDetector):
    """AMD GPU detector using the ADL2 API (atiadlxx.dll)."""

    def __init__(self):
        super().__init__()
        self._lib: Optional[ctypes.CDLL] = None
        self._ctx: Optional[c_void_p] = None
        self._cb_ref = None      # keep callback alive
        self._keep_alive: list = []  # keep malloc buffers alive
        self._init_adl2()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_adl2(self):
        if platform.system() != "Windows":
            return

        try:
            windir = os.environ.get("WINDIR", r"C:\Windows")
            for dll_name in ("atiadlxx.dll", "atiadlxy.dll"):
                path = os.path.join(windir, "System32", dll_name)
                if os.path.exists(path):
                    break
            else:
                self.logger.info("ADL2: atiadlxx.dll not found")
                return

            lib = ctypes.CDLL(path)

            # Allocation callback required by ADL2_Main_Control_Create
            def _alloc(n: int) -> int:
                buf = ctypes.create_string_buffer(n)
                self._keep_alive.append(buf)
                ptr = ctypes.cast(buf, c_void_p)
                return ptr.value or 0

            cb_type = CFUNCTYPE(c_void_p, c_int)
            cb = cb_type(_alloc)
            self._cb_ref = cb  # prevent GC

            ctx = c_void_p()
            ret = lib.ADL2_Main_Control_Create(cb, 1, ctypes.byref(ctx))
            if ret != 0:
                self.logger.warning(f"ADL2_Main_Control_Create returned {ret}")
                return

            self._lib = lib
            self._ctx = ctx
            self.logger.info("ADL2 detector initialised")

        except Exception as exc:
            self.logger.warning(f"ADL2 init error: {exc}")

    # ------------------------------------------------------------------
    # GPUDetector interface
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return self._lib is not None and self._ctx is not None

    def detect(self) -> List[GPUInfo]:
        if not self.is_available():
            return []

        try:
            sensors = self._read_sensors()
            if not sensors:
                self.logger.warning("ADL2: no sensor data returned")
                return []

            gpu_name = self._get_gpu_name()
            vram_mb = self._get_vram_registry(gpu_name)

            def s(key: str) -> Optional[int]:
                return sensors.get(_PMLOG_IDX[key])

            gfx_mhz = s("gfx_mhz")
            mem_mhz = s("mem_mhz")
            temp_edge = s("temp_edge")
            temp_hotspot = s("temp_hotspot")
            temp_mem = s("temp_mem")
            fan_rpm = s("fan_rpm")
            fan_pct = s("fan_pct")
            gpu_use = s("gpu_use")
            mem_use = s("mem_use")
            gfx_mv = s("gfx_mv")
            bus_speed = s("bus_speed")
            bus_lanes = s("bus_lanes")

            pci_str = ""
            pci_gen = 0
            pci_width = 0
            if bus_speed is not None and bus_lanes is not None:
                pci_str = f"PCIe Gen {bus_speed} x{bus_lanes}"
                pci_gen = int(bus_speed)
                pci_width = int(bus_lanes)

            gpu_info = GPUInfo(
                name=gpu_name,
                vendor=GPUVendor.AMD,
                gpu_type=GPUType.DEDICATED,
                core_clock_mhz=float(gfx_mhz) if gfx_mhz is not None else 0.0,
                memory_clock_mhz=float(mem_mhz) if mem_mhz is not None else 0.0,
                temperature_celsius=float(temp_edge) if temp_edge is not None else None,
                hotspot_temp_celsius=float(temp_hotspot) if temp_hotspot is not None else None,
                memory_temp_celsius=float(temp_mem) if temp_mem is not None else None,
                fan_speed_rpm=float(fan_rpm) if fan_rpm is not None else None,
                fan_speed_percent=float(fan_pct) if fan_pct is not None else None,
                gpu_utilization_percent=float(gpu_use) if gpu_use is not None else 0.0,
                memory_utilization_percent=float(mem_use) if mem_use is not None else 0.0,
                vram_total_mb=float(vram_mb) if vram_mb else 0.0,
                pci_bus=pci_str,
                pci_generation=pci_gen,
                pci_link_width=pci_width,
                raw_data={"gfx_mv": gfx_mv},
                detector_source="ADL2",
                is_available=True,
                last_updated=time.time(),
            )

            self.logger.debug(
                f"ADL2: {gpu_name} | core={gfx_mhz} MHz | mem={mem_mhz} MHz | "
                f"temp={temp_edge}°C | load={gpu_use}%"
            )
            return [gpu_info]

        except Exception as exc:
            self.logger.error(f"ADL2 detect error: {exc}", exc_info=True)
            return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_sensors(self) -> Dict[int, int]:
        """Call ADL2_New_QueryPMLogData_Get and return {index: value} for supported sensors."""
        try:
            data = _PMLogData()
            ret = self._lib.ADL2_New_QueryPMLogData_Get(
                self._ctx, 0, ctypes.byref(data)
            )
            if ret != 0:
                self.logger.warning(f"ADL2_New_QueryPMLogData_Get returned {ret}")
                return {}
            return {
                i: data.sensors[i].value
                for i in range(256)
                if data.sensors[i].supported
            }
        except Exception as exc:
            self.logger.warning(f"ADL2 sensor read error: {exc}")
            return {}

    def _get_gpu_name(self) -> str:
        """Return AMD GPU name from WMI, falling back to a generic label."""
        try:
            import wmi  # type: ignore
            for ctrl in wmi.WMI().Win32_VideoController():
                name = ctrl.Name or ""
                if "amd" in name.lower() or "radeon" in name.lower():
                    return name.strip()
        except Exception:
            pass
        return "AMD GPU"

    def _get_vram_registry(self, name_hint: str = "") -> Optional[int]:
        """
        Read VRAM from the Windows display-adapter registry key.
        HardwareInformation.qwMemorySize is 64-bit and correct for cards > 4 GB,
        unlike Win32_VideoController.AdapterRAM which wraps at 4 GB.
        """
        try:
            import winreg
            key_path = (
                r"SYSTEM\CurrentControlSet\Control\Class"
                r"\{4d36e968-e325-11ce-bfc1-08002be10318}"
            )
            hint = name_hint.lower()
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as base:
                idx = 0
                while True:
                    try:
                        sub_name = winreg.EnumKey(base, idx)
                        idx += 1
                        if not sub_name.isdigit():
                            continue
                        sub_path = f"{key_path}\\{sub_name}"
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_path) as sub:
                            try:
                                desc, _ = winreg.QueryValueEx(sub, "DriverDesc")
                                if hint and not any(
                                    x in desc.lower() for x in ("amd", "radeon")
                                ):
                                    continue
                                val, _ = winreg.QueryValueEx(
                                    sub, "HardwareInformation.qwMemorySize"
                                )
                                mb = int(val) // (1024 * 1024)
                                if mb > 0:
                                    return mb
                            except FileNotFoundError:
                                pass
                    except OSError:
                        break
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def __del__(self):
        try:
            if self._lib is not None and self._ctx is not None:
                self._lib.ADL2_Main_Control_Destroy(self._ctx)
        except Exception:
            pass
