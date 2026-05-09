"""
Utility helper functions
"""
from typing import Union
from datetime import timedelta

# Import theme manager for color functions
from styles.theme import theme_manager


def format_bytes(bytes_value: Union[int, float], precision: int = 2) -> str:
    """
    Format bytes to human readable string
    
    Args:
        bytes_value: Number of bytes
        precision: Decimal precision
        
    Returns:
        Formatted string (e.g., "1.50 GB")
    """
    if bytes_value is None or bytes_value == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    value = float(bytes_value)
    
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1
    
    return f"{value:.{precision}f} {units[unit_index]}"


def format_bytes_per_second(bytes_per_sec: Union[int, float], precision: int = 2) -> str:
    """Format bytes per second to human readable string"""
    return f"{format_bytes(bytes_per_sec, precision)}/s"


def format_uptime(seconds: Union[int, float]) -> str:
    """
    Format uptime seconds to human readable string
    
    Args:
        seconds: Uptime in seconds
        
    Returns:
        Formatted string (e.g., "5d 12h 30m")
    """
    if seconds is None or seconds < 0:
        return "N/A"
    
    td = timedelta(seconds=int(seconds))
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def format_frequency(hz: Union[int, float]) -> str:
    """Format frequency in Hz to MHz or GHz"""
    if hz is None or hz == 0:
        return "0 MHz"
    
    if hz >= 1_000_000_000:
        return f"{hz / 1_000_000_000:.2f} GHz"
    elif hz >= 1_000_000:
        return f"{hz / 1_000_000:.0f} MHz"
    else:
        return f"{hz:.0f} Hz"


def format_percentage(value: Union[int, float], precision: int = 1) -> str:
    """Format percentage value"""
    if value is None:
        return "N/A"
    return f"{value:.{precision}f}%"


def format_number(value: Union[int, float], precision: int = 2) -> str:
    """Format number with thousands separator"""
    if value is None:
        return "N/A"
    
    if isinstance(value, int):
        return f"{value:,}"
    else:
        return f"{value:,.{precision}f}"


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to max length with suffix"""
    if text is None:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_cpu_color(percentage: float) -> str:
    """Get color based on CPU percentage - theme aware"""
    c = theme_manager.colors
    if percentage >= 90:
        return c.STATUS_RED
    elif percentage >= 70:
        return c.STATUS_ORANGE
    elif percentage >= 50:
        return c.STATUS_YELLOW
    else:
        return c.STATUS_GREEN


def get_temperature_color(temp: float) -> str:
    """Get color based on temperature - theme aware"""
    c = theme_manager.colors
    if temp >= 80:
        return c.STATUS_RED
    elif temp >= 70:
        return c.STATUS_ORANGE
    elif temp >= 60:
        return c.STATUS_YELLOW
    else:
        return c.STATUS_GREEN


def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))


def lerp(start: float, end: float, t: float) -> float:
    """Linear interpolation between start and end"""
    t = clamp(t, 0.0, 1.0)
    return start + (end - start) * t


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Smooth step function for smooth transitions"""
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)
