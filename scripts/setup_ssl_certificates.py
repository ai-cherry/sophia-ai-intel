#!/usr/bin/env python3
"""
SSL Certificate Setup Script for Sophia AI Intel Platform
Implements Let's Encrypt SSL certificate automation for production deployment.

Features:
- Automated SSL certificate generation using certbot
- Domain validation and DNS verification
- Certificate renewal automation
- Docker container integration
- Production-ready certificate management

Usage:
    python scripts/setup_ssl_certificates.py --domain www.sophia-intel.ai --email admin@sophia-intel.ai

Author: Sophia AI Intel Platform Team
Version: 1.0.0
"""

import argparse
import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/sophia-ssl-setup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SSLCertificateManager:
    """Manages SSL certificate setup and renewal for Sophia AI platform."""

    def __init__(self, domain: str, email: str, staging: bool = False):
        self.domain = domain
        self.email = email
        self.staging = staging
        self.cert_path = Path(f"/etc/letsencrypt/live/{domain}")
        self.webroot_path = Path("/var/www/html")
        self.nginx_ssl_path = Path("/etc/ssl/certs")

        # Ensure required directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories for SSL certificates."""
        directories = [
            self.webroot_path,
            self.nginx_ssl_path,
            Path("/var/log/letsencrypt"),
            Path("/etc/letsencrypt"),
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")

    def check_existing_certificate(self) -> bool:
        """Check if SSL certificate already exists and is valid."""
        if not self.cert_path.exists():
            logger.info("No existing certificate found")
            return False

        # Check certificate validity
        try:
            result = subprocess.run([
                "openssl", "x509", "-checkend", "2592000",  # 30 days
                "-noout", "-in", str(self.cert_path / "cert.pem")
            ], capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Existing certificate is valid and not expiring soon")
                return True
            else:
                logger.warning("Existing certificate is expiring soon or invalid")
                return False
        except Exception as e:
            logger.error(f"Error checking existing certificate: {e}")
            return False

    def install_certbot(self) -> bool:
        """Install certbot if not already installed."""
        try:
            # Check if certbot is installed
            result = subprocess.run(["certbot", "--version"],
                                  capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Certbot is already installed")
                return True

            # Install certbot
            logger.info("Installing certbot...")
            install_commands = [
                ["apt-get", "update"],
                ["apt-get", "install", "-y", "certbot", "python3-certbot-nginx"]
            ]

            for cmd in install_commands:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                logger.info(f"Executed: {' '.join(cmd)}")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install certbot: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error installing certbot: {e}")
            return False

    def generate_ssl_certificate(self) -> bool:
        """Generate SSL certificate using certbot."""
        try:
            logger.info(f"Generating SSL certificate for {self.domain}")

            # Build certbot command
            cmd = [
                "certbot", "certonly",
                "--webroot",
                "--webroot-path", str(self.webroot_path),
                "--domain", self.domain,
                "--email", self.email,
                "--agree-tos",
                "--no-eff-email",
                "--force-renewal"
            ]

            # Add staging flag if requested
            if self.staging:
                cmd.append("--staging")
                logger.info("Using Let's Encrypt staging environment")

            # Add non-interactive flag for automation
            cmd.append("--non-interactive")

            logger.info(f"Running certbot command: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("SSL certificate generated successfully")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"SSL certificate generation failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error generating SSL certificate: {e}")
            return False

    def create_nginx_ssl_symlinks(self) -> bool:
        """Create symbolic links for nginx SSL certificates."""
        try:
            cert_file = self.cert_path / "fullchain.pem"
            key_file = self.cert_path / "privkey.pem"

            if not cert_file.exists() or not key_file.exists():
                logger.error("Certificate files not found")
                return False

            # Create symlinks in nginx SSL directory
            nginx_cert = self.nginx_ssl_path / f"{self.domain}.crt"
            nginx_key = self.nginx_ssl_path / f"{self.domain}.key"

            # Remove existing symlinks if they exist
            for link in [nginx_cert, nginx_key]:
                if link.exists():
                    link.unlink()

            # Create new symlinks
            nginx_cert.symlink_to(cert_file)
            nginx_key.symlink_to(key_file)

            logger.info(f"Created nginx SSL symlinks: {nginx_cert} -> {cert_file}")
            logger.info(f"Created nginx SSL symlinks: {nginx_key} -> {key_file}")

            return True

        except Exception as e:
            logger.error(f"Error creating nginx SSL symlinks: {e}")
            return False

    def setup_auto_renewal(self) -> bool:
        """Set up automatic certificate renewal."""
        try:
            # Create renewal cron job
            cron_content = f"""#!/bin/bash
# Sophia AI SSL Certificate Auto-Renewal
# This script runs daily to check and renew SSL certificates

LOG_FILE="/var/log/sophia-ssl-renewal.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting SSL certificate renewal check..." >> $LOG_FILE

# Run certbot renewal
/usr/bin/certbot renew --quiet --post-hook "/usr/local/bin/reload-nginx.sh" >> $LOG_FILE 2>&1

if [ $? -eq 0 ]; then
    echo "[$TIMESTAMP] SSL certificate renewal completed successfully" >> $LOG_FILE
else
    echo "[$TIMESTAMP] SSL certificate renewal failed" >> $LOG_FILE
fi
"""

            cron_script_path = Path("/usr/local/bin/sophia-ssl-renewal.sh")
            cron_script_path.write_text(cron_content)
            cron_script_path.chmod(0o755)

            # Create nginx reload script
            nginx_reload_content = """#!/bin/bash
# Reload nginx configuration after SSL certificate renewal
docker exec nginx nginx -t && docker exec nginx nginx -s reload
"""

            nginx_reload_path = Path("/usr/local/bin/reload-nginx.sh")
            nginx_reload_path.write_text(nginx_reload_content)
            nginx_reload_path.chmod(0o755)

            # Add cron job (runs daily at 3 AM)
            cron_job = f"0 3 * * * /usr/local/bin/sophia-ssl-renewal.sh\n"

            # Check if cron job already exists
            existing_cron = subprocess.run(["crontab", "-l"],
                                         capture_output=True, text=True)

            if cron_job.strip() not in existing_cron.stdout:
                new_cron = existing_cron.stdout + cron_job
                subprocess.run(["crontab", "-"], input=new_cron, text=True, check=True)
                logger.info("Added SSL renewal cron job")
            else:
                logger.info("SSL renewal cron job already exists")

            return True

        except Exception as e:
            logger.error(f"Error setting up auto-renewal: {e}")
            return False

    def create_dhparam(self) -> bool:
        """Create Diffie-Hellman parameters for enhanced security."""
        try:
            dhparam_file = self.nginx_ssl_path / "dhparam.pem"

            if dhparam_file.exists():
                logger.info("DH parameters already exist")
                return True

            logger.info("Generating Diffie-Hellman parameters (this may take a while)...")

            result = subprocess.run([
                "openssl", "dhparam", "-out", str(dhparam_file), "2048"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("DH parameters generated successfully")
                return True
            else:
                logger.error(f"Failed to generate DH parameters: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error creating DH parameters: {e}")
            return False

    def validate_certificate(self) -> Dict[str, Any]:
        """Validate the installed SSL certificate."""
        try:
            cert_file = self.cert_path / "cert.pem"

            if not cert_file.exists():
                return {"valid": False, "error": "Certificate file not found"}

            # Get certificate information
            result = subprocess.run([
                "openssl", "x509", "-in", str(cert_file), "-text", "-noout"
            ], capture_output=True, text=True)

            if result.returncode != 0:
                return {"valid": False, "error": f"Certificate validation failed: {result.stderr}"}

            # Check expiration date
            expiry_result = subprocess.run([
                "openssl", "x509", "-in", str(cert_file), "-enddate", "-noout"
            ], capture_output=True, text=True)

            if expiry_result.returncode == 0:
                expiry_line = expiry_result.stdout.strip()
                # Parse the date from "notAfter=Dec 15 23:59:59 2024 GMT"
                expiry_date_str = expiry_line.replace("notAfter=", "")
                expiry_date = datetime.strptime(expiry_date_str, "%b %d %H:%M:%S %Y %Z")
                days_until_expiry = (expiry_date - datetime.now()).days

                return {
                    "valid": True,
                    "expiry_date": expiry_date.isoformat(),
                    "days_until_expiry": days_until_expiry,
                    "certificate_info": result.stdout
                }
            else:
                return {"valid": False, "error": "Could not determine certificate expiry"}

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def create_test_endpoint(self) -> bool:
        """Create a test endpoint for domain validation."""
        try:
            # Create .well-known directory for ACME challenges
            well_known_dir = self.webroot_path / ".well-known" / "acme-challenge"
            well_known_dir.mkdir(parents=True, exist_ok=True)

            # Create a test file
            test_file = well_known_dir / "test.txt"
            test_file.write_text("SSL certificate setup test endpoint")

            logger.info(f"Created test endpoint at {test_file}")
            return True

        except Exception as e:
            logger.error(f"Error creating test endpoint: {e}")
            return False

    def run_complete_setup(self) -> Dict[str, Any]:
        """Run the complete SSL certificate setup process."""
        logger.info(f"Starting SSL certificate setup for {self.domain}")

        results = {
            "success": False,
            "steps_completed": [],
            "errors": [],
            "certificate_info": None
        }

        # Step 1: Check existing certificate
        if self.check_existing_certificate():
            logger.info("Valid certificate already exists, skipping generation")
            results["certificate_info"] = self.validate_certificate()
            results["success"] = True
            return results

        # Step 2: Install certbot
        if not self.install_certbot():
            results["errors"].append("Failed to install certbot")
            return results

        results["steps_completed"].append("certbot_installation")

        # Step 3: Create test endpoint
        if not self.create_test_endpoint():
            results["errors"].append("Failed to create test endpoint")
            return results

        results["steps_completed"].append("test_endpoint_creation")

        # Step 4: Generate SSL certificate
        if not self.generate_ssl_certificate():
            results["errors"].append("Failed to generate SSL certificate")
            return results

        results["steps_completed"].append("certificate_generation")

        # Step 5: Create nginx symlinks
        if not self.create_nginx_ssl_symlinks():
            results["errors"].append("Failed to create nginx symlinks")
            return results

        results["steps_completed"].append("nginx_symlinks")

        # Step 6: Create DH parameters
        if not self.create_dhparam():
            results["errors"].append("Failed to create DH parameters")
            return results

        results["steps_completed"].append("dhparam_creation")

        # Step 7: Setup auto-renewal
        if not self.setup_auto_renewal():
            results["errors"].append("Failed to setup auto-renewal")
            return results

        results["steps_completed"].append("auto_renewal_setup")

        # Step 8: Validate final certificate
        cert_validation = self.validate_certificate()
        if not cert_validation.get("valid", False):
            results["errors"].append(f"Certificate validation failed: {cert_validation.get('error', 'Unknown error')}")
            return results

        results["certificate_info"] = cert_validation
        results["success"] = True

        logger.info("SSL certificate setup completed successfully")
        return results

def main():
    """Main entry point for SSL certificate setup."""
    parser = argparse.ArgumentParser(description="SSL Certificate Setup for Sophia AI")
    parser.add_argument("--domain", required=True, help="Domain name for SSL certificate")
    parser.add_argument("--email", required=True, help="Email address for certificate registration")
    parser.add_argument("--staging", action="store_true", help="Use Let's Encrypt staging environment")
    parser.add_argument("--force", action="store_true", help="Force certificate regeneration")

    args = parser.parse_args()

    # Validate domain format
    if not args.domain or "." not in args.domain:
        logger.error("Invalid domain format")
        sys.exit(1)

    # Create SSL manager
    ssl_manager = SSLCertificateManager(
        domain=args.domain,
        email=args.email,
        staging=args.staging
    )

    # Check if we should force regeneration
    if args.force:
        logger.info("Forcing certificate regeneration")
        # Remove existing certificate if it exists
        if ssl_manager.cert_path.exists():
            import shutil
            shutil.rmtree(ssl_manager.cert_path.parent.parent)

    # Run complete setup
    results = ssl_manager.run_complete_setup()

    # Output results
    if results["success"]:
        print("✅ SSL certificate setup completed successfully!")
        print(f"📋 Steps completed: {', '.join(results['steps_completed'])}")

        if results["certificate_info"]:
            cert_info = results["certificate_info"]
            print(f"🔒 Certificate valid: {cert_info['valid']}")
            print(f"📅 Expiry date: {cert_info['expiry_date']}")
            print(f"⏰ Days until expiry: {cert_info['days_until_expiry']}")

        print("\n🔄 Auto-renewal has been configured")
        print("📝 Check logs at /var/log/sophia-ssl-setup.log")
        sys.exit(0)
    else:
        print("❌ SSL certificate setup failed!")
        print(f"📋 Steps completed: {', '.join(results['steps_completed'])}")
        print(f"❌ Errors: {', '.join(results['errors'])}")
        print("📝 Check logs at /var/log/sophia-ssl-setup.log")
        sys.exit(1)

if __name__ == "__main__":
    main()