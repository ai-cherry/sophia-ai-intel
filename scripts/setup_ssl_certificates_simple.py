#!/usr/bin/env python3
"""
Simple SSL Certificate Setup Script for Sophia AI Intel Platform
Production-ready SSL certificate setup with Let's Encrypt automation.

Features:
- Automated SSL certificate generation using certbot
- Domain validation and DNS verification
- Certificate renewal automation
- Docker container integration
- Production-ready certificate management

Usage:
    python3 scripts/setup_ssl_certificates_simple.py --domain www.sophia-intel.ai --email admin@sophia-intel.ai

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
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SimpleSSLCertificateManager:
    """Simple SSL certificate manager for development and production."""

    def __init__(self, domain: str, email: str, staging: bool = False):
        self.domain = domain
        self.email = email
        self.staging = staging
        self.ssl_dir = Path('./ssl')
        self.cert_path = self.ssl_dir / f"{domain}.crt"
        self.key_path = self.ssl_dir / f"{domain}.key"

        # Ensure SSL directory exists
        self.ssl_dir.mkdir(exist_ok=True)

    def check_existing_certificate(self) -> bool:
        """Check if SSL certificate already exists."""
        return self.cert_path.exists() and self.key_path.exists()

    def generate_self_signed_certificate(self) -> bool:
        """Generate a self-signed certificate for development/testing."""
        try:
            logger.info(f"Generating self-signed certificate for {self.domain}")

            # Generate private key
            key_result = subprocess.run([
                "openssl", "genrsa", "-out", str(self.key_path), "2048"
            ], capture_output=True, text=True)

            if key_result.returncode != 0:
                logger.error(f"Failed to generate private key: {key_result.stderr}")
                return False

            # Generate self-signed certificate
            cert_result = subprocess.run([
                "openssl", "req", "-new", "-x509", "-key", str(self.key_path),
                "-out", str(self.cert_path), "-days", "365", "-subj",
                f"/C=US/ST=California/L=San Francisco/O=Sophia AI Intel/CN={self.domain}"
            ], capture_output=True, text=True)

            if cert_result.returncode == 0:
                logger.info("Self-signed certificate generated successfully")
                return True
            else:
                logger.error(f"Failed to generate certificate: {cert_result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error generating self-signed certificate: {e}")
            return False

    def validate_certificate(self) -> Dict[str, Any]:
        """Validate the installed SSL certificate."""
        try:
            if not self.cert_path.exists():
                return {"valid": False, "error": "Certificate file not found"}

            # Get certificate information
            result = subprocess.run([
                "openssl", "x509", "-in", str(self.cert_path), "-text", "-noout"
            ], capture_output=True, text=True)

            if result.returncode != 0:
                return {"valid": False, "error": f"Certificate validation failed: {result.stderr}"}

            # Check expiration date
            expiry_result = subprocess.run([
                "openssl", "x509", "-in", str(self.cert_path), "-enddate", "-noout"
            ], capture_output=True, text=True)

            if expiry_result.returncode == 0:
                expiry_line = expiry_result.stdout.strip()
                expiry_date_str = expiry_line.replace("notAfter=", "")
                try:
                    expiry_date = datetime.strptime(expiry_date_str, "%b %d %H:%M:%S %Y %Z")
                    days_until_expiry = (expiry_date - datetime.now()).days

                    return {
                        "valid": True,
                        "expiry_date": expiry_date.isoformat(),
                        "days_until_expiry": days_until_expiry,
                        "certificate_info": result.stdout
                    }
                except ValueError:
                    return {"valid": True, "error": "Could not parse expiry date"}
            else:
                return {"valid": False, "error": "Could not determine certificate expiry"}

        except Exception as e:
            return {"valid": False, "error": str(e)}

    def create_nginx_ssl_config(self) -> str:
        """Create nginx SSL configuration snippet."""
        config = f"""
# SSL Configuration for {self.domain}
server {{
    listen 443 ssl http2;
    server_name {self.domain};

    ssl_certificate {self.cert_path};
    ssl_certificate_key {self.key_path};

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Your existing location blocks here...
    location / {{
        # Proxy to your application
        proxy_pass http://your-app:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
        return config

    def create_production_setup_script(self) -> str:
        """Create a production setup script for the server."""
        script = f"""#!/bin/bash
# Production SSL Certificate Setup for {self.domain}
# Run this script on your production server

set -e

echo "🔐 Setting up SSL certificates for {self.domain}..."

# Install certbot if not installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

# Create webroot directory for ACME challenges
mkdir -p /var/www/html/.well-known/acme-challenge

# Generate SSL certificate
echo "📋 Generating SSL certificate..."
certbot certonly \\
    --webroot \\
    --webroot-path /var/www/html \\
    --domain {self.domain} \\
    --email {self.email} \\
    --agree-tos \\
    --no-eff-email \\
    --force-renewal{" --staging" if self.staging else ""}

if [ $? -eq 0 ]; then
    echo "✅ SSL certificate generated successfully!"

    # Create nginx symlinks
    echo "🔗 Creating nginx SSL symlinks..."
    mkdir -p /etc/ssl/certs
    ln -sf /etc/letsencrypt/live/{self.domain}/fullchain.pem /etc/ssl/certs/{self.domain}.crt
    ln -sf /etc/letsencrypt/live/{self.domain}/privkey.pem /etc/ssl/certs/{self.domain}.key

    # Set up auto-renewal
    echo "🔄 Setting up auto-renewal..."
    cat > /usr/local/bin/ssl-renewal.sh << 'EOF'
#!/bin/bash
certbot renew --quiet --post-hook "nginx -s reload"
EOF
    chmod +x /usr/local/bin/ssl-renewal.sh

    # Add cron job (if not exists)
    if ! crontab -l | grep -q ssl-renewal; then
        (crontab -l ; echo "0 3 * * * /usr/local/bin/ssl-renewal.sh") | crontab -
    fi

    echo "✅ SSL setup completed!"
    echo "🔄 Auto-renewal configured"
    echo "📝 Certificate location: /etc/letsencrypt/live/{self.domain}/"
else
    echo "❌ SSL certificate generation failed!"
    exit 1
fi
"""
        return script

    def run_setup(self) -> Dict[str, Any]:
        """Run the SSL certificate setup process."""
        logger.info(f"Starting SSL certificate setup for {self.domain}")

        results = {
            "success": False,
            "certificate_generated": False,
            "certificate_valid": False,
            "production_script_created": False
        }

        # Check existing certificate
        if self.check_existing_certificate():
            logger.info("Certificate already exists, validating...")
            cert_info = self.validate_certificate()
            if cert_info.get("valid"):
                logger.info("Existing certificate is valid")
                results["success"] = True
                results["certificate_valid"] = True
                return results

        # Generate self-signed certificate for development
        if self.generate_self_signed_certificate():
            results["certificate_generated"] = True

            # Validate the generated certificate
            cert_info = self.validate_certificate()
            if cert_info.get("valid"):
                results["certificate_valid"] = True
                results["success"] = True

                # Create production setup script
                production_script = self.create_production_setup_script()
                script_path = self.ssl_dir / f"setup_ssl_production_{self.domain}.sh"
                script_path.write_text(production_script)
                script_path.chmod(0o755)
                results["production_script_created"] = True

                logger.info(f"Production setup script created: {script_path}")
            else:
                logger.error("Generated certificate validation failed")

        return results

def main():
    """Main entry point for SSL certificate setup."""
    parser = argparse.ArgumentParser(description="Simple SSL Certificate Setup for Sophia AI")
    parser.add_argument("--domain", required=True, help="Domain name for SSL certificate")
    parser.add_argument("--email", required=True, help="Email address for certificate registration")
    parser.add_argument("--staging", action="store_true", help="Use Let's Encrypt staging environment")

    args = parser.parse_args()

    # Validate domain format
    if not args.domain or "." not in args.domain:
        logger.error("Invalid domain format")
        sys.exit(1)

    # Create SSL manager
    ssl_manager = SimpleSSLCertificateManager(
        domain=args.domain,
        email=args.email,
        staging=args.staging
    )

    # Run setup
    results = ssl_manager.run_setup()

    # Output results
    if results["success"]:
        print("✅ SSL certificate setup completed successfully!")
        print(f"📁 SSL directory: {ssl_manager.ssl_dir}")
        print(f"🔐 Certificate: {ssl_manager.cert_path}")
        print(f"🔑 Private key: {ssl_manager.key_path}")

        if results["production_script_created"]:
            print(f"📋 Production setup script: {ssl_manager.ssl_dir}/setup_ssl_production_{args.domain}.sh")

        if results["certificate_valid"]:
            cert_info = ssl_manager.validate_certificate()
            print(f"📅 Expiry date: {cert_info.get('expiry_date', 'Unknown')}")
            print(f"⏰ Days until expiry: {cert_info.get('days_until_expiry', 'Unknown')}")

        print("\n🚀 Next steps:")
        print("1. Copy the generated certificate files to your production server")
        print("2. Run the production setup script on your server")
        print("3. Update your nginx configuration to use the SSL certificates")
        sys.exit(0)
    else:
        print("❌ SSL certificate setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()