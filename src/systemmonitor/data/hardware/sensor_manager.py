"""
Sensor Manager - Extended hardware sensors (fan RPM, voltage rails)

Most consumer Windows hardware only exposes these through vendor utilities
(HWiNFO, LibreHardwareMonitor, motherboard tools); the OS-level sources
(psutil, WMI) are sparse and inconsistent across vendors. This manager tries
the available sources and returns an empty list when nothing usable is found
so the UI can show an honest "not available" message instead of fake numbers.
"""
import platform
import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FanReading:
    label: str
    rpm: Optional[float]


@dataclass
class VoltageReading:
    label: str
    volts: Optional[float]


class SensorManager:
    """Best-effort reader for fan speeds and voltage rails."""

    def get_fan_speeds(self) -> List[FanReading]:
        readings = self._read_psutil_fans()
        if readings:
            return readings
        return self._read_wmi_fans()

    def get_voltages(self) -> List[VoltageReading]:
        return self._read_wmi_voltages()

    # ------------------------------------------------------------------
    # Fans
    # ------------------------------------------------------------------
    def _read_psutil_fans(self) -> List[FanReading]:
        """Direct kernel-exposed fan sensors (mainly Linux hwmon)."""
        try:
            import psutil
            if not hasattr(psutil, 'sensors_fans'):
                return []
            fans = psutil.sensors_fans()
        except Exception:
            return []

        readings = []
        for name, entries in (fans or {}).items():
            for i, entry in enumerate(entries):
                rpm = getattr(entry, 'current', None)
                if rpm is None:
                    continue
                label = entry.label.strip() if getattr(entry, 'label', None) else f"{name} #{i + 1}"
                readings.append(FanReading(label=label, rpm=float(rpm)))
        return readings

    def _read_wmi_fans(self) -> List[FanReading]:
        """Windows fallback via Win32_Fan - rarely populated on consumer boards,
        but surfaces the cooling devices Windows is at least aware of."""
        if platform.system() != 'Windows':
            return []
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-CimInstance Win32_Fan -ErrorAction SilentlyContinue | "
                 "ForEach-Object { \"$($_.Name)|$($_.DesiredSpeed)\" }"],
                capture_output=True, text=True, timeout=3
            )
        except Exception:
            return []

        readings = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or '|' not in line:
                continue
            name, _, speed = line.partition('|')
            name = name.strip() or "System Fan"
            speed = speed.strip()
            rpm = float(speed) if speed.isdigit() and int(speed) > 0 else None
            readings.append(FanReading(label=name, rpm=rpm))
        return readings

    # ------------------------------------------------------------------
    # Voltages
    # ------------------------------------------------------------------
    def _read_wmi_voltages(self) -> List[VoltageReading]:
        """Windows fallback via Win32_Processor.CurrentVoltage.

        The CIM property packs the reading: bit 7 set means the low 7 bits are
        an index into VoltageCaps (no usable value), otherwise the value is the
        voltage in tenths of a volt.
        """
        if platform.system() != 'Windows':
            return []
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | "
                 "Select-Object -First 1).CurrentVoltage"],
                capture_output=True, text=True, timeout=3
            )
            value = result.stdout.strip()
            if not value:
                return []
            raw = int(value)
        except Exception:
            return []

        if raw & 0x80:
            return []  # encodes a capability index, not a real reading

        volts = raw / 10.0
        if volts <= 0:
            return []
        return [VoltageReading(label="CPU Core (VID)", volts=volts)]
