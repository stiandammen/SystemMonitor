"""
Network Discovery Module
Comprehensive LAN/WiFi device scanning using multiple techniques
"""
import socket
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable, Set
import ipaddress

import psutil

from .classification import DeviceClassifier, DeviceType


@dataclass
class DiscoveredDevice:
    """Discovered network device"""
    ip: str
    mac: str = ""
    hostname: str = ""
    vendor: str = ""
    device_type: DeviceType = DeviceType.UNKNOWN
    ports: List[int] = field(default_factory=list)
    services: Dict[int, str] = field(default_factory=dict)
    status: str = "offline"
    ping_ms: float = 0
    last_seen: datetime = field(default_factory=datetime.now)
    first_seen: datetime = field(default_factory=datetime.now)
    connection_type: str = "wired"
    os_guess: str = ""
    is_local_adapter: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for GUI"""
        cfg = DeviceClassifier.get_type_config(self.device_type)
        return {
            "id": f"net_{self.ip.replace('.', '_')}",
            "name": self.hostname or self.ip,
            "ip": self.ip,
            "mac": self.mac.upper() if self.mac else "N/A",
            "vendor": self.vendor or "Unknown",
            "type": self.device_type.value,
            "type_label": cfg.label,
            "type_color": cfg.color,
            "type_glyph": cfg.glyph,
            "status": self.status,
            "ping": int(self.ping_ms),
            "ports": self.ports,
            "services": self.services,
            "os": self.os_guess or "N/A",
            "connection_type": self.connection_type,
            "last_seen": self.last_seen.strftime("%H:%M:%S"),
            "first_seen": self.first_seen.isoformat(),
            "is_adapter": self.is_local_adapter,
        }


class NetworkDiscovery:
    """Network device discovery using ARP, ping, and port scanning"""

    def __init__(self):
        self._devices: Dict[str, DiscoveredDevice] = {}
        self._lock = threading.Lock()
        self._scanning = False
        self._scan_thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable] = None

    def get_local_ip(self) -> str:
        """Get the primary local IP address"""
        try:
            for iface, addrs in psutil.net_if_addrs().items():
                # Skip virtual interfaces
                skip_prefixes = ('vEthernet', 'Virtual', 'Loopback', 'Loop',
                               'isatap', 'Local Area Connection', 'Loopback')
                if any(p.lower() in iface.lower() for p in skip_prefixes):
                    continue

                for addr in addrs:
                    if addr.family.name == 'AF_INET' and not addr.address.startswith('127.'):
                        return addr.address
        except Exception:
            pass
        return "192.168.1.1"

    def get_subnet(self) -> str:
        """Get the network subnet"""
        local_ip = self.get_local_ip()
        parts = local_ip.rsplit(".", 1)
        return f"{parts[0]}.0/24"

    def get_local_interfaces(self) -> List[dict]:
        """Get all local network interfaces"""
        interfaces = []
        try:
            for iface, addrs in psutil.net_if_addrs().items():
                skip_prefixes = ('vEthernet', 'Virtual', 'Loopback', 'Loop', 'isatap')
                if any(p.lower() in iface.lower() for p in skip_prefixes):
                    continue

                ipv4 = None
                mac = None
                for addr in addrs:
                    if addr.family.name == 'AF_INET' and not addr.address.startswith('127.'):
                        ipv4 = addr.address
                    elif addr.family.value == -1 and '-' in addr.address:
                        mac = addr.address.upper().replace('-', ':')

                if not mac:
                    continue

                try:
                    stats = psutil.net_if_stats()[iface]
                    speed = int(stats.speed * 1000) if stats.speed else 0
                    is_up = stats.isup
                except KeyError:
                    speed = 0
                    is_up = False

                # Determine type
                iface_lower = iface.lower()
                if 'wi-fi' in iface_lower or 'wlan' in iface_lower or 'wifi' in iface_lower:
                    conn_type = 'wifi'
                    dev_type = DeviceType.WIFI
                elif 'bluetooth' in iface_lower:
                    conn_type = 'bluetooth'
                    dev_type = DeviceType.BLUETOOTH
                else:
                    conn_type = 'ethernet'
                    dev_type = DeviceType.ETHERNET

                vendor = DeviceClassifier.get_vendor_from_mac(mac)

                device = DiscoveredDevice(
                    ip=ipv4 or "0.0.0.0",
                    mac=mac,
                    hostname=socket.gethostname(),
                    vendor=vendor,
                    device_type=dev_type,
                    status="online" if is_up else "disconnected",
                    ping_ms=0,
                    is_local_adapter=True,
                    connection_type=conn_type,
                )
                device.vendor = vendor

                interfaces.append(device.to_dict())
        except Exception:
            pass
        return interfaces

    def _ping_host(self, ip: str, timeout: float = 1.0) -> bool:
        """Ping a single host"""
        try:
            if subprocess.run(["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip],
                            capture_output=True, timeout=timeout + 0.5).returncode == 0:
                return True
        except Exception:
            # Fallback using PowerShell ping
            try:
                result = subprocess.run(
                    ["powershell", "-Command", f"Test-Connection -ComputerName {ip} -Count 1 -TimeoutSeconds 1 -Quiet"],
                    capture_output=True, timeout=2
                )
                return result.returncode == 0
            except Exception:
                pass
        return False

    def _get_ping_latency(self, ip: str) -> float:
        """Get ping latency to host in milliseconds"""
        start = time.perf_counter()
        try:
            if subprocess.run(["ping", "-n", "1", "-w", "1000", ip],
                            capture_output=True, timeout=1.2).returncode == 0:
                return (time.perf_counter() - start) * 1000
        except Exception:
            pass
        return 999

    def _resolve_hostname(self, ip: str) -> str:
        """Resolve hostname from IP"""
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except Exception:
            return ""

    def _parse_arp_entry(self, line: str, subnet_prefix: str) -> Optional[DiscoveredDevice]:
        """Parse ARP entry line"""
        try:
            if subnet_prefix not in line:
                return None

            parts = line.split()
            ip = None
            mac = None

            # Windows arp -a format: "192.168.1.1          00-11-22-33-44-55     dynamic"
            for i, part in enumerate(parts):
                if '.' in part and subnet_prefix in part:
                    ip = part.strip('()')
                if '-' in part and len(part) == 17:
                    mac = part.upper().replace('-', ':')

            if not ip or not mac or len(mac) != 17:
                return None

            vendor = DeviceClassifier.get_vendor_from_mac(mac)
            device_type = DeviceClassifier.classify(mac=mac, vendor=vendor, ip=ip)
            ping_ms = self._get_ping_latency(ip)

            return DiscoveredDevice(
                ip=ip,
                mac=mac,
                vendor=vendor,
                device_type=device_type,
                status="online",
                ping_ms=ping_ms,
            )
        except Exception:
            return None

    def _read_arp_cache(self) -> List[DiscoveredDevice]:
        """Read ARP cache using multiple methods"""
        devices = []
        local_ip = self.get_local_ip()
        subnet_prefix = local_ip.rsplit(".", 1)[0]

        # Method 1: Windows ARP command
        try:
            result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=10)
            for line in result.stdout.split("\n"):
                device = self._parse_arp_entry(line, subnet_prefix)
                if device:
                    devices.append(device)
        except Exception:
            pass

        # Method 2: PowerShell Get-NetNeighbor
        if not devices:
            try:
                ps_script = """
                $neighbors = Get-NetNeighbor -AddressFamily IPv4 | Where-Object { $_.State -ne 'Unreachable' }
                foreach ($n in $neighbors) {
                    if ($n.IPAddress -and $n.LinkLayerAddress -and $n.LinkLayerAddress.Length -eq 17) {
                        Write-Output "$($n.IPAddress)|$($n.LinkLayerAddress)"
                    }
                }
                """
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_script],
                    capture_output=True, text=True, timeout=15
                )
                for line in result.stdout.strip().split("\n"):
                    if "|" in line:
                        parts = line.split("|")
                        ip = parts[0].strip()
                        mac = parts[1].strip().upper().replace("-", ":")
                        if ":" in mac and len(mac) == 17:
                            vendor = DeviceClassifier.get_vendor_from_mac(mac)
                            device_type = DeviceClassifier.classify(mac=mac, vendor=vendor, ip=ip)
                            devices.append(DiscoveredDevice(
                                ip=ip, mac=mac, vendor=vendor,
                                device_type=device_type,
                                status="online", ping_ms=self._get_ping_latency(ip)
                            ))
            except Exception:
                pass

        return devices

    def _scan_ports(self, ip: str, ports: List[int] = None) -> tuple:
        """Scan common ports on a host"""
        if ports is None:
            ports = [80, 443, 445, 22, 8080, 8008, 8009, 554, 5000, 5001, 9100, 5353, 1900, 7000]

        open_ports = []
        services = {}

        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.3)
                if sock.connect_ex((ip, port)) == 0:
                    open_ports.append(port)
                    service = DeviceClassifier.get_service_for_port(port)
                    if service:
                        services[port] = service
                sock.close()
            except Exception:
                pass

        return open_ports, services

    def _scan_network(self, progress_callback: Callable = None) -> List[DiscoveredDevice]:
        """Perform full network scan"""
        devices = []

        # First get ARP cache
        arp_devices = self._read_arp_cache()
        devices.extend(arp_devices)

        # Also get active connections
        try:
            local_ip = self.get_local_ip()
            local_prefix = local_ip.rsplit(".", 1)[0]

            for conn in psutil.net_connections(kind='inet'):
                if conn.raddr and conn.raddr.ip:
                    remote_ip = conn.raddr.ip
                    if remote_ip.startswith(local_prefix) and not any(d.ip == remote_ip for d in devices):
                        devices.append(DiscoveredDevice(
                            ip=remote_ip,
                            mac="00:00:00:00:00:00",
                            vendor="Unknown",
                            device_type=DeviceType.UNKNOWN,
                            status="online",
                            ping_ms=999,
                        ))
        except Exception:
            pass

        # Update devices with additional info in parallel
        def update_device(dev: DiscoveredDevice):
            dev.hostname = self._resolve_hostname(dev.ip)
            if dev.mac != "00:00:00:00:00:00":
                dev.ports, dev.services = self._scan_ports(dev.ip)
                # Re-classify with more info
                dev.device_type = DeviceClassifier.classify(
                    mac=dev.mac, vendor=dev.vendor,
                    hostname=dev.hostname, ip=dev.ip,
                    open_ports=dev.ports
                )
            dev.last_seen = datetime.now()

        threads = []
        for dev in devices:
            t = threading.Thread(target=lambda d=dev: update_device(d), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=2)

        return devices

    def scan(self, callback: Callable = None) -> List[DiscoveredDevice]:
        """Perform network scan with optional callback"""
        self._callback = callback
        self._scanning = True

        try:
            devices = self._scan_network()
            with self._lock:
                # Update internal state
                for dev in devices:
                    self._devices[dev.ip] = dev

            if callback:
                callback(devices)

            return devices
        finally:
            self._scanning = False

    def scan_async(self, callback: Callable = None):
        """Scan network in background thread"""
        if self._scanning:
            return

        self._scan_thread = threading.Thread(target=self.scan, args=(callback,), daemon=True)
        self._scan_thread.start()

    def get_devices(self) -> List[DiscoveredDevice]:
        """Get currently known devices"""
        with self._lock:
            return list(self._devices.values())

    def is_scanning(self) -> bool:
        """Check if scan is in progress"""
        return self._scanning

    def ping_device(self, ip: str) -> float:
        """Ping a specific device and return latency"""
        return self._get_ping_latency(ip)
