#!/bin/bash

# Sophia AI mTLS Certificate Generation Script
# This script generates a Certificate Authority and certificates for all 11 core services

set -e

# Configuration
CERT_DIR="./certs"
CA_KEY="${CERT_DIR}/ca.key"
CA_CERT="${CERT_DIR}/ca.crt"
CA_SUBJECT="/C=US/ST=California/L=San Francisco/O=Sophia AI/OU=Platform/CN=Sophia AI Root CA"
VALIDITY=3650  # 10 years

# Services that need certificates
SERVICES=(
    "orchestrator"
    "agno-coordinator"
    "agno-teams"
    "mcp-context"
    "mcp-agents"
    "mcp-business"
    "mcp-gong"
    "mcp-salesforce"
    "mcp-slack"
    "mcp-apollo"
    "mcp-hubspot"
    "mcp-research"
    "mcp-github"
    "mcp-lambda"
)

# Create certificate directory
mkdir -p "$CERT_DIR"

echo "🔐 Generating Sophia AI mTLS certificates..."

# Generate CA private key
echo "📝 Generating Certificate Authority..."
openssl genrsa -out "$CA_KEY" 4096

# Generate CA certificate
openssl req -x509 -new -nodes -key "$CA_KEY" -sha256 -days "$VALIDITY" \
    -out "$CA_CERT" -subj "$CA_SUBJECT"

echo "✅ CA certificate generated successfully"

# Generate certificates for each service
for service in "${SERVICES[@]}"; do
    echo "🔐 Generating certificate for $service..."

    # Generate private key
    openssl genrsa -out "${CERT_DIR}/${service}.key" 2048

    # Generate CSR
    openssl req -new -key "${CERT_DIR}/${service}.key" \
        -out "${CERT_DIR}/${service}.csr" \
        -subj "/C=US/ST=California/L=San Francisco/O=Sophia AI/OU=Services/CN=${service}.sophia.svc.cluster.local"

    # Generate certificate signed by CA
    openssl x509 -req -in "${CERT_DIR}/${service}.csr" \
        -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial \
        -out "${CERT_DIR}/${service}.crt" \
        -days "$VALIDITY" -sha256

    # Clean up CSR
    rm "${CERT_DIR}/${service}.csr"

    echo "✅ Certificate generated for $service"
done

echo "📄 Creating Kubernetes secret templates..."

# Create base64 encoded versions for Kubernetes secrets
CA_CERT_B64=$(cat "$CA_CERT" | base64 -w 0)
CA_KEY_B64=$(cat "$CA_KEY" | base64 -w 0)

# Update the tls-secrets.yaml file with actual base64 values
TLS_SECRETS_FILE="../secrets/tls-secrets.yaml"

# Replace CA certificate and key placeholders
sed -i.bak "s|<BASE64_ENCODED_CA_CERT>|$CA_CERT_B64|g" "$TLS_SECRETS_FILE"
sed -i.bak "s|<BASE64_ENCODED_CA_KEY>|$CA_KEY_B64|g" "$TLS_SECRETS_FILE"

# Replace service certificates
for service in "${SERVICES[@]}"; do
    service_cert_b64=$(cat "${CERT_DIR}/${service}.crt" | base64 -w 0)
    service_key_b64=$(cat "${CERT_DIR}/${service}.key" | base64 -w 0)

    # Replace in tls-secrets.yaml
    sed -i.bak "s|<BASE64_ENCODED_CERT>|$service_cert_b64|g; s|<BASE64_ENCODED_KEY>|$service_key_b64|g" "$TLS_SECRETS_FILE"
done

echo "✅ Kubernetes secret templates updated with certificates"

# Create certificate bundle for services
echo "📦 Creating certificate bundle for application use..."
cat > "${CERT_DIR}/README.md" << 'EOF'
# Sophia AI mTLS Certificates

This directory contains the generated certificates for mTLS communication between services.

## Files
- `ca.crt` - Certificate Authority certificate (public)
- `ca.key` - Certificate Authority private key (secure this!)
- `{service}.crt` - Service certificate (public)
- `{service}.key` - Service private key (secure this!)

## Usage in Applications

Mount the CA certificate and service certificate/key pair in your application:

```yaml
volumeMounts:
- name: tls-certs
  mountPath: /etc/ssl/certs
  readOnly: true
- name: tls-keys
  mountPath: /etc/ssl/private
  readOnly: true

volumes:
- name: tls-certs
  secret:
    secretName: sophia-ca-cert
- name: tls-keys
  secret:
    secretName: sophia-{service}-tls
```

## Security Notes
- Keep private keys secure and rotate regularly
- Use these certificates only for internal service communication
- Monitor certificate expiration and renew before expiry
EOF

echo "🎉 mTLS certificate generation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Review and apply the TLS secrets: kubectl apply -f ../secrets/tls-secrets.yaml"
echo "2. Update service manifests to mount certificates and enable mTLS"
echo "3. Apply network policies to enforce mTLS-only communication"
echo "4. Test service-to-service communication with TLS verification"

# Display certificate information
echo ""
echo "🔍 Certificate Information:"
echo "CA Subject: $CA_SUBJECT"
echo "Validity: $VALIDITY days"
echo "Services: ${#SERVICES[@]} certificates generated"
echo ""
echo "📍 Certificate files location: $CERT_DIR"