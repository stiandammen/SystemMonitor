"""
Device Classification System
Intelligent device type detection using vendor, MAC, ports, and metadata
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class DeviceType(Enum):
    """Device type enumeration"""
    NAS = "nas"
    SERVER = "server"
    COMPUTER = "computer"
    LAPTOP = "laptop"
    PHONE = "phone"
    TABLET = "tablet"
    PRINTER = "printer"
    ROUTER = "router"
    SWITCH = "switch"
    ACCESS_POINT = "access_point"
    IOT = "iot"
    SMART = "smart"
    WEBCAM = "webcam"
    SPEAKER = "speaker"
    HEADSET = "headset"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    GAME_CONTROLLER = "game_controller"
    USB_DONGLE = "usb_dongle"
    AUDIO_INTERFACE = "audio_interface"
    STORAGE = "storage"
    NETWORKAdapter = "network_adapter"
    BLUETOOTH = "bluetooth"
    ETHERNET = "ethernet"
    WIFI = "wifi"
    UNKNOWN = "unknown"


@dataclass
class DeviceClassConfig:
    """Configuration for device class display"""
    label: str
    color: str
    dim: str
    glyph: str
    icon: str


DEVICE_TYPE_CONFIG: Dict[DeviceType, DeviceClassConfig] = {
    DeviceType.NAS: DeviceClassConfig("NAS-SERVER", "#00AAFF", "#001F3D", "[SRV]", "fa5s.server"),
    DeviceType.SERVER: DeviceClassConfig("SERVER", "#00AAFF", "#001F3D", "[SRV]", "fa5s.server"),
    DeviceType.COMPUTER: DeviceClassConfig("ENDPOINT", "#00FFE5", "#004D45", "[CPU]", "fa5s.desktop"),
    DeviceType.LAPTOP: DeviceClassConfig("LAPTOP", "#00FFE5", "#004D45", "[LAP]", "fa5s.laptop"),
    DeviceType.PHONE: DeviceClassConfig("MOBILE-DEV", "#00FF88", "#003D20", "[MOB]", "fa5s.mobile"),
    DeviceType.TABLET: DeviceClassConfig("TABLET", "#00FF88", "#003D20", "[TAB]", "fa5s.tablet"),
    DeviceType.PRINTER: DeviceClassConfig("PERIPH-DEV", "#CC44FF", "#2A0040", "[PRN]", "fa5s.print"),
    DeviceType.ROUTER: DeviceClassConfig("GATEWAY", "#FF3B5C", "#3D0012", "[GWY]", "fa5s.wifi"),
    DeviceType.SWITCH: DeviceClassConfig("SWITCH", "#FF3B5C", "#3D0012", "[SWT]", "fa5s.projectdiagram"),
    DeviceType.ACCESS_POINT: DeviceClassConfig("AP", "#FF3B5C", "#3D0012", "[AP ]", "fa5s.wifi"),
    DeviceType.IOT: DeviceClassConfig("IOT-DEVICE", "#FFB800", "#3D2C00", "[IOT]", "ph.devices"),
    DeviceType.SMART: DeviceClassConfig("SMART-DEV", "#FFB800", "#3D2C00", "[SMT]", "ph.lightbulb"),
    DeviceType.WEBCAM: DeviceClassConfig("WEBCAM", "#FFB800", "#3D2C00", "[CAM]", "fa5s.camera"),
    DeviceType.SPEAKER: DeviceClassConfig("SPEAKER", "#FFB800", "#3D2C00", "[SPK]", "fa5s.volume-up"),
    DeviceType.HEADSET: DeviceClassConfig("HEADSET", "#FFB800", "#3D2C00", "[HDP]", "fa5s.headphones"),
    DeviceType.KEYBOARD: DeviceClassConfig("KEYBOARD", "#FFB800", "#3D2C00", "[KBD]", "fa5s.keyboard"),
    DeviceType.MOUSE: DeviceClassConfig("MOUSE", "#FFB800", "#3D2C00", "[MSE]", "fa5s.mouse-pointer"),
    DeviceType.GAME_CONTROLLER: DeviceClassConfig("CONTROLLER", "#FFB800", "#3D2C00", "[GME]", "fa5s.gamepad"),
    DeviceType.USB_DONGLE: DeviceClassConfig("USB-DONGLE", "#FFB800", "#3D2C00", "[USB]", "fa5s.plug"),
    DeviceType.AUDIO_INTERFACE: DeviceClassConfig("AUDIO-IF", "#00AAFF", "#001F3D", "[AUD]", "fa5s.volume-up"),
    DeviceType.STORAGE: DeviceClassConfig("STORAGE", "#00AAFF", "#001F3D", "[DIS]", "fa5s.hdd"),
    DeviceType.NETWORKAdapter: DeviceClassConfig("NETWORK-ADAPTER", "#00FFE5", "#004D45", "[ETH]", "fa5s.ethernet"),
    DeviceType.BLUETOOTH: DeviceClassConfig("BLUETOOTH", "#CC44FF", "#2A0040", "[BT ]", "fa5s.bluetooth-b"),
    DeviceType.ETHERNET: DeviceClassConfig("ETHERNET", "#00FFE5", "#004D45", "[ETH]", "fa5s.ethernet"),
    DeviceType.WIFI: DeviceClassConfig("WI-FI-ADAPTER", "#00AAFF", "#001F3D", "[WFI]", "fa5s.wifi"),
    DeviceType.UNKNOWN: DeviceClassConfig("UNKNOWN", "#3D6B50", "#111111", "[UNK]", "fa5s.question"),
}


# Extended OUI Vendor database
OUI_VENDORS: Dict[str, str] = {
    # Apple
    "A4:C3:F0": "Apple Inc.",
    "D8:BB:2C": "Apple",
    "F0:18:98": "Apple",
    "3C:22:FB": "Apple",
    "A8:66:7F": "Apple",
    "00:1F:F3": "Apple",
    "F0:DB:E2": "Apple",
    "74:E1:B6": "Apple",
    "48:A9:1C": "Apple",
    "34:C0:59": "Apple",
    # Samsung
    "F4:42:8F": "Samsung Electronics",
    "FC:A1:3E": "Samsung",
    "8C:F5:A3": "Samsung",
    "94:E9:6A": "Samsung",
    "9C:02:98": "Samsung",
    "D0:22:BE": "Samsung",
    # Google
    "54:60:09": "Google LLC",
    "3C:5A:B4": "Google",
    "F4:F5:D8": "Google",
    "94:EB:2C": "Google",
    # HP
    "B0:5A:DA": "HP Inc.",
    "68:A5:99": "HP",
    "00:1E:0B": "HP",
    "2C:27:D7": "HP",
    # QNAP
    "00:08:9B": "QNAP Systems",
    "2C:B0:5D": "QNAP",
    "24:5E:CB": "QNAP",
    # Synology
    "00:1B:21": "Synology",
    "34:88:5D": "Synology",
    "24:69:A5": "Synology",
    # Raspberry Pi
    "DC:A6:32": "Raspberry Pi Ltd.",
    "B8:27:EB": "Raspberry Pi",
    "E4:5F:01": "Raspberry Pi",
    # Ring
    "78:8A:20": "Ring LLC",
    "24:6B:2C": "Ring",
    # Philips Hue
    "00:17:88": "Philips",
    "EC:B5:FA": "Philips Hue",
    "00:BB:3E": "Philips",
    # ASUS
    "00:1A:2B": "ASUSTeK Computer",
    "1C:87:2C": "ASUS",
    "F0:79:59": "ASUS",
    # TP-Link
    "50:C7:BF": "TP-Link Technologies",
    "64:70:02": "TP-Link",
    "14:CC:20": "TP-Link",
    # Netgear
    "44:94:FC": "Netgear",
    "6C:B0:CE": "Netgear",
    "C4:04:15": "Netgear",
    # Intel
    "00:1B:77": "Intel Corporation",
    "00:1E:67": "Intel",
    "00:1F:3B": "Intel",
    "A0:36:9F": "Intel",
    # Microsoft
    "00:03:FF": "Microsoft",
    "7C:1E:52": "Microsoft",
    "50:1A:C5": "Microsoft",
    "00:0D:3A": "Microsoft",
    # VMware
    "00:50:56": "VMware Inc.",
    "08:00:27": "Oracle VirtualBox",
    "00:0C:29": "VMware",
    # Dell
    "00:14:22": "Dell",
    "18:03:73": "Dell",
    "F0:1F:AF": "Dell",
    # Lenovo
    "00:23:7C": "Lenovo",
    "F4:8E:09": "Lenovo",
    "58:91:CF": "Lenovo",
    # Sony
    "00:19:C5": "Sony",
    "00:1D:BA": "Sony",
    "B4:52:7D": "Sony",
    # LG
    "AC:0D:1B": "LG Electronics",
    "08:08:AF": "LG",
    # Huawei
    "00:1E:10": "Huawei",
    "00:25:9E": "Huawei",
    "34:00:A3": "Huawei",
    # Xiaomi
    "34:80:B3": "Xiaomi",
    "74:23:44": "Xiaomi",
    "F0:B4:29": "Xiaomi",
    # Amazon
    "74:C2:46": "Amazon",
    "FC:A1:83": "Amazon",
    "0C:47:C9": "Amazon",
    # ESPurna
    "84:CC:A8": "ESPurna",
    # Shelly
    "24:6F:28": "Shelly",
    # Tuya
    "BC:DD:C2": "Tuya",
    # Sonoff
    "60:01:94": "Sonoff",
    # Wyze
    "24:0A:C4": "Wyze",
    # LIFX
    "D0:73:D5": "LIFX",
    # Nest
    "64:16:66": "Nest Labs",
    # Ecovacs
    "F4:39:09": "Ecovacs",
    # iRobot
    "9C:EC:EF": "iRobot",
    # DJI
    "00:12:46": "DJI",
    # GoPro
    "60:AA:FD": "GoPro",
    # Anker
    "4C:1A:3D": "Anker",
    # Jabra
    "00:1A:7D": "Jabra",
    "20:DF:BD": "Jabra",
    # Bose
    "04:52:C3": "Bose",
    "28:6C:07": "Bose",
    # Sony (PlayStation)
    "00:19:C5": "Sony Interactive Entertainment",
    # NVIDIA
    "10:DE:E6": "NVIDIA",
    "04:4B:80": "NVIDIA",
    # AMD
    "02:00:00": "AMD",
    # Realtek
    "00:E0:4C": "Realtek",
    "52:54:00": "Realtek",
    # Cisco
    "00:1A:2B": "Cisco",
    "00:50:56": "Cisco",
    # Ubiquiti
    "44:D9:E7": "Ubiquiti",
    "68:D7:9A": "Ubiquiti",
    # Foscam
    "38:F0:98": "Foscam",
    # Axis
    "AC:CC:8E": "Axis Communications",
    # Dahua
    "48:4F:E2": "Dahua Technology",
    # Logitech
    "00:1F:20": "Logitech",
    "7C:1D:EF": "Logitech",
    "30:FD:38": "Logitech",
    # Razer
    "00:05:8E": "Razer",
    "04:4B:ED": "Razer",
    # Corsair
    "00:1D:28": "Corsair",
    "70:62:11": "Corsair",
    # SteelSeries
    "10:9C:AD": "SteelSeries",
    # HyperX
    "98:5D:AD": "HyperX",
    # Elgato
    "70:85:C2": "Elgato",
    # Scarlett
    "06EE:0100": "Scarlett",
    # Focusrite
    "06EE:0100": "Focusrite",
    # Behringer
    "08AC:0100": "Behringer",
    # Pioneer
    "00:A0:96": "Pioneer",
    # Denon
    "00:05:CD": "Denon",
    # Yamaha
    "00:A0:7A": "Yamaha",
    # Sennheiser
    "00:1B:66": "Sennheiser",
    # Audio-Technica
    "00:16:20": "Audio-Technica",
    # Shure
    "00:1E:8C": "Shure",
    # Blue
    "00:1F:00": "Blue Microphones",
}


# Port-based service detection
COMMON_PORTS: Dict[int, Tuple[str, DeviceType]] = {
    22: ("SSH", DeviceType.COMPUTER),
    80: ("HTTP", DeviceType.SERVER),
    443: ("HTTPS", DeviceType.SERVER),
    445: ("SMB", DeviceType.COMPUTER),
    554: ("RTSP", DeviceType.WEBCAM),
    8008: ("Google Cast", DeviceType.SMART),
    8009: ("Google Cast TLS", DeviceType.SMART),
    8080: ("HTTP-ALT", DeviceType.SERVER),
    8443: ("HTTPS-ALT", DeviceType.SERVER),
    9000: ("NAS", DeviceType.NAS),
    5000: ("NAS", DeviceType.NAS),
    5001: ("HTTPS-NAS", DeviceType.NAS),
    5353: ("mDNS", DeviceType.IOT),
    5357: ("WS-Discovery", DeviceType.IOT),
    7000: ("Sonos", DeviceType.SPEAKER),
    1400: ("Denon HEOS", DeviceType.SPEAKER),
    1900: ("UPnP", DeviceType.IOT),
    1883: ("MQTT", DeviceType.IOT),
    8883: ("MQTT-TLS", DeviceType.IOT),
    5683: ("CoAP", DeviceType.IOT),
    9100: ("JetDirect", DeviceType.PRINTER),
    631: ("IPP", DeviceType.PRINTER),
    161: ("SNMP", DeviceType.ROUTER),
    162: ("SNMP-TRAP", DeviceType.ROUTER),
    53: ("DNS", DeviceType.ROUTER),
    67: ("DHCP", DeviceType.ROUTER),
    68: ("DHCP", DeviceType.ROUTER),
    389: ("LDAP", DeviceType.SERVER),
    636: ("LDAPS", DeviceType.SERVER),
    3306: ("MySQL", DeviceType.SERVER),
    5432: ("PostgreSQL", DeviceType.SERVER),
    27017: ("MongoDB", DeviceType.SERVER),
    6379: ("Redis", DeviceType.SERVER),
    11211: ("Memcached", DeviceType.SERVER),
    873: ("rsync", DeviceType.NAS),
    2049: ("NFS", DeviceType.NAS),
    445: ("SMB", DeviceType.NAS),
    548: ("AFP", DeviceType.NAS),
    3689: ("DAAP", DeviceType.SPEAKER),
    8200: ("Roku", DeviceType.SMART),
    8888: ("Kodi", DeviceType.SMART),
    9090: ("Prometheus", DeviceType.SERVER),
    3000: ("Node.js", DeviceType.SERVER),
    50070: ("HDFS", DeviceType.NAS),
    8086: ("InfluxDB", DeviceType.SERVER),
    8123: ("Telegraf", DeviceType.IOT),
    188: ("Node-RED", DeviceType.IOT),
    5433: ("TimescaleDB", DeviceType.SERVER),
    5432: ("PostgreSQL", DeviceType.SERVER),
}


class DeviceClassifier:
    """Intelligent device classification system"""

    @staticmethod
    def get_vendor_from_mac(mac: str) -> str:
        """Look up vendor from MAC address OUI"""
        if not mac:
            return "Unknown"
        mac_clean = mac.upper().replace("-", ":").replace(".", ":")
        parts = mac_clean.split(":")
        if len(parts) >= 3:
            oui = ":".join(parts[:3])
            return OUI_VENDORS.get(oui, "Unknown")
        return "Unknown"

    @staticmethod
    def classify_by_vendor(vendor: str, hostname: str = "") -> DeviceType:
        """Classify device by vendor name and hostname"""
        vendor_lower = vendor.lower()
        hostname_lower = hostname.lower()

        # NAS detection
        if any(x in vendor_lower for x in ["qnap", "synology", "nas", "wd", "western digital", "seagate", "netapp", "dell emc", "hpe", "hitachi"]):
            if any(x in hostname_lower for x in ["nas", "storage", "raid", "backup", "server"]):
                return DeviceType.NAS
            return DeviceType.NAS

        # Server detection
        if any(x in vendor_lower for x in ["dell", "hp", "ibm", "lenovo", "supermicro", "oracle", "fujitsu"]):
            if any(x in hostname_lower for x in ["server", "srv", "host", "vm", "node"]):
                return DeviceType.SERVER
            return DeviceType.COMPUTER

        # Mobile detection
        if any(x in vendor_lower for x in ["apple", "samsung", "google", "sony", "lg", "xiaomi", "huawei", "oneplus", "oppo", "vivo", "nokia"]):
            if any(x in hostname_lower for x in ["iphone", "ipad", "galaxy", "pixel", "redmi", "note"]):
                return DeviceType.PHONE
            return DeviceType.PHONE

        # Router/AP detection
        if any(x in vendor_lower for x in ["tp-link", "netgear", "asus", "linksys", "cisco", "ubiquiti", "mikrotik", "netcomm", "dlink", "belkin", "tp link"]):
            if any(x in hostname_lower for x in ["router", "ap", "gateway", "mesh", "deco", "orbi", "eap"]):
                return DeviceType.ROUTER
            return DeviceType.ROUTER

        # Smart/IoT detection
        if any(x in vendor_lower for x in ["philips", "hue", "ring", "nest", "ecobee", "nest labs", "smartthings", "samsung smartthings"]):
            return DeviceType.SMART
        if any(x in vendor_lower for x in ["shelly", "tuya", "sonoff", "espurna", "esphome", "wemos", "lolin"]):
            return DeviceType.IOT
        if any(x in vendor_lower for x in ["amazon", "echodot", "echospot", "firetv", "alexa"]):
            return DeviceType.SMART

        # Printer detection
        if any(x in vendor_lower for x in ["hp", "canon", "epson", "brother", "lexmark", "xerox", "ricoh", "konica", "sharp", "pantum"]):
            return DeviceType.PRINTER

        # Webcam/Security camera
        if any(x in vendor_lower for x in ["axis", "dahua", "hikvision", "foscam", "amcrest", "reolink", "nest cam", "ring cam", "arlo", "wyze"]):
            return DeviceType.WEBCAM

        # Audio devices
        if any(x in vendor_lower for x in ["sonos", "bose", "denon", "yamaha", "pioneer", "marantz", "heos", "chromecast audio", "google home"]):
            return DeviceType.SPEAKER
        if any(x in vendor_lower for x in ["jabra", "sennheiser", "bose", "beats", "audio-technica", "shure", "blue", "rode", "focusrite", "scarlett", "behringer", "presonus"]):
            return DeviceType.HEADSET

        # Input devices
        if any(x in vendor_lower for x in ["logitech", "razer", "corsair", "steelseries", "hyperx", "keychron", "apple magic"]):
            if "keyboard" in hostname_lower:
                return DeviceType.KEYBOARD
            if any(x in hostname_lower for x in ["mouse", "mx", "trackpad"]):
                return DeviceType.MOUSE
            return DeviceType.UNKNOWN

        # Game controllers
        if any(x in vendor_lower for x in ["sony computer entertainment", "microsoft xbox", "nvidia", "steam"]):
            return DeviceType.GAME_CONTROLLER

        # Network adapters
        if any(x in vendor_lower for x in ["intel", "broadcom", "qualcomm", "realtek", "mediatek"]):
            return DeviceType.NETWORKAdapter

        # Raspberry Pi and single board computers
        if any(x in vendor_lower for x in ["raspberry pi", "odroid", "orange pi", "banana pi", "beaglebone"]):
            return DeviceType.COMPUTER

        # Default unknown
        return DeviceType.UNKNOWN

    @classmethod
    def classify_by_hostname(cls, hostname: str, ip: str = "") -> DeviceType:
        """Classify device by hostname patterns"""
        hostname_lower = hostname.lower()
        ip_last = ip.split(".")[-1] if ip else ""

        # Known hostname patterns
        patterns = {
            r"(nas|storage|raid|backup|server)": DeviceType.NAS,
            r"(router|gateway|ap\.?|wifi|mesh|deco|orbi|tp\-link|netgear|asus)": DeviceType.ROUTER,
            r"(printer|canon|hp\-|epson|brother|laser)": DeviceType.PRINTER,
            r"(iphone|ipad|android|galaxy|pixel|redmi|oneplus)": DeviceType.PHONE,
            r"(macbook|imac|macmini|thinkpad|surface|laptop|dell|hp\-)": DeviceType.LAPTOP,
            r"(pc|desktop|workstation|win|linux|macos)": DeviceType.COMPUTER,
            r"(sonos|bose|denon|heos|chromecast|speaker)": DeviceType.SPEAKER,
            r"(hue|philips|ring|nest|ecobee|smartthings)": DeviceType.SMART,
            r"(camera|cam|webcam|dahua|hikvision|axis|foscam)": DeviceType.WEBCAM,
            r"(switch|poe|unifi|pro curve)": DeviceType.SWITCH,
        }

        for pattern, device_type in patterns.items():
            if re.search(pattern, hostname_lower):
                return device_type

        # Default based on IP range
        if ip:
            # Common subnets
            if ip.startswith("192.168.1."):
                return DeviceType.COMPUTER
            elif ip.startswith("192.168.2."):
                return DeviceType.IOT

        return DeviceType.UNKNOWN

    @classmethod
    def classify_by_ports(cls, open_ports: List[int]) -> DeviceType:
        """Classify device by open ports"""
        if not open_ports:
            return DeviceType.UNKNOWN

        port_set = set(open_ports)

        # NAS detection
        if port_set & {2049, 5450, 548, 873, 445, 9000, 5000, 5001}:
            return DeviceType.NAS

        # Printer detection
        if port_set & {9100, 631, 515}:
            return DeviceType.PRINTER

        # Webcam detection
        if 554 in port_set or 8554 in port_set:
            return DeviceType.WEBCAM

        # Router detection
        if port_set & {161, 162, 53, 67, 68}:
            return DeviceType.ROUTER

        # Cast devices
        if port_set & {8008, 8009}:
            return DeviceType.SMART

        # Speaker detection
        if port_set & {7000, 1400, 3689}:
            return DeviceType.SPEAKER

        # Server detection (many ports open)
        if len(port_set) > 5:
            return DeviceType.SERVER

        return DeviceType.UNKNOWN

    @classmethod
    def classify(cls, mac: str = "", vendor: str = "", hostname: str = "", ip: str = "", open_ports: List[int] = None) -> DeviceType:
        """Comprehensive device classification using all available data"""
        if open_ports is None:
            open_ports = []

        # Priority 1: Classify by vendor (most reliable)
        if vendor and vendor != "Unknown":
            return cls.classify_by_vendor(vendor, hostname)

        # Priority 2: Look up vendor from MAC
        if mac:
            vendor_from_mac = cls.get_vendor_from_mac(mac)
            if vendor_from_mac != "Unknown":
                return cls.classify_by_vendor(vendor_from_mac, hostname)

        # Priority 3: Classify by hostname
        if hostname:
            return cls.classify_by_hostname(hostname, ip)

        # Priority 4: Classify by ports
        if open_ports:
            return cls.classify_by_ports(open_ports)

        return DeviceType.UNKNOWN

    @staticmethod
    def get_type_config(device_type: DeviceType) -> DeviceClassConfig:
        """Get display configuration for device type"""
        return DEVICE_TYPE_CONFIG.get(device_type, DEVICE_TYPE_CONFIG[DeviceType.UNKNOWN])

    @staticmethod
    def get_service_for_port(port: int) -> Optional[str]:
        """Get service name for port number"""
        return COMMON_PORTS.get(port, (None, None))[0]
