#!/usr/bin/env python3
'''
Service Discovery Implementation
Replaces direct service-to-service calls with event-driven communication
'''

import asyncio
import redis.asyncio as redis
from typing import Dict, Any, List
import json
import structlog

logger = structlog.get_logger()

class ServiceDiscovery:
    '''Service discovery and event bus implementation'''
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        
    async def connect(self):
        '''Connect to Redis event bus'''
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to service discovery bus")
        except Exception as e:
            logger.error("Failed to connect to service discovery", error=str(e))
            raise
    
    async def register_service(self, service_name: str, health_endpoint: str):
        '''Register service with discovery'''
        service_info = {
            "name": service_name,
            "health_endpoint": health_endpoint,
            "timestamp": asyncio.get_event_loop().time(),
            "status": "healthy"
        }
        
        await self.redis_client.hset(
            "services:registry", 
            service_name, 
            json.dumps(service_info)
        )
        
        logger.info("Service registered", service=service_name)
    
    async def publish_event(self, event_type: str, data: Dict[str, Any]):
        '''Publish event to event bus'''
        event = {
            "type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.redis_client.publish(f"events:{event_type}", json.dumps(event))
        logger.info("Event published", event_type=event_type)
    
    async def subscribe_to_events(self, event_types: List[str], callback):
        '''Subscribe to event types'''
        pubsub = self.redis_client.pubsub()
        
        for event_type in event_types:
            await pubsub.subscribe(f"events:{event_type}")
        
        logger.info("Subscribed to events", event_types=event_types)
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    event_data = json.loads(message['data'])
                    await callback(event_data)
                except Exception as e:
                    logger.error("Error processing event", error=str(e))
    
    async def get_service_endpoint(self, service_name: str) -> str:
        '''Get service endpoint from registry'''
        service_data = await self.redis_client.hget("services:registry", service_name)
        
        if service_data:
            service_info = json.loads(service_data)
            return service_info.get('health_endpoint', '')
        
        return None

# Example usage for MCP services
async def setup_mcp_service_discovery():
    '''Setup service discovery for MCP services'''
    discovery = ServiceDiscovery("redis://sophia-event-bus:6379")
    await discovery.connect()
    
    # Register this service
    service_name = os.getenv("SERVICE_NAME", "unknown")
    health_endpoint = f"http://{service_name}:8080/health"
    
    await discovery.register_service(service_name, health_endpoint)
    
    return discovery

# Event types for service communication
EVENT_TYPES = {
    "CONTEXT_REQUEST": "context.request",
    "CONTEXT_RESPONSE": "context.response", 
    "AGENT_REQUEST": "agent.request",
    "AGENT_RESPONSE": "agent.response",
    "BUSINESS_EVENT": "business.event",
    "RESEARCH_REQUEST": "research.request",
    "RESEARCH_RESPONSE": "research.response"
}
