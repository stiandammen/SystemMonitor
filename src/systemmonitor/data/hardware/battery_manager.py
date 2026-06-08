"""
Battery Manager - Laptop battery & power-plan info
Wraps psutil.sensors_battery() and the active Windows power scheme so the UI
can show charge level, charging status, time remaining and the active plan.
Returns None gracefully on desktops with no battery.
"""
import platform
import subprocess
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class BatteryInfo:
    percent: float
    power_plugged: Optional[bool]
    secs_left: Optional[int]   # None = unknown/unlimited (e.g. while charging)
    power_plan: str

    @property
    def status_text(self) -> str:
        if self.power_plugged is True:
            return "Charging" if self.percent < 100 else "Plugged in"
        if self.power_plugged is False:
            return "On battery"
        return "Unknown"


class BatteryManager:
    """Reads the system battery and active Windows power plan, with caching."""

    _POWER_PLAN_CACHE_TTL = 60.0

    def __init__(self):
        self._power_plan_cache: Optional[str] = None
        self._power_plan_cache_time: float = 0.0

    def has_battery(self) -> bool:
        return self.get_status() is not None

    def get_status(self) -> Optional[BatteryInfo]:
        """Return current battery info, or None if no battery is present."""
        try:
            import psutil
            if not hasattr(psutil, 'sensors_battery'):
                return None
            battery = psutil.sensors_battery()
        except Exception:
            return None

        if battery is None:
            return None

        secs_left = battery.secsleft
        try:
            import psutil
            if secs_left in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN):
                secs_left = None
        except Exception:
            if not isinstance(secs_left, (int, float)) or secs_left < 0:
                secs_left = None

        return BatteryInfo(
            percent=float(battery.percent),
            power_plugged=battery.power_plugged,
            secs_left=secs_left,
            power_plan=self._get_power_plan(),
        )

    def _get_power_plan(self) -> str:
        """Active Windows power scheme name (e.g. 'Balanced', 'High performance')."""
        now = time.time()
        if self._power_plan_cache and (now - self._power_plan_cache_time) < self._POWER_PLAN_CACHE_TTL:
            return self._power_plan_cache

        plan = "Unknown"
        if platform.system() == 'Windows':
            try:
                result = subprocess.run(
                    ["powercfg", "/getactivescheme"],
                    capture_output=True, text=True, timeout=3
                )
                out = result.stdout.strip()
                if '(' in out and ')' in out:
                    plan = out.split('(', 1)[1].rsplit(')', 1)[0].strip()
            except Exception:
                pass

        self._power_plan_cache = plan
        self._power_plan_cache_time = now
        return plan

    @staticmethod
    def format_time_remaining(secs: Optional[int]) -> str:
        if secs is None or secs < 0:
            return "—"
        hours, remainder = divmod(int(secs), 3600)
        minutes = remainder // 60
        if hours > 0:
            return f"{hours}h {minutes}m left"
        return f"{minutes}m left"
