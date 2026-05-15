import clr
import os

if os.path.exists(os.path.join(os.path.abspath(__file__), "_version.py")):
    from WinTmp._version import __version__
else:
    __version__ = "0.0.0-dev"

clr.AddReference(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "LibreHardwareMonitorLib.dll"
    )
)
from LibreHardwareMonitor import Hardware

hw = Hardware.Computer()
# Only enable GPU - skip CPU, Memory, Motherboard, Storage to avoid RAMSPDToolkit issues
hw.IsCpuEnabled = False
hw.IsGpuEnabled = True
hw.IsMemoryEnabled = False
hw.IsMotherboardEnabled = False
hw.IsStorageEnabled = False
hw.Open()

GPU_SENSORS = (
    Hardware.HardwareType.GpuAmd,
    Hardware.HardwareType.GpuNvidia,
    Hardware.HardwareType.GpuIntel,
)


def GPU_Temp():
    for h in hw.Hardware:
        h.Update()

        if h.HardwareType in GPU_SENSORS:
            for sensor in h.Sensors:
                if sensor.SensorType == Hardware.SensorType.Temperature:
                    return sensor.Value
    return None


def CPU_Temp():
    return None  # Disabled due to RAMSPDToolkit issues


def GPU_Temps():
    temps = []
    for h in hw.Hardware:
        h.Update()

        if h.HardwareType in GPU_SENSORS:
            for sensor in h.Sensors:
                if sensor.SensorType == Hardware.SensorType.Temperature:
                    temps.append(sensor.Value)
    return temps


def CPU_Temps():
    return []  # Disabled due to RAMSPDToolkit issues


def _all_temps():
    temps = {}
    for h in hw.Hardware:
        h.Update()
        for sensor in h.Sensors:
            if sensor.SensorType == Hardware.SensorType.Temperature:
                key = f"{h.HardwareType}_{sensor.Name}"
                temps[key] = sensor.Value
    return temps