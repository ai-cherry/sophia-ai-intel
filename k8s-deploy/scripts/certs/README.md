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
