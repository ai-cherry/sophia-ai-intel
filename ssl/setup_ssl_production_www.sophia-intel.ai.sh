#!/bin/bash
# Production SSL Certificate Setup for www.sophia-intel.ai
# Run this script on your production server

set -e

echo "🔐 Setting up SSL certificates for www.sophia-intel.ai..."

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
certbot certonly \
    --webroot \
    --webroot-path /var/www/html \
    --domain www.sophia-intel.ai \
    --email admin@sophia-intel.ai \
    --agree-tos \
    --no-eff-email \
    --force-renewal

if [ $? -eq 0 ]; then
    echo "✅ SSL certificate generated successfully!"

    # Create nginx symlinks
    echo "🔗 Creating nginx SSL symlinks..."
    mkdir -p /etc/ssl/certs
    ln -sf /etc/letsencrypt/live/www.sophia-intel.ai/fullchain.pem /etc/ssl/certs/www.sophia-intel.ai.crt
    ln -sf /etc/letsencrypt/live/www.sophia-intel.ai/privkey.pem /etc/ssl/certs/www.sophia-intel.ai.key

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
    echo "📝 Certificate location: /etc/letsencrypt/live/www.sophia-intel.ai/"
else
    echo "❌ SSL certificate generation failed!"
    exit 1
fi
