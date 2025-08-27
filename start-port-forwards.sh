#!/bin/bash

echo 'Starting port-forward for comms-mcp on port 8080...'
kubectl port-forward service/comms-mcp 8080:8080 -n sophia &
PID1=$!

echo 'Starting port-forward for crm-mcp on port 8081...'
kubectl port-forward service/crm-mcp 8081:8080 -n sophia &
PID2=$!

echo 'Starting port-forward for analytics-mcp on port 8082...'
kubectl port-forward service/analytics-mcp 8082:8080 -n sophia &
PID3=$!

echo ''
echo 'Port forwarding established:'
echo '  - comms-mcp:    http://localhost:8080'
echo '  - crm-mcp:      http://localhost:8081'
echo '  - analytics-mcp: http://localhost:8082'
echo ''
echo 'Press Ctrl+C to stop all port-forwards'

# Wait for any of the background processes to exit
wait $PID1 $PID2 $PID3
