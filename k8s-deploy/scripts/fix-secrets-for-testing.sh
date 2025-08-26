#!/bin/bash
# Script to replace placeholder values in secrets files with dummy base64-encoded values
# This allows deployment testing without real credentials

set -e

echo "🔧 Fixing secrets files for deployment testing..."

# Function to generate a dummy base64-encoded value
generate_dummy_base64() {
    echo -n "dummy_value_for_testing_$(date +%s)_$RANDOM" | base64
}

# List of secrets files to fix
SECRET_FILES=(
    "secrets/database-secrets.yaml"
    "secrets/llm-secrets.yaml"
    "secrets/infrastructure-secrets.yaml"
    "secrets/business-secrets.yaml"
)

for file in "${SECRET_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "📝 Processing $file..."

        # Create a backup
        cp "$file" "${file}.backup"

        # Replace all placeholder values with dummy base64 values
        sed -i 's/<BASE64_ENCODED_[^>]*>/'$(generate_dummy_base64)'/g' "$file"

        echo "✅ Fixed $file"
    else
        echo "⚠️  File $file not found, skipping..."
    fi
done

echo "🎉 All secrets files have been updated with dummy values for testing"
echo "📋 Note: These are dummy values for deployment testing only"
echo "🔒 In production, replace with real base64-encoded credentials"