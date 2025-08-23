#!/usr/bin/env bash
set -euo pipefail

APP=$(awk -F'"' '/^app =/ {print $2}' fly.toml)
: "${FLY_ORG:?FLY_ORG must be set}"

echo "Ensuring Fly app exists: $APP (org=$FLY_ORG)"

if ! flyctl apps show "$APP" >/dev/null 2>&1; then
  echo "Creating Fly app: $APP"
  flyctl apps create "$APP" --org "$FLY_ORG"
  echo "Successfully created app: $APP"
else
  echo "App already exists: $APP"
fi