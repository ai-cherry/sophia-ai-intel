#!/usr/bin/env python3
# Sophia AI - DNS Configuration Script for www.sophia-intel.ai
# Updates DNSimple records to point to Lambda Labs cluster

import os
import requests
import json
import sys

# Configuration
DNSIMPLE_TOKEN = os.environ.get('DNSIMPLE_API_KEY') or "dnsimple_u_XBHeyhH3O8uKJF6HnqU76h7ANWdNvUzN"
DOMAIN = 'sophia-intel.ai'
LAMBDA_IP = '192.222.51.223'

# First, let's get the account ID by making a test request
def get_account_id():
    """Get DNSimple account ID using the API token"""
    headers = {
        'Authorization': f'Bearer {DNSIMPLE_TOKEN}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get('https://api.dnsimple.com/v2/accounts', headers=headers)
        if response.status_code == 200:
            accounts = response.json()['data']
            if accounts:
                return accounts[0]['id']  # Return first account ID
        else:
            print(f"❌ Failed to get account ID: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting account ID: {e}")
        return None

def update_dns_records(account_id):
    """Update DNS records for Sophia AI production domain"""

    headers = {
        'Authorization': f'Bearer {DNSIMPLE_TOKEN}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    base_url = f'https://api.dnsimple.com/v2/{account_id}'

    # Records to create/update
    records = [
        {'name': '', 'type': 'A', 'content': LAMBDA_IP, 'ttl': 300},  # Root domain (@)
        {'name': 'www', 'type': 'A', 'content': LAMBDA_IP, 'ttl': 300},  # www subdomain
        {'name': 'api', 'type': 'A', 'content': LAMBDA_IP, 'ttl': 300},  # api subdomain
    ]

    print(f"🌐 Updating DNS records for {DOMAIN}...")
    print(f"📍 Pointing all records to: {LAMBDA_IP}")
    print("")

    # Get existing records
    try:
        response = requests.get(f'{base_url}/zones/{DOMAIN}/records', headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to get existing records: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        existing = {(r['name'], r['type']): r for r in response.json()['data']}
    except Exception as e:
        print(f"❌ Error getting existing records: {e}")
        return False

    success_count = 0

    for record in records:
        key = (record['name'], record['type'])
        record_name = record['name'] or '@'

        try:
            if key in existing:
                # Update existing record
                record_id = existing[key]['id']
                print(f"🔄 Updating {record_name} {record['type']} record...")

                update_response = requests.patch(
                    f'{base_url}/zones/{DOMAIN}/records/{record_id}',
                    headers=headers,
                    json=record
                )

                if update_response.status_code == 200:
                    print(f"✅ Successfully updated {record_name} {record['type']}")
                    success_count += 1
                else:
                    print(f"❌ Failed to update {record_name} {record['type']}: {update_response.status_code}")
                    print(f"Response: {update_response.text}")

            else:
                # Create new record
                print(f"➕ Creating {record_name} {record['type']} record...")

                create_response = requests.post(
                    f'{base_url}/zones/{DOMAIN}/records',
                    headers=headers,
                    json=record
                )

                if create_response.status_code == 201:
                    print(f"✅ Successfully created {record_name} {record['type']}")
                    success_count += 1
                else:
                    print(f"❌ Failed to create {record_name} {record['type']}: {create_response.status_code}")
                    print(f"Response: {create_response.text}")

        except Exception as e:
            print(f"❌ Error processing {record_name} {record['type']}: {e}")

    print("")
    print(f"📊 DNS Update Summary:")
    print(f"✅ Successful updates: {success_count}/{len(records)}")
    print(f"🌐 Domain: {DOMAIN}")
    print(f"📍 IP Address: {LAMBDA_IP}")
    print("")
    print("⏳ DNS propagation may take up to 24-48 hours")
    print("🔍 You can check propagation with:")
    print(f"   dig www.{DOMAIN}")
    print(f"   nslookup www.{DOMAIN}")

    return success_count == len(records)

def main():
    print("🚀 Sophia AI - DNS Configuration for Production")
    print("=" * 50)

    if not DNSIMPLE_TOKEN:
        print("❌ DNSIMPLE_API_KEY not found in environment variables")
        sys.exit(1)

    print(f"🔑 DNSimple Token: {DNSIMPLE_TOKEN[:10]}...")
    print(f"🌐 Domain: {DOMAIN}")
    print(f"📍 Target IP: {LAMBDA_IP}")
    print("")

    # Get account ID
    account_id = get_account_id()
    if not account_id:
        print("❌ Could not determine DNSimple account ID")
        sys.exit(1)

    print(f"🆔 Account ID: {account_id}")
    print("")

    # Update DNS records
    success = update_dns_records(account_id)

    if success:
        print("")
        print("🎉 DNS Configuration Complete!")
        print("")
        print("📋 Next Steps:")
        print("1. Wait for DNS propagation (5-30 minutes for initial, 24-48 hours for full)")
        print("2. Test domain resolution: curl -I http://www.sophia-intel.ai")
        print("3. Configure SSL certificates")
        print("4. Update ingress configuration")
        print("")
        print("🔗 Production URLs after DNS propagation:")
        print(f"   - http://www.{DOMAIN}")
        print(f"   - http://api.{DOMAIN}")
        print(f"   - http://{DOMAIN}")
    else:
        print("")
        print("❌ DNS Configuration Failed!")
        print("Please check the errors above and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()