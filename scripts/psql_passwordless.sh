#!/usr/bin/env bash
set -euo pipefail

# Neon Passwordless Connection Helper Script
# Usage:
#   NEON_PROJECT_ID=rough-... NEON_API_KEY=... ./scripts/psql_passwordless.sh [-u neondb_owner] [-d neondb]

USER="neondb_owner"
DB="neondb"
while getopts "u:d:" opt; do
  case $opt in
    u) USER="$OPTARG" ;;
    d) DB="$OPTARG" ;;
  esac
done

# Detect psql location
if [ -f "/opt/homebrew/opt/postgresql@15/bin/psql" ]; then
  PSQL="/opt/homebrew/opt/postgresql@15/bin/psql"
elif [ -f "/opt/homebrew/opt/postgresql@17/bin/psql" ]; then
  PSQL="/opt/homebrew/opt/postgresql@17/bin/psql"
elif command -v psql >/dev/null 2>&1; then
  PSQL="psql"
else
  echo "❌ psql not found."
  echo ""
  echo "To install:"
  echo "  macOS:  brew install postgresql"
  echo "  Linux:  sudo apt-get install postgresql-client"
  exit 2
fi

echo "Using psql from: $PSQL"
$PSQL --version
echo ""

echo "============================================"
echo "Neon Passwordless Connection Tool"
echo "============================================"
echo "User: $USER"
echo "Database: $DB"
echo ""

# Try SNI method first (modern libpq)
echo "🔗 Attempting SNI passwordless connection..."
if PGSSLMODE=require $PSQL -h pg.neon.tech -U "$USER" -d "$DB" \
   -c "SELECT current_user, current_database(), version();" 2>/dev/null; then
  echo ""
  echo "✅ SNI passwordless connection successful!"
  echo ""
  echo "You can now connect with:"
  echo "  PGSSLMODE=require $PSQL -h pg.neon.tech -U $USER -d $DB"
  exit 0
fi

echo "❌ SNI attempt failed (this is normal for older psql versions)"
echo ""

# Try with explicit endpoint
echo "🔍 Fetching endpoint ID from Neon API..."

# Check for required environment variables
if [[ -z "${NEON_API_KEY:-}" || -z "${NEON_PROJECT_ID:-}" ]]; then
  echo "❌ Need NEON_API_KEY and NEON_PROJECT_ID to auto-discover endpoint."
  echo ""
  echo "Please set:"
  echo "  export NEON_API_KEY=napi_..."
  echo "  export NEON_PROJECT_ID=rough-union-72390895"
  echo ""
  echo "Or use the endpoint directly:"
  echo "  PGSSLMODE=require $PSQL -h pg.neon.tech -U $USER -d $DB --options=endpoint=ep-rough-dew-af6w48m3"
  exit 3
fi

# Fetch endpoints from Neon API
EP_JSON=$(curl -sS -H "Authorization: Bearer $NEON_API_KEY" \
  "https://console.neon.tech/api/v2/projects/$NEON_PROJECT_ID/endpoints") || {
  echo "❌ Failed to query endpoints via REST API"
  exit 4
}

# Parse endpoint ID (looking for read_write type)
EP_ID=$(echo "$EP_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for ep in data.get('endpoints', []):
    if ep.get('type') == 'read_write':
        print(ep.get('id', ''))
        break
" 2>/dev/null) || {
  # Fallback to awk if Python fails
  EP_ID=$(echo "$EP_JSON" | awk '/"type":"read_write"/{f=1} f && /"id":/ {gsub(/[", ]/,""); split($0,a,":"); print a[2]; exit}')
}

if [[ -z "$EP_ID" ]]; then
  echo "❌ Could not find a read_write endpoint in project."
  echo ""
  echo "Endpoints found:"
  echo "$EP_JSON" | python3 -m json.tool 2>/dev/null || echo "$EP_JSON"
  echo ""
  echo "Please create an endpoint for your branch or use the console."
  exit 5
fi

echo "✅ Found endpoint: $EP_ID"
echo ""

# Try connection with explicit endpoint
echo "🔗 Attempting connection with explicit endpoint..."
if PGSSLMODE=require $PSQL -h pg.neon.tech -U "$USER" -d "$DB" \
   --options=endpoint="$EP_ID" \
   -c "SELECT current_user, current_database(), version();" 2>/dev/null; then
  echo ""
  echo "✅ Passwordless connection with explicit endpoint successful!"
  echo ""
  echo "You can now connect with:"
  echo "  PGSSLMODE=require $PSQL -h pg.neon.tech -U $USER -d $DB --options=endpoint=$EP_ID"
  exit 0
fi

# If both methods fail
echo ""
echo "❌ Both connection methods failed."
echo ""
echo "Troubleshooting steps:"
echo "1. Ensure psql is up-to-date:"
echo "   brew upgrade postgresql  # macOS"
echo "   sudo apt-get upgrade postgresql-client  # Linux"
echo ""
echo "2. Verify your endpoint is active in the Neon console:"
echo "   https://console.neon.tech"
echo ""
echo "3. Check project and branch IDs are correct:"
echo "   Project: $NEON_PROJECT_ID"
echo "   Endpoint: $EP_ID"
echo ""
echo "4. Try manual connection with password from console if needed"
exit 6