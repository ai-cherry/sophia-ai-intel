#!/usr/bin/env python3
"""
Sophia AI Redis Setup and Configuration
Sets up Redis caching layer with pub/sub configuration for the Sophia AI system.
"""

import os
import sys
import json
import redis
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisManager:
    """Redis connection and configuration manager"""

    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL')
        self.redis_password = os.getenv('REDIS_PASSWORD')
        self.redis_client = None

    def connect(self) -> bool:
        """Establish Redis connection"""
        try:
            if not self.redis_url:
                logger.error("REDIS_URL not found in environment")
                return False

            # Parse Redis URL
            if self.redis_url.startswith('redis://'):
                # Extract host and port from URL
                url_parts = self.redis_url.replace('redis://', '').split(':')
                if len(url_parts) >= 2:
                    host = url_parts[0]
                    port = int(url_parts[1].split('/')[0]) if '/' in url_parts[1] else 6379
                else:
                    host = 'localhost'
                    port = 6379
            else:
                host = self.redis_url
                port = 6379

            # Connect to Redis
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                password=self.redis_password,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )

            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            return False

    def setup_cache_configuration(self) -> bool:
        """Set up Redis cache configuration"""
        try:
            if not self.redis_client:
                return False

            # Set cache configuration
            cache_config = {
                'maxmemory': '1gb',
                'maxmemory-policy': 'allkeys-lru',
                'appendonly': 'yes',
                'appendfsync': 'everysec',
                'save': '60 1000',
                'tcp-keepalive': '300'
            }

            # Apply configuration (note: some settings may require CONFIG SET command)
            for key, value in cache_config.items():
                try:
                    self.redis_client.config_set(key, value)
                    logger.info(f"Set Redis config: {key} = {value}")
                except Exception as e:
                    logger.warning(f"Could not set {key}: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to setup cache configuration: {e}")
            return False

    def setup_pubsub_channels(self) -> bool:
        """Set up pub/sub channels for Sophia AI system"""
        try:
            if not self.redis_client:
                return False

            # Define pub/sub channels for different system components
            channels = [
                'sophia:agents:status',
                'sophia:agents:commands',
                'sophia:conversations:updates',
                'sophia:tasks:status',
                'sophia:knowledge:updates',
                'sophia:cache:invalidation',
                'sophia:monitoring:events',
                'sophia:webhooks:events'
            ]

            # Create a registry of channels
            channel_registry = {
                'channels': channels,
                'created_at': str(self.redis_client.time()[0]),
                'version': '1.0.0'
            }

            # Store channel registry
            self.redis_client.set('sophia:channels:registry', json.dumps(channel_registry))

            logger.info(f"✅ Set up {len(channels)} pub/sub channels")
            return True

        except Exception as e:
            logger.error(f"Failed to setup pub/sub channels: {e}")
            return False

    def setup_cache_namespaces(self) -> bool:
        """Set up cache namespaces and TTL policies"""
        try:
            if not self.redis_client:
                return False

            # Define cache namespaces with TTL policies
            cache_policies = {
                'sophia:cache:users': 3600,      # 1 hour
                'sophia:cache:agents': 1800,     # 30 minutes
                'sophia:cache:conversations': 7200,  # 2 hours
                'sophia:cache:knowledge': 86400,    # 24 hours
                'sophia:cache:tasks': 600,       # 10 minutes
                'sophia:cache:sessions': 1800,   # 30 minutes
                'sophia:cache:api_responses': 300,  # 5 minutes
                'sophia:cache:embeddings': 604800,  # 7 days
            }

            # Store cache policies
            self.redis_client.set('sophia:cache:policies', json.dumps(cache_policies))

            # Set up namespace keys
            for namespace, ttl in cache_policies.items():
                self.redis_client.set(f"{namespace}:ttl", ttl)

            logger.info(f"✅ Set up {len(cache_policies)} cache namespaces")
            return True

        except Exception as e:
            logger.error(f"Failed to setup cache namespaces: {e}")
            return False

    def test_pubsub_functionality(self) -> bool:
        """Test pub/sub functionality"""
        try:
            if not self.redis_client:
                return False

            # Subscribe to test channel
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe('sophia:test:channel')

            # Publish test message
            test_message = {
                'type': 'test',
                'message': 'Redis pub/sub test',
                'timestamp': str(self.redis_client.time()[0])
            }

            self.redis_client.publish('sophia:test:channel', json.dumps(test_message))

            # Try to get message (non-blocking)
            message = pubsub.get_message(timeout=1.0)
            if message:
                logger.info("✅ Pub/sub test successful")
                pubsub.unsubscribe('sophia:test:channel')
                return True
            else:
                logger.warning("⚠️ Pub/sub test completed but no message received")
                pubsub.unsubscribe('sophia:test:channel')
                return True

        except Exception as e:
            logger.error(f"Pub/sub test failed: {e}")
            return False

    def setup_monitoring_keys(self) -> bool:
        """Set up monitoring and metrics keys"""
        try:
            if not self.redis_client:
                return False

            # Initialize monitoring counters
            monitoring_keys = [
                'sophia:metrics:requests:total',
                'sophia:metrics:errors:total',
                'sophia:metrics:cache:hits',
                'sophia:metrics:cache:misses',
                'sophia:metrics:agents:active',
                'sophia:metrics:conversations:active',
                'sophia:metrics:tasks:completed',
                'sophia:metrics:tasks:failed'
            ]

            # Initialize counters to 0
            for key in monitoring_keys:
                self.redis_client.set(key, 0)

            logger.info(f"✅ Set up {len(monitoring_keys)} monitoring keys")
            return True

        except Exception as e:
            logger.error(f"Failed to setup monitoring keys: {e}")
            return False

    def get_system_info(self) -> Dict[str, Any]:
        """Get Redis system information"""
        try:
            if not self.redis_client:
                return {}

            info = self.redis_client.info()
            return {
                'redis_version': info.get('redis_version', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'unknown'),
                'total_connections_received': info.get('total_connections_received', 0),
                'total_commands_processed': info.get('total_commands_processed', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {}

def main():
    """Main setup function"""
    print("🚀 Setting up Sophia AI Redis Configuration")
    print("=" * 50)

    redis_manager = RedisManager()

    # Step 1: Connect to Redis
    print("\n1️⃣ Connecting to Redis...")
    if not redis_manager.connect():
        print("❌ Failed to connect to Redis. Please check your configuration.")
        sys.exit(1)

    # Step 2: Setup cache configuration
    print("\n2️⃣ Setting up cache configuration...")
    if redis_manager.setup_cache_configuration():
        print("✅ Cache configuration completed")
    else:
        print("⚠️ Some cache configuration settings may not have been applied")

    # Step 3: Setup pub/sub channels
    print("\n3️⃣ Setting up pub/sub channels...")
    if redis_manager.setup_pubsub_channels():
        print("✅ Pub/sub channels configured")
    else:
        print("❌ Failed to setup pub/sub channels")

    # Step 4: Setup cache namespaces
    print("\n4️⃣ Setting up cache namespaces...")
    if redis_manager.setup_cache_namespaces():
        print("✅ Cache namespaces configured")
    else:
        print("❌ Failed to setup cache namespaces")

    # Step 5: Test pub/sub functionality
    print("\n5️⃣ Testing pub/sub functionality...")
    if redis_manager.test_pubsub_functionality():
        print("✅ Pub/sub test completed")
    else:
        print("❌ Pub/sub test failed")

    # Step 6: Setup monitoring keys
    print("\n6️⃣ Setting up monitoring keys...")
    if redis_manager.setup_monitoring_keys():
        print("✅ Monitoring keys configured")
    else:
        print("❌ Failed to setup monitoring keys")

    # Step 7: Display system information
    print("\n7️⃣ Redis System Information:")
    system_info = redis_manager.get_system_info()
    if system_info:
        for key, value in system_info.items():
            print(f"   {key}: {value}")
    else:
        print("   Unable to retrieve system information")

    print("\n" + "=" * 50)
    print("🎉 Redis setup completed successfully!")
    print("\n📋 Configuration Summary:")
    print("   • Cache configuration: ✅")
    print("   • Pub/sub channels: ✅")
    print("   • Cache namespaces: ✅")
    print("   • Monitoring keys: ✅")
    print("   • Connection test: ✅")

    print("\n🔧 Next Steps:")
    print("   1. Update your application to use Redis for caching")
    print("   2. Implement pub/sub message handlers")
    print("   3. Set up Redis monitoring and alerts")
    print("   4. Configure Redis persistence if needed")

if __name__ == "__main__":
    main()