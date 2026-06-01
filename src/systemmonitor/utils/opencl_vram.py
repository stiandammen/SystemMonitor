"""
Utility for detecting VRAM via OpenCL
"""
import logging
from systemmonitor.typing import Optional

logger = logging.getLogger("OpenCLVRAM")

def get_vram_via_opencl(device_name: str) -> Optional[float]:
    """
    Try to get VRAM size in MB for a device with the given name using OpenCL

    Args:
        device_name: The name of the device to match

    Returns:
        VRAM size in MB if found, None otherwise
    """
    try:
        import pyopencl as cl
    except ImportError:
        logger.debug("PyOpenCL not available for VRAM detection")
        return None

    try:
        platforms = cl.get_platforms()
        for platform in platforms:
            try:
                devices = platform.get_devices()
                for device in devices:
                    # Check if the device name matches (case-insensitive, partial match)
                    if device_name.lower() in device.name.lower() or \
                       device.name.lower() in device_name.lower():
                        vram_bytes = device.global_mem_size
                        vram_mb = vram_bytes / (1024 * 1024)
                        logger.debug(f"Found VRAM via OpenCL for '{device.name}': {vram_mb:.0f} MB")
                        return vram_mb
            except Exception as e:
                logger.debug(f"Error getting devices from platform {platform.name}: {e}")
                continue
    except Exception as e:
        logger.debug(f"Error in OpenCL VRAM detection: {e}")

    return None
