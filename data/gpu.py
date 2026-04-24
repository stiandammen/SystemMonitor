"""
GPU Data Collector
Supports NVIDIA GPUs via NVML or GPUtil
"""
from typing import Dict, Any, Optional


class GPUCollector:
    """Collect GPU usage and information"""
    
    def __init__(self):
        self._nvml_available = False
        self._gputil_available = False
        self._gpu_count = 0
        self._init_backends()
    
    def _init_backends(self):
        """Initialize GPU backends"""
        # Try NVML (NVIDIA Management Library)
        try:
            import pynvml
            pynvml.nvmlInit()
            self._nvml_available = True
            self._gpu_count = pynvml.nvmlDeviceGetCount()
        except:
            pass
        
        # Try GPUtil as fallback
        if not self._nvml_available:
            try:
                import GPUtil
                self._gputil_available = True
                self._gpu_count = len(GPUtil.getGPUs())
            except:
                pass
    
    def is_available(self) -> bool:
        """Check if GPU monitoring is available"""
        return self._nvml_available or self._gputil_available
    
    def collect(self) -> Dict[str, Any]:
        """Collect GPU data"""
        if not self.is_available():
            return {'available': False}
        
        try:
            if self._nvml_available:
                return self._collect_nvml()
            elif self._gputil_available:
                return self._collect_gputil()
            else:
                return {'available': False}
                
        except Exception as e:
            print(f"GPU collect error: {e}")
            return {'available': False, 'error': str(e)}
    
    def _collect_nvml(self) -> Dict[str, Any]:
        """Collect using NVML"""
        import pynvml
        
        # Get first GPU (can be extended for multi-GPU)
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        
        # Get name
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        
        # Get utilization
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        
        # Get memory
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        
        # Get temperature
        try:
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        except:
            temp = None
        
        # Get power
        try:
            power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # Convert to watts
        except:
            power = None
        
        # Get fan speed
        try:
            fan = pynvml.nvmlDeviceGetFanSpeed(handle)
        except:
            fan = None
        
        return {
            'available': True,
            'name': name,
            'load': util.gpu,
            'memory_used': mem.used / (1024**3),  # GB
            'memory_total': mem.total / (1024**3),  # GB
            'memory_percent': (mem.used / mem.total) * 100 if mem.total > 0 else 0,
            'temperature': temp,
            'power': power,
            'fan_speed': fan,
        }
    
    def _collect_gputil(self) -> Dict[str, Any]:
        """Collect using GPUtil"""
        import GPUtil
        
        gpus = GPUtil.getGPUs()
        if not gpus:
            return {'available': False}
        
        gpu = gpus[0]  # First GPU
        
        return {
            'available': True,
            'name': gpu.name,
            'load': gpu.load * 100,
            'memory_used': gpu.memoryUsed,
            'memory_total': gpu.memoryTotal,
            'memory_percent': (gpu.memoryUsed / gpu.memoryTotal) * 100 if gpu.memoryTotal > 0 else 0,
            'temperature': gpu.temperature,
            'power': None,  # GPUtil doesn't provide power
            'fan_speed': None,  # GPUtil doesn't provide fan speed
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Get static GPU information"""
        if not self.is_available():
            return {'available': False}
        
        data = self.collect()
        return {
            'available': True,
            'name': data.get('name', 'Unknown GPU'),
            'memory_total': data.get('memory_total', 0),
        }
