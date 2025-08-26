#!/bin/bash
# Enterprise SSL Certificate Setup with Let's Encrypt
# Production-ready SSL deployment for www.sophia-intel.ai

set -e

DOMAIN="www.sophia-intel.ai"
EMAIL="admin@sophia-intel.ai"
WEBROOT_PATH="/var/www/html"
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}"
DOCKER_CERT_PATH="/etc/ssl/certs"

echo "🔐 Setting up Enterprise SSL certificates for ${DOMAIN}..."

# Check if running on the target server
if [[ "$1" == "local" ]]; then
    echo "🏠 Running in local mode - setting up for Docker deployment"
    LOCAL_MODE=true
else
    echo "🌐 Running on production server"
    LOCAL_MODE=false
fi

# Function to install certbot
install_certbot() {
    echo "📦 Installing certbot and nginx plugin..."
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    elif command -v yum &> /dev/null; then
        yum install -y certbot python3-certbot-nginx
    elif command -v dnf &> /dev/null; then
        dnf install -y certbot python3-certbot-nginx
    else
        echo "❌ Unsupported package manager"
        exit 1
    fi
}

# Function to generate certificates
generate_certificates() {
    echo "📋 Generating SSL certificates..."

    if [[ "$LOCAL_MODE" == true ]]; then
        # Local mode - generate self-signed certificates for testing
        echo "🔧 Generating self-signed certificates for local development..."

        # Create certificate directory
        mkdir -p "${DOCKER_CERT_PATH}"

        # Generate private key
        openssl genrsa -out "${DOCKER_CERT_PATH}/${DOMAIN}.key" 4096

        # Generate certificate signing request
        openssl req -new -key "${DOCKER_CERT_PATH}/${DOMAIN}.key" \
            -out "${DOCKER_CERT_PATH}/${DOMAIN}.csr" \
            -subj "/C=US/ST=California/L=San Francisco/O=Sophia AI/OU=Engineering/CN=${DOMAIN}"

        # Generate self-signed certificate
        openssl x509 -req -days 365 -in "${DOCKER_CERT_PATH}/${DOMAIN}.csr" \
            -signkey "${DOCKER_CERT_PATH}/${DOMAIN}.key" \
            -out "${DOCKER_CERT_PATH}/${DOMAIN}.crt"

        # Create fullchain.pem (same as certificate for self-signed)
        cp "${DOCKER_CERT_PATH}/${DOMAIN}.crt" "${DOCKER_CERT_PATH}/fullchain.pem"

        # Create privkey.pem
        cp "${DOCKER_CERT_PATH}/${DOMAIN}.key" "${DOCKER_CERT_PATH}/privkey.pem"

        # Create combined certificate
        cat "${DOCKER_CERT_PATH}/${DOMAIN}.crt" "${DOCKER_CERT_PATH}/${DOMAIN}.key" > "${DOCKER_CERT_PATH}/combined.pem"

        echo "✅ Self-signed certificates generated"
        echo "📍 Certificate location: ${DOCKER_CERT_PATH}/"
        echo "⚠️  WARNING: These are self-signed certificates for development only"

    else
        # Production mode - use Let's Encrypt
        # Create webroot directory for ACME challenges
        mkdir -p "${WEBROOT_PATH}/.well-known/acme-challenge"

        # Generate certificate
        certbot certonly \
            --webroot \
            --webroot-path "${WEBROOT_PATH}" \
            --domain "${DOMAIN}" \
            --email "${EMAIL}" \
            --agree-tos \
            --no-eff-email \
            --force-renewal \
            --cert-name "${DOMAIN}"

        if [ $? -eq 0 ]; then
            echo "✅ SSL certificates generated successfully!"
            echo "📍 Certificate location: ${CERT_PATH}/"

            # Create symlinks for nginx
            mkdir -p "${DOCKER_CERT_PATH}"
            ln -sf "${CERT_PATH}/fullchain.pem" "${DOCKER_CERT_PATH}/${DOMAIN}.crt"
            ln -sf "${CERT_PATH}/privkey.pem" "${DOCKER_CERT_PATH}/${DOMAIN}.key"
            ln -sf "${CERT_PATH}/fullchain.pem" "${DOCKER_CERT_PATH}/fullchain.pem"
            ln -sf "${CERT_PATH}/privkey.pem" "${DOCKER_CERT_PATH}/privkey.pem"

            # Create combined certificate
            cat "${CERT_PATH}/fullchain.pem" "${CERT_PATH}/privkey.pem" > "${DOCKER_CERT_PATH}/combined.pem"

        else
            echo "❌ SSL certificate generation failed!"
            exit 1
        fi
    fi
}

# Function to setup auto-renewal
setup_auto_renewal() {
    if [[ "$LOCAL_MODE" == true ]]; then
        echo "⏭️  Skipping auto-renewal setup for local mode"
        return
    fi

    echo "🔄 Setting up certificate auto-renewal..."

    # Create renewal script
    cat > /usr/local/bin/ssl-renewal.sh << EOF
#!/bin/bash
# SSL Certificate Auto-Renewal Script

DOMAIN="${DOMAIN}"
CERT_PATH="${CERT_PATH}"
DOCKER_CERT_PATH="${DOCKER_CERT_PATH}"

# Renew certificates
certbot renew --quiet --post-hook "
    # Update symlinks
    ln -sf \${CERT_PATH}/fullchain.pem \${DOCKER_CERT_PATH}/\${DOMAIN}.crt
    ln -sf \${CERT_PATH}/privkey.pem \${DOCKER_CERT_PATH}/\${DOMAIN}.key
    ln -sf \${CERT_PATH}/fullchain.pem \${DOCKER_CERT_PATH}/fullchain.pem
    ln -sf \${CERT_PATH}/privkey.pem \${DOCKER_CERT_PATH}/privkey.pem

    # Create combined certificate
    cat \${CERT_PATH}/fullchain.pem \${CERT_PATH}/privkey.pem > \${DOCKER_CERT_PATH}/combined.pem

    # Reload nginx if running
    if pgrep nginx > /dev/null; then
        nginx -s reload
        echo \"\$(date): SSL certificates renewed and nginx reloaded\" >> /var/log/ssl-renewal.log
    fi
"

# Log renewal
echo "\$(date): SSL renewal check completed" >> /var/log/ssl-renewal.log
EOF

    chmod +x /usr/local/bin/ssl-renewal.sh

    # Add cron job (if not exists)
    if ! crontab -l 2>/dev/null | grep -q ssl-renewal; then
        (crontab -l 2>/dev/null ; echo "0 3 * * * /usr/local/bin/ssl-renewal.sh") | crontab -
        echo "✅ Cron job added for daily SSL renewal checks at 3 AM"
    else
        echo "✅ Cron job already exists for SSL renewal"
    fi

    # Setup log rotation
    cat > /etc/logrotate.d/ssl-renewal << EOF
/var/log/ssl-renewal.log {
    weekly
    missingok
    rotate 4
    compress
    notifempty
    create 644 root root
}
EOF
}

# Function to validate certificates
validate_certificates() {
    echo "🔍 Validating SSL certificates..."

    if [[ "$LOCAL_MODE" == true ]]; then
        CERT_FILE="${DOCKER_CERT_PATH}/${DOMAIN}.crt"
    else
        CERT_FILE="${DOCKER_CERT_PATH}/${DOMAIN}.crt"
    fi

    if [ -f "$CERT_FILE" ]; then
        echo "📋 Certificate information:"
        openssl x509 -in "$CERT_FILE" -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:)"

        echo ""
        echo "🔗 Certificate chain validation:"
        openssl verify -CAfile "$CERT_FILE" "$CERT_FILE" 2>/dev/null && echo "✅ Certificate chain is valid" || echo "⚠️  Certificate chain validation failed (expected for self-signed)"

        echo ""
        echo "🔐 Private key validation:"
        openssl rsa -in "${DOCKER_CERT_PATH}/${DOMAIN}.key" -check && echo "✅ Private key is valid" || echo "❌ Private key validation failed"
    else
        echo "❌ Certificate file not found: $CERT_FILE"
        exit 1
    fi
}

# Function to create nginx SSL configuration
create_nginx_ssl_config() {
    echo "📝 Creating production nginx SSL configuration..."

    cat > nginx.conf.ssl.production << EOF
# Sophia AI Production Nginx Configuration with Enterprise SSL
# Unified reverse proxy for Lambda Labs + Kubernetes deployment

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging format
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for" '
                    'rt=\$request_time uct="\$upstream_connect_time" '
                    'uht="\$upstream_header_time" urt="\$upstream_response_time"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Performance optimizations
    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=health:10m rate=1r/s;

    # Upstream servers
    upstream agno_coordinator {
        server agno-coordinator:8080;
        keepalive 32;
    }

    upstream mcp_agents {
        server mcp-agents:8000;
        keepalive 32;
    }

    upstream mcp_context {
        server mcp-context:8080;
        keepalive 32;
    }

    upstream mcp_github {
        server mcp-github:8080;
        keepalive 32;
    }

    upstream mcp_hubspot {
        server mcp-hubspot:8080;
        keepalive 32;
    }

    upstream mcp_lambda {
        server mcp-lambda:8080;
        keepalive 32;
    }

    upstream mcp_research {
        server mcp-research:8080;
        keepalive 32;
    }

    upstream mcp_business {
        server mcp-business:8080;
        keepalive 32;
    }

    upstream prometheus {
        server prometheus:9090;
        keepalive 32;
    }

    upstream grafana {
        server grafana:3000;
        keepalive 32;
    }

    upstream loki {
        server loki:3100;
        keepalive 32;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80 default_server;
        server_name _;
        return 301 https://\$host\$request_uri;
    }

    # Production HTTP server block
    server {
        listen 80;
        server_name ${DOMAIN};

        # Health check endpoint (no rate limiting)
        location /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }

        # ACME challenge for Let's Encrypt
        location /.well-known/acme-challenge/ {
            root ${WEBROOT_PATH};
            try_files \$uri =404;
        }

        # Redirect all HTTP traffic to HTTPS
        location / {
            return 301 https://\$host\$request_uri;
        }
    }

    # SSL/TLS configuration
    server {
        listen 443 ssl http2;
        server_name ${DOMAIN};

        # SSL certificate configuration
        ssl_certificate ${DOCKER_CERT_PATH}/${DOMAIN}.crt;
        ssl_certificate_key ${DOCKER_CERT_PATH}/${DOMAIN}.key;

        # SSL protocols and ciphers
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
        ssl_prefer_server_ciphers off;

        # SSL session settings
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        ssl_session_tickets off;

        # HSTS (HTTP Strict Transport Security)
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

        # Security headers
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # OCSP stapling
        ssl_stapling on;
        ssl_stapling_verify on;
        resolver 8.8.8.8 8.8.4.4 valid=300s;
        resolver_timeout 5s;

        # API endpoints with rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://agno_coordinator/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # MCP service endpoints
        location /agents/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://mcp_agents/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /context/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://mcp_context/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /github/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://mcp_github/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /hubspot/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://mcp_hubspot/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /lambda/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://mcp_lambda/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /research/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://mcp_research/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /business/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://mcp_business/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Monitoring endpoints (no rate limiting)
        location /prometheus/ {
            proxy_pass http://prometheus/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        location /grafana/ {
            proxy_pass http://grafana/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;

            # WebSocket support for Grafana
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        location /loki/ {
            proxy_pass http://loki/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Health check endpoint (no rate limiting)
        location /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }

        # Static file serving (if needed in future)
        location /static/ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Error pages
        error_page 404 /404.html;
        error_page 500 502 503 504 /50x.html;
    }
}
EOF

    echo "✅ Production nginx SSL configuration created"
}

# Main execution
main() {
    echo "🚀 Starting SSL certificate setup..."

    if [[ "$LOCAL_MODE" == false ]]; then
        # Check if running as root for production setup
        if [[ $EUID -ne 0 ]]; then
           echo "❌ This script must be run as root for production setup"
           exit 1
        fi

        # Install certbot for production
        install_certbot
    fi

    # Generate certificates
    generate_certificates

    # Setup auto-renewal
    setup_auto_renewal

    # Validate certificates
    validate_certificates

    # Create nginx SSL configuration
    create_nginx_ssl_config

    echo ""
    echo "🎉 SSL setup completed successfully!"
    echo ""
    echo "📋 Summary:"
    if [[ "$LOCAL_MODE" == true ]]; then
        echo "   - Mode: Local Development (Self-signed certificates)"
        echo "   - Certificate type: Self-signed"
    else
        echo "   - Mode: Production"
        echo "   - Certificate type: Let's Encrypt"
        echo "   - Auto-renewal: Configured (daily at 3 AM)"
    fi
    echo "   - Domain: ${DOMAIN}"
    echo "   - Certificate path: ${DOCKER_CERT_PATH}/"
    echo "   - Configuration: nginx.conf.ssl.production"
    echo ""
    echo "🔧 Next steps:"
    echo "   1. Update docker-compose.yml to use nginx.conf.ssl.production"
    echo "   2. Restart nginx container: docker-compose restart nginx"
    echo "   3. Verify SSL: curl -I https://${DOMAIN}/health"
    echo "   4. Test SSL rating: https://www.ssllabs.com/ssltest/analyze.html?d=${DOMAIN}"
    echo ""
    echo "📞 For issues, check logs:"
    echo "   - Certificate logs: /var/log/letsencrypt/"
    echo "   - Renewal logs: /var/log/ssl-renewal.log"
}

# Run main function with all arguments
main "$@"