#!/usr/bin/env python3
"""
Redis Diagnostic Script
Detailed analysis of Redis connectivity issues
"""

import redis
import os
from dotenv import load_dotenv
import logging
import socket
import ssl

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedisDiagnostic:
    def __init__(self):
        load_dotenv()
        self.redis_config = {
            "host": os.getenv("REDIS_HOST"),
            "port": int(os.getenv("REDIS_PORT", 6379)),
            "username": os.getenv("REDIS_USERNAME"),
            "password": os.getenv("REDIS_PASSWORD"),
            "url": os.getenv("REDIS_URL")
        }

    def test_basic_connectivity(self):
        """Test basic TCP connectivity to Redis server"""
        logger.info("Testing basic TCP connectivity")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.redis_config["host"], self.redis_config["port"]))
            sock.close()

            if result == 0:
                logger.info("✅ Basic TCP connectivity successful")
                return True
            else:
                logger.error(f"❌ Basic TCP connectivity failed (error code: {result})")
                return False
        except Exception as e:
            logger.error(f"❌ Basic TCP connectivity error: {e}")
            return False

    def test_redis_no_auth(self):
        """Test Redis connection without authentication"""
        logger.info("Testing Redis connection without authentication")

        try:
            r = redis.Redis(
                host=self.redis_config["host"],
                port=self.redis_config["port"],
                decode_responses=True,
                socket_timeout=5
            )
            r.ping()
            logger.info("✅ Redis connection without auth successful")
            return True, r
        except Exception as e:
            logger.error(f"❌ Redis connection without auth failed: {e}")
            return False, None

    def test_redis_with_auth(self):
        """Test Redis connection with authentication"""
        logger.info("Testing Redis connection with authentication")

        try:
            r = redis.Redis(
                host=self.redis_config["host"],
                port=self.redis_config["port"],
                username=self.redis_config["username"],
                password=self.redis_config["password"],
                decode_responses=True,
                socket_timeout=5
            )
            r.ping()
            logger.info("✅ Redis connection with auth successful")
            return True, r
        except Exception as e:
            logger.error(f"❌ Redis connection with auth failed: {e}")
            return False, None

    def test_redis_with_url(self):
        """Test Redis connection using URL"""
        logger.info("Testing Redis connection with URL")

        try:
            r = redis.from_url(self.redis_config["url"], decode_responses=True, socket_timeout=5)
            r.ping()
            logger.info("✅ Redis connection with URL successful")
            return True, r
        except Exception as e:
            logger.error(f"❌ Redis connection with URL failed: {e}")
            return False, None

    def test_redis_ssl(self):
        """Test Redis connection with SSL"""
        logger.info("Testing Redis connection with SSL")

        try:
            r = redis.Redis(
                host=self.redis_config["host"],
                port=self.redis_config["port"],
                username=self.redis_config["username"],
                password=self.redis_config["password"],
                ssl=True,
                ssl_cert_reqs=ssl.CERT_NONE,
                decode_responses=True,
                socket_timeout=5
            )
            r.ping()
            logger.info("✅ Redis connection with SSL successful")
            return True, r
        except Exception as e:
            logger.error(f"❌ Redis connection with SSL failed: {e}")
            return False, None

    def test_redis_different_db(self):
        """Test Redis connection with different database"""
        logger.info("Testing Redis connection with different database")

        for db in [0, 1, 2]:
            try:
                r = redis.Redis(
                    host=self.redis_config["host"],
                    port=self.redis_config["port"],
                    username=self.redis_config["username"],
                    password=self.redis_config["password"],
                    db=db,
                    decode_responses=True,
                    socket_timeout=5
                )
                r.ping()
                logger.info(f"✅ Redis connection with DB {db} successful")
                return True, r
            except Exception as e:
                logger.error(f"❌ Redis connection with DB {db} failed: {e}")

        return False, None

    def diagnose_redis_issues(self):
        """Comprehensive Redis diagnosis"""
        logger.info("Starting comprehensive Redis diagnosis")
        logger.info(f"Redis Configuration: {self.redis_config}")

        # Test basic connectivity
        tcp_ok = self.test_basic_connectivity()

        if not tcp_ok:
            logger.error("🔴 DIAGNOSIS: Cannot reach Redis server at network level")
            logger.error("Possible issues:")
            logger.error("1. Redis server is not running")
            logger.error("2. Firewall blocking connection")
            logger.error("3. Wrong host/port configuration")
            logger.error("4. Network connectivity issues")
            return

        # Test different connection methods
        logger.info("\n" + "="*50)
        logger.info("TESTING DIFFERENT CONNECTION METHODS")
        logger.info("="*50)

        results = {}

        # Test without auth
        no_auth_ok, _ = self.test_redis_no_auth()
        results["no_auth"] = no_auth_ok

        # Test with auth
        auth_ok, redis_client = self.test_redis_with_auth()
        results["auth"] = auth_ok

        # Test with URL
        url_ok, _ = self.test_redis_with_url()
        results["url"] = url_ok

        # Test with SSL
        ssl_ok, _ = self.test_redis_ssl()
        results["ssl"] = ssl_ok

        # Test different DBs
        db_ok, _ = self.test_redis_different_db()
        results["db"] = db_ok

        logger.info("\n" + "="*50)
        logger.info("DIAGNOSIS SUMMARY")
        logger.info("="*50)

        if auth_ok:
            logger.info("✅ SUCCESS: Redis authentication is working correctly")
            if redis_client:
                try:
                    info = redis_client.info()
                    logger.info(f"Redis version: {info.get('redis_version', 'Unknown')}")
                    logger.info(f"Connected clients: {info.get('connected_clients', 'Unknown')}")
                    logger.info(f"Used memory: {info.get('used_memory_human', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Could not get Redis info: {e}")
        else:
            logger.error("❌ FAILURE: Redis authentication is not working")
            logger.info("\nTroubleshooting steps:")
            logger.info("1. Verify Redis server is running and accepting connections")
            logger.info("2. Check if Redis is configured for authentication")
            logger.info("3. Verify username/password are correct")
            logger.info("4. Check if Redis requires SSL connection")
            logger.info("5. Verify Redis ACL configuration if using Redis 6+")

            if no_auth_ok:
                logger.info("6. Redis accepts connections without auth - auth might be optional")
            else:
                logger.info("6. Redis rejects all connections - check server status")

            if url_ok:
                logger.info("7. URL-based connection works - check individual parameters")

        return results

def main():
    """Main execution function"""
    diagnostic = RedisDiagnostic()
    results = diagnostic.diagnose_redis_issues()

    print("\n" + "="*80)
    print("REDIS DIAGNOSTIC COMPLETE")
    print("="*80)

    if results:
        successful_methods = [k for k, v in results.items() if v]
        failed_methods = [k for k, v in results.items() if not v]

        print(f"Successful methods: {successful_methods}")
        print(f"Failed methods: {failed_methods}")

        if "auth" in successful_methods:
            print("✅ Redis authentication is working correctly")
        else:
            print("❌ Redis authentication needs to be fixed")
    else:
        print("❌ Could not complete Redis diagnosis")

if __name__ == "__main__":
    main()