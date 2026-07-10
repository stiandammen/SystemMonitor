"""
Network Data Collector
"""
import socket
import platform
from typing import Dict, Any, List, Optional


class NetworkCollector:
    """Collect network usage and connection information with realistic speed tracking"""
    
    EMA_ALPHA = 0.3  # Smoothing factor

    def __init__(self):
        self._previous_io = None
        self._previous_time = 0
        self._smoothed_download = 0.0
        self._smoothed_upload = 0.0
        self._active_interface = None
    
    def collect(self) -> Dict[str, Any]:
        """Collect current network data with smoothing and interface detection"""
        try:
            import psutil
            import time
            
            # Get stats
            io_dict = psutil.net_io_counters(pernic=True)
            stats = psutil.net_if_stats()
            total_io = psutil.net_io_counters()
            current_time = time.time()
            
            # Find active interface
            if not self._active_interface or int(current_time) % 30 == 0:
                self._active_interface = self._find_active_interface(io_dict, stats)
            
            # Calculate rates
            if self._previous_io is None:
                self._previous_io = total_io
                self._previous_time = current_time
                download_rate = 0.0
                upload_rate = 0.0
            else:
                time_delta = current_time - self._previous_time
                if time_delta > 0:
                    raw_download = (total_io.bytes_recv - self._previous_io.bytes_recv) / time_delta
                    raw_upload = (total_io.bytes_sent - self._previous_io.bytes_sent) / time_delta
                    
                    # EMA Smoothing
                    self._smoothed_download = (self.EMA_ALPHA * raw_download) + ((1 - self.EMA_ALPHA) * self._smoothed_download)
                    self._smoothed_upload = (self.EMA_ALPHA * raw_upload) + ((1 - self.EMA_ALPHA) * self._smoothed_upload)
                
                download_rate = self._smoothed_download
                upload_rate = self._smoothed_upload
                
                self._previous_io = total_io
                self._previous_time = current_time
            
            # Get interface info
            interfaces = self._get_interfaces()
            
            # Get connections
            connections = self._get_connections()
            
            # Get addresses
            addresses = self._get_addresses()
            
            return {
                'download_speed': max(0, download_rate),
                'upload_speed': max(0, upload_rate),
                'total_sent': total_io.bytes_sent,
                'total_recv': total_io.bytes_recv,
                'interfaces': interfaces,
                'connections_count': len(connections),
                'addresses': addresses,
                'active_interface': self._active_interface
            }
            
        except Exception as e:
            print(f"Network collect error: {e}")
            return self._get_fallback_data()
            
    def _find_active_interface(self, io_dict, stats_dict) -> str:
        """Heuristic to find the likely primary physical interface"""
        best_iface = None
        max_traffic = -1
        virtual_keywords = ['loopback', 'lo', 'virtual', 'docker', 'veth', 'br-', 'vmnet', 'vbox', 'pseudo', 'teredo', 'tunnel']
        
        for name, io in io_dict.items():
            lname = name.lower()
            if any(k in lname for k in virtual_keywords): continue
            is_up = stats_dict.get(name).isup if name in stats_dict else False
            if not is_up: continue
            traffic = io.bytes_sent + io.bytes_recv
            if traffic > max_traffic:
                max_traffic = traffic
                best_iface = name
        return best_iface or "Total"
    
    def _get_interfaces(self) -> List[Dict[str, Any]]:
        """Get network interface information"""
        try:
            import psutil
            
            interfaces = []
            stats = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
            
            for name, stat in stats.items():
                interface = {
                    'name': name,
                    'is_up': stat.isup,
                    'speed': stat.speed,  # Mbps
                    'mtu': stat.mtu,
                    'addresses': [],
                }
                
                # Get addresses for this interface
                if name in addrs:
                    for addr in addrs[name]:
                        interface['addresses'].append({
                            'family': str(addr.family),
                            'address': addr.address,
                            'netmask': addr.netmask,
                        })
                
                interfaces.append(interface)
            
            return interfaces
            
        except Exception as e:
            print(f"Interface error: {e}")
            return []
    
    def _get_connections(self) -> List[Dict[str, Any]]:
        """Get active network connections"""
        try:
            import psutil
            
            connections = []
            for conn in psutil.net_connections(kind='inet'):
                try:
                    connections.append({
                        'fd': conn.fd,
                        'family': str(conn.family),
                        'type': str(conn.type),
                        'local_addr': conn.laddr,
                        'remote_addr': conn.raddr,
                        'status': conn.status,
                        'pid': conn.pid,
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            return connections
            
        except Exception as e:
            print(f"Connections error: {e}")
            return []
    
    def _get_addresses(self) -> Dict[str, str]:
        """Get system network addresses"""
        try:
            hostname = socket.gethostname()
            
            # Try to get IPv4
            try:
                ipv4 = socket.gethostbyname(hostname)
            except:
                ipv4 = "N/A"
            
            # Try to get IPv6
            try:
                ipv6_info = socket.getaddrinfo(hostname, None, socket.AF_INET6)
                ipv6 = ipv6_info[0][4][0] if ipv6_info else "N/A"
            except:
                ipv6 = "N/A"
            
            return {
                'hostname': hostname,
                'ipv4': ipv4,
                'ipv6': ipv6,
            }
            
        except Exception as e:
            print(f"Address error: {e}")
            return {
                'hostname': "N/A",
                'ipv4': "N/A",
                'ipv6': "N/A",
            }
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Return fallback data"""
        return {
            'download_speed': 0,
            'upload_speed': 0,
            'total_sent': 0,
            'total_recv': 0,
            'interfaces': [],
            'connections_count': 0,
            'addresses': {
                'hostname': "N/A",
                'ipv4': "N/A",
                'ipv6': "N/A",
            },
        }

