"""
Network Data Collector
"""
import socket
import platform
from systemmonitor.typing import Dict, Any, List, Optional


class NetworkCollector:
    """Collect network usage and connection information"""
    
    def __init__(self):
        self._previous_io = None
        self._previous_time = 0
    
    def collect(self) -> Dict[str, Any]:
        """Collect current network data"""
        try:
            import psutil
            import time
            
            # Get IO counters
            io_stats = self._get_io_stats()
            
            # Get interface info
            interfaces = self._get_interfaces()
            
            # Get connections
            connections = self._get_connections()
            
            # Get addresses
            addresses = self._get_addresses()
            
            return {
                'download_speed': io_stats.get('download_rate', 0),
                'upload_speed': io_stats.get('upload_rate', 0),
                'total_sent': io_stats.get('bytes_sent', 0),
                'total_recv': io_stats.get('bytes_recv', 0),
                'interfaces': interfaces,
                'connections_count': len(connections),
                'addresses': addresses,
            }
            
        except Exception as e:
            print(f"Network collect error: {e}")
            return self._get_fallback_data()
    
    def _get_io_stats(self) -> Dict[str, float]:
        """Get network I/O with rate calculation"""
        try:
            import psutil
            import time
            
            current_io = psutil.net_io_counters()
            current_time = time.time()
            
            if self._previous_io is None:
                self._previous_io = current_io
                self._previous_time = current_time
                return {
                    'bytes_sent': 0,
                    'bytes_recv': 0,
                    'upload_rate': 0,
                    'download_rate': 0,
                }
            
            # Calculate rates
            time_delta = current_time - self._previous_time
            if time_delta > 0:
                upload_rate = (current_io.bytes_sent - self._previous_io.bytes_sent) / time_delta
                download_rate = (current_io.bytes_recv - self._previous_io.bytes_recv) / time_delta
            else:
                upload_rate = 0
                download_rate = 0
            
            # Update previous
            self._previous_io = current_io
            self._previous_time = current_time
            
            return {
                'bytes_sent': current_io.bytes_sent,
                'bytes_recv': current_io.bytes_recv,
                'upload_rate': max(0, upload_rate),
                'download_rate': max(0, download_rate),
            }
            
        except Exception as e:
            print(f"Network IO error: {e}")
            return {
                'bytes_sent': 0,
                'bytes_recv': 0,
                'upload_rate': 0,
                'download_rate': 0,
            }
    
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

