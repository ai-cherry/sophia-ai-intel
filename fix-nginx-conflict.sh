#!/bin/bash

# Create temporary SSH key file
TMP_KEY_FILE=$(mktemp)
echo "-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACD7o6LbAggKrpqP5/WWcFWVHI8vC7t9YPq2UXeVZcfs0AAAAKhOiNSdTojU
nQAAAAtzc2gtZWQyNTUxOQAAACD7o6LbAggKrpqP5/WWcFWVHI8vC7t9YPq2UXeVZcfs0A
AAAEAGUPlkGE0k0DKawkILgrUEnx6e9VZmEbpx5LolLW6NjvujotsCCAqumo/n9ZZwVZUc
jy8Lu31g+rZRd5Vlx+zQAAAAIlNPUEhJQSBQcm9kdWN0aW9uIEtleSAtIDIwMjUtMDgtMT
UBAgM=
-----END OPENSSH PRIVATE KEY-----" > "$TMP_KEY_FILE"
chmod 600 "$TMP_KEY_FILE"

echo "🔧 Stopping system nginx and restarting deployment..."

# Stop system nginx and restart deployment
ssh -o StrictHostKeyChecking=no -i "$TMP_KEY_FILE" ubuntu@192.222.51.223 "sudo systemctl stop nginx && sudo systemctl disable nginx && cd /home/ubuntu/sophia-ai-intel && docker-compose up -d --build"

echo "✅ System nginx stopped and deployment restarted"

# Clean up
rm -f "$TMP_KEY_FILE"