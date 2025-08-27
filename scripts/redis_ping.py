#!/usr/bin/env python3
"""
Redis connectivity test script
Tests Redis connection and performs basic operations with expiry
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import redis
from redis.exceptions import ConnectionError, TimeoutError, RedisError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv('/Users/lynnmusil/sophia-ai-intel-1/.env')

class RedisTester:
    """Redis connectivity and operations tester"""
    
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.client = None
        
        logger.info(f"Redis URL: {self.redis_url}")
        
    def connect(self) -> bool:
        """Establish connection to Redis"""
        logger.info("Connecting to Redis...")
        
        try:
            # Parse Redis URL and create client
            if self.redis_url.startswith('redis://'):
                self.client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
            else:
                # Assume it's a host:port format
                parts = self.redis_url.split(':')
                host = parts[0]
                port = int(parts[1]) if len(parts) > 1 else 6379
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    db=0,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
            
            # Test connection with ping
            pong = self.client.ping()
            if pong:
                logger.info("✅ Successfully connected to Redis")
                return True
            else:
                logger.error("❌ Redis ping failed")
                return False
                
        except ConnectionError as e:
            logger.error(f"❌ Connection error: {str(e)}")
            return False
        except TimeoutError as e:
            logger.error(f"❌ Connection timeout: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return False
    
    def test_basic_operations(self) -> bool:
        """Test basic Redis operations (SET/GET with expiry)"""
        logger.info("\nTesting basic operations...")
        
        try:
            # Test SET with expiry
            key = 'sophia:test:basic'
            value = 'Hello from Sophia AI!'
            expiry_seconds = 60
            
            self.client.setex(key, expiry_seconds, value)
            logger.info(f"✅ SET operation successful: {key} (expires in {expiry_seconds}s)")
            
            # Test GET
            retrieved = self.client.get(key)
            if retrieved == value:
                logger.info(f"✅ GET operation successful: retrieved '{retrieved}'")
            else:
                logger.error(f"❌ GET operation failed: expected '{value}', got '{retrieved}'")
                return False
            
            # Test TTL (Time To Live)
            ttl = self.client.ttl(key)
            logger.info(f"✅ TTL check: {ttl} seconds remaining")
            
            # Test EXISTS
            exists = self.client.exists(key)
            if exists:
                logger.info(f"✅ EXISTS check passed")
            
            # Test DELETE
            deleted = self.client.delete(key)
            if deleted:
                logger.info(f"✅ DELETE operation successful")
            
            return True
            
        except RedisError as e:
            logger.error(f"❌ Redis operation failed: {str(e)}")
            return False
    
    def test_string_operations(self) -> bool:
        """Test string operations"""
        logger.info("\nTesting string operations...")
        
        try:
            base_key = 'sophia:test:string'
            
            # Test INCR/DECR
            counter_key = f'{base_key}:counter'
            self.client.set(counter_key, 0)
            
            new_val = self.client.incr(counter_key)
            logger.info(f"✅ INCR: counter = {new_val}")
            
            new_val = self.client.incrby(counter_key, 5)
            logger.info(f"✅ INCRBY 5: counter = {new_val}")
            
            new_val = self.client.decr(counter_key)
            logger.info(f"✅ DECR: counter = {new_val}")
            
            # Test APPEND
            text_key = f'{base_key}:text'
            self.client.set(text_key, 'Hello')
            self.client.append(text_key, ' World!')
            result = self.client.get(text_key)
            logger.info(f"✅ APPEND: '{result}'")
            
            # Test MSET/MGET (multiple set/get)
            multi_data = {
                f'{base_key}:1': 'value1',
                f'{base_key}:2': 'value2',
                f'{base_key}:3': 'value3'
            }
            self.client.mset(multi_data)
            values = self.client.mget(list(multi_data.keys()))
            logger.info(f"✅ MSET/MGET: Set and retrieved {len(values)} values")
            
            # Cleanup
            self.client.delete(counter_key, text_key, *multi_data.keys())
            
            return True
            
        except RedisError as e:
            logger.error(f"❌ String operation failed: {str(e)}")
            return False
    
    def test_list_operations(self) -> bool:
        """Test list operations"""
        logger.info("\nTesting list operations...")
        
        try:
            list_key = 'sophia:test:list'
            
            # Test LPUSH/RPUSH
            self.client.lpush(list_key, 'first', 'second', 'third')
            self.client.rpush(list_key, 'last')
            
            # Test LLEN
            length = self.client.llen(list_key)
            logger.info(f"✅ List length: {length}")
            
            # Test LRANGE
            items = self.client.lrange(list_key, 0, -1)
            logger.info(f"✅ List items: {items}")
            
            # Test LPOP/RPOP
            first = self.client.lpop(list_key)
            last = self.client.rpop(list_key)
            logger.info(f"✅ LPOP: '{first}', RPOP: '{last}'")
            
            # Test LINDEX
            item_at_1 = self.client.lindex(list_key, 1)
            logger.info(f"✅ Item at index 1: '{item_at_1}'")
            
            # Set expiry on list
            self.client.expire(list_key, 60)
            logger.info(f"✅ Set expiry on list (60s)")
            
            # Cleanup
            self.client.delete(list_key)
            
            return True
            
        except RedisError as e:
            logger.error(f"❌ List operation failed: {str(e)}")
            return False
    
    def test_hash_operations(self) -> bool:
        """Test hash operations"""
        logger.info("\nTesting hash operations...")
        
        try:
            hash_key = 'sophia:test:hash'
            
            # Test HSET/HGET
            self.client.hset(hash_key, 'field1', 'value1')
            self.client.hset(hash_key, mapping={
                'field2': 'value2',
                'field3': 'value3',
                'timestamp': datetime.utcnow().isoformat(),
                'counter': '0'
            })
            
            value = self.client.hget(hash_key, 'field1')
            logger.info(f"✅ HGET field1: '{value}'")
            
            # Test HGETALL
            all_fields = self.client.hgetall(hash_key)
            logger.info(f"✅ HGETALL: {len(all_fields)} fields")
            
            # Test HKEYS/HVALS
            keys = self.client.hkeys(hash_key)
            vals = self.client.hvals(hash_key)
            logger.info(f"✅ Hash has {len(keys)} keys and {len(vals)} values")
            
            # Test HEXISTS
            exists = self.client.hexists(hash_key, 'field2')
            logger.info(f"✅ HEXISTS field2: {exists}")
            
            # Test HINCRBY
            new_count = self.client.hincrby(hash_key, 'counter', 5)
            logger.info(f"✅ HINCRBY counter by 5: {new_count}")
            
            # Test HDEL
            deleted = self.client.hdel(hash_key, 'field3')
            logger.info(f"✅ HDEL field3: {deleted} field(s) deleted")
            
            # Set expiry
            self.client.expire(hash_key, 60)
            logger.info(f"✅ Set expiry on hash (60s)")
            
            # Cleanup
            self.client.delete(hash_key)
            
            return True
            
        except RedisError as e:
            logger.error(f"❌ Hash operation failed: {str(e)}")
            return False
    
    def test_set_operations(self) -> bool:
        """Test set operations"""
        logger.info("\nTesting set operations...")
        
        try:
            set_key1 = 'sophia:test:set1'
            set_key2 = 'sophia:test:set2'
            
            # Test SADD
            self.client.sadd(set_key1, 'a', 'b', 'c', 'd')
            self.client.sadd(set_key2, 'c', 'd', 'e', 'f')
            
            # Test SCARD (cardinality)
            size1 = self.client.scard(set_key1)
            size2 = self.client.scard(set_key2)
            logger.info(f"✅ Set sizes - set1: {size1}, set2: {size2}")
            
            # Test SMEMBERS
            members1 = self.client.smembers(set_key1)
            logger.info(f"✅ Set1 members: {members1}")
            
            # Test SISMEMBER
            is_member = self.client.sismember(set_key1, 'b')
            logger.info(f"✅ 'b' is member of set1: {is_member}")
            
            # Test set operations
            union = self.client.sunion(set_key1, set_key2)
            logger.info(f"✅ UNION: {union}")
            
            intersection = self.client.sinter(set_key1, set_key2)
            logger.info(f"✅ INTERSECTION: {intersection}")
            
            diff = self.client.sdiff(set_key1, set_key2)
            logger.info(f"✅ DIFFERENCE (set1 - set2): {diff}")
            
            # Test SREM
            removed = self.client.srem(set_key1, 'a')
            logger.info(f"✅ SREM 'a' from set1: {removed} removed")
            
            # Cleanup
            self.client.delete(set_key1, set_key2)
            
            return True
            
        except RedisError as e:
            logger.error(f"❌ Set operation failed: {str(e)}")
            return False
    
    def test_sorted_set_operations(self) -> bool:
        """Test sorted set operations"""
        logger.info("\nTesting sorted set operations...")
        
        try:
            zset_key = 'sophia:test:zset'
            
            # Test ZADD
            self.client.zadd(zset_key, {
                'player1': 100,
                'player2': 200,
                'player3': 150,
                'player4': 300
            })
            
            # Test ZCARD
            size = self.client.zcard(zset_key)
            logger.info(f"✅ Sorted set size: {size}")
            
            # Test ZRANGE (ascending)
            ascending = self.client.zrange(zset_key, 0, -1, withscores=True)
            logger.info(f"✅ ZRANGE (ascending): {ascending}")
            
            # Test ZREVRANGE (descending)
            descending = self.client.zrevrange(zset_key, 0, 2, withscores=True)
            logger.info(f"✅ ZREVRANGE (top 3): {descending}")
            
            # Test ZSCORE
            score = self.client.zscore(zset_key, 'player2')
            logger.info(f"✅ ZSCORE for player2: {score}")
            
            # Test ZINCRBY
            new_score = self.client.zincrby(zset_key, 50, 'player1')
            logger.info(f"✅ ZINCRBY player1 by 50: new score = {new_score}")
            
            # Test ZRANK
            rank = self.client.zrank(zset_key, 'player3')
            logger.info(f"✅ ZRANK for player3: {rank} (0-based)")
            
            # Cleanup
            self.client.delete(zset_key)
            
            return True
            
        except RedisError as e:
            logger.error(f"❌ Sorted set operation failed: {str(e)}")
            return False
    
    def test_expiry_operations(self) -> bool:
        """Test expiry-related operations"""
        logger.info("\nTesting expiry operations...")
        
        try:
            key = 'sophia:test:expiry'
            
            # Set key with value
            self.client.set(key, 'test_value')
            
            # Test EXPIRE
            self.client.expire(key, 120)
            ttl = self.client.ttl(key)
            logger.info(f"✅ EXPIRE: TTL = {ttl} seconds")
            
            # Test PERSIST (remove expiry)
            self.client.persist(key)
            ttl = self.client.ttl(key)
            logger.info(f"✅ PERSIST: TTL = {ttl} (-1 means no expiry)")
            
            # Test EXPIREAT
            expire_time = datetime.utcnow() + timedelta(minutes=2)
            expire_timestamp = int(expire_time.timestamp())
            self.client.expireat(key, expire_timestamp)
            ttl = self.client.ttl(key)
            logger.info(f"✅ EXPIREAT: TTL = {ttl} seconds")
            
            # Test SETEX (SET with EXpiry)
            self.client.setex('sophia:test:setex', 60, 'expires in 60s')
            logger.info(f"✅ SETEX: Key set with 60s expiry")
            
            # Cleanup
            self.client.delete(key, 'sophia:test:setex')
            
            return True
            
        except RedisError as e:
            logger.error(f"❌ Expiry operation failed: {str(e)}")
            return False
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get Redis server information"""
        logger.info("\nGetting server information...")
        
        try:
            info = self.client.info()
            
            # Extract key metrics
            metrics = {
                'version': info.get('redis_version', 'unknown'),
                'mode': info.get('redis_mode', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'unknown'),
                'used_memory_peak_human': info.get('used_memory_peak_human', 'unknown'),
                'total_connections_received': info.get('total_connections_received', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0),
                'uptime_in_days': info.get('uptime_in_days', 0)
            }
            
            # Log key metrics
            logger.info(f"✅ Redis Version: {metrics['version']}")
            logger.info(f"✅ Mode: {metrics['mode']}")
            logger.info(f"✅ Connected Clients: {metrics['connected_clients']}")
            logger.info(f"✅ Used Memory: {metrics['used_memory_human']}")
            logger.info(f"✅ Operations/sec: {metrics['instantaneous_ops_per_sec']}")
            logger.info(f"✅ Uptime: {metrics['uptime_in_days']} days")
            
            return metrics
            
        except RedisError as e:
            logger.error(f"❌ Failed to get server info: {str(e)}")
            return {}
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all Redis tests"""
        results = {}
        
        # Connect to Redis
        if not self.connect():
            logger.error("Failed to connect to Redis. Aborting tests.")
            return {'connection': False}
        
        results['connection'] = True
        
        # Run tests
        test_methods = [
            ('basic_operations', self.test_basic_operations),
            ('string_operations', self.test_string_operations),
            ('list_operations', self.test_list_operations),
            ('hash_operations', self.test_hash_operations),
            ('set_operations', self.test_set_operations),
            ('sorted_set_operations', self.test_sorted_set_operations),
            ('expiry_operations', self.test_expiry_operations)
        ]
        
        for test_name, test_method in test_methods:
            try:
                results[test_name] = test_method()
            except Exception as e:
                logger.error(f"Error in {test_name}: {str(e)}")
                results[test_name] = False
        
        # Get server info
        self.get_server_info()
        
        return results

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Redis Connectivity and Operations Test")
    logger.info("=" * 60)
    
    try:
        tester = RedisTester()
        results = tester.run_all_tests()
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        for test_name, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        
        # Overall status
        all_success = all(results.values())
        
        logger.info("\n" + "=" * 60)
        if all_success:
            logger.info("🎉 All Redis tests passed successfully!")
            logger.info("Redis is ready for use with Sophia AI.")
        else:
            failed_tests = [name for name, success in results.items() if not success]
            logger.error(f"⚠️ {len(failed_tests)} test(s) failed: {', '.join(failed_tests)}")
            logger.error("Please check Redis configuration and try again.")
        logger.info("=" * 60)
        
        sys.exit(0 if all_success else 1)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()