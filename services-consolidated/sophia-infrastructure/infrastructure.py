"""Infrastructure management module - consolidated from agno-wrappers"""
from typing import Dict, List, Any
import psutil
import time

class InfrastructureManager:
    def __init__(self):
        self.wrappers = {}
        self.metrics = {}
        
    async def initialize(self):
        self.wrappers = {
            "monitoring": MonitoringWrapper(),
            "health": HealthWrapper(),
            "metrics": MetricsWrapper()
        }
        
    async def health_check(self):
        return {"wrappers": list(self.wrappers.keys())}
        
    async def execute_wrapper(self, service: str, action: str, data: Dict[str, Any]):
        wrapper = self.wrappers.get(service)
        if not wrapper:
            raise ValueError(f"Unknown wrapper: {service}")
        return await wrapper.execute(action, data)
        
    async def get_metrics(self):
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "timestamp": time.time()
        }
        
    async def get_system_status(self):
        return {"status": "operational", "uptime": time.time()}
        
    async def cleanup(self):
        for wrapper in self.wrappers.values():
            await wrapper.cleanup()

class BaseWrapper:
    async def execute(self, action: str, data: Dict[str, Any]):
        return {"action": action, "result": "success"}
    async def cleanup(self):
        pass

class MonitoringWrapper(BaseWrapper):
    pass

class HealthWrapper(BaseWrapper):
    pass

class MetricsWrapper(BaseWrapper):
    pass