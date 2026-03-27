#!/usr/bin/env python3
"""
Integration Setup Helper
Run this to configure LinkedIn and WhatsApp integrations
"""

import json
import sys
from pathlib import Path

VAULT_PATH = Path(__file__).parent / "vault_data"


def setup_linkedin():
    print("\n" + "=" * 50)
    print("LINKEDIN SETUP")
    print("=" * 50)
    print("""
To get LinkedIn API access:
1. Go to https://www.linkedin.com/developers/apps
2. Create a new app
3. Get your Access Token
4. Copy it below
""")

    access_token = input("Enter LinkedIn Access Token: ").strip()
    company_id = input("Enter Company ID (optional, press Enter to skip): ").strip()
    profile_id = input("Enter Profile ID (optional, press Enter to skip): ").strip()

    config_file = VAULT_PATH / "LinkedIn" / "config.json"

    if config_file.exists():
        config = json.loads(config_file.read_text())
    else:
        config = {}

    config["access_token"] = access_token if access_token else None
    config["company_id"] = company_id if company_id else None
    config["profile_id"] = profile_id if profile_id else None
    config["status"] = "configured" if access_token else "needs_setup"

    config_file.write_text(json.dumps(config, indent=2))

    if access_token:
        print("\n✓ LinkedIn configured!")
        print(f"  Company ID: {company_id or 'Not set'}")
        print(f"  Profile ID: {profile_id or 'Not set'}")
    else:
        print("\n✗ No token provided")


def setup_whatsapp():
    print("\n" + "=" * 50)
    print("WHATSAPP SETUP")
    print("=" * 50)
    print("""
To get WhatsApp Business API:
1. Go to https://developers.facebook.com/
2. Create a WhatsApp Business app
3. Get your API URL and Token
4. Copy them below
""")

    api_url = input("Enter WhatsApp API URL: ").strip()
    api_token = input("Enter WhatsApp API Token: ").strip()
    phone_id = input("Enter Phone Number ID (optional): ").strip()

    config_file = VAULT_PATH / "WhatsApp" / "config.json"

    if config_file.exists():
        config = json.loads(config_file.read_text())
    else:
        config = {}

    config["api_url"] = api_url if api_url else None
    config["api_token"] = api_token if api_token else None
    config["phone_number_id"] = phone_id if phone_id else None
    config["status"] = "configured" if api_url and api_token else "needs_setup"

    config_file.write_text(json.dumps(config, indent=2))

    if api_url and api_token:
        print("\n✓ WhatsApp configured!")
    else:
        print("\n✗ API URL and Token required")


def setup_gmail():
    print("\n" + "=" * 50)
    print("GMAIL SETUP")
    print("=" * 50)
    print("""
To get Gmail API access:
1. Go to https://console.cloud.google.com/
2. Create a project
3. Enable Gmail API
4. Create OAuth credentials (Desktop app)
5. Download as 'credentials.json' to project root
""")

    creds_path = Path(__file__).parent / "credentials.json"

    if creds_path.exists():
        print("\n✓ credentials.json found!")
        print("  Gmail is ready to use.")
    else:
        print("\n✗ credentials.json not found")
        print("  Please download from Google Cloud Console")


def show_status():
    print("\n" + "=" * 50)
    print("INTEGRATION STATUS")
    print("=" * 50)

    # Gmail
    creds_path = Path(__file__).parent / "credentials.json"
    gmail_status = "✓ Configured" if creds_path.exists() else "✗ Not found"
    print(f"\nGmail: {gmail_status}")

    # LinkedIn
    li_config = VAULT_PATH / "LinkedIn" / "config.json"
    if li_config.exists():
        li = json.loads(li_config.read_text())
        li_status = "✓ Configured" if li.get("access_token") else "✗ Not configured"
    else:
        li_status = "✗ Not setup"
    print(f"LinkedIn: {li_status}")

    # WhatsApp
    wa_config = VAULT_PATH / "WhatsApp" / "config.json"
    if wa_config.exists():
        wa = json.loads(wa_config.read_text())
        wa_status = "✓ Configured" if wa.get("api_url") else "✗ Not configured"
    else:
        wa_status = "✗ Not setup"
    print(f"WhatsApp: {wa_status}")


def main():
    print("\nAI Employee Vault - Integration Setup")
    print("=" * 50)
    print("1. Setup LinkedIn")
    print("2. Setup WhatsApp")
    print("3. Setup Gmail")
    print("4. Show Status")
    print("5. Exit")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == "1":
        setup_linkedin()
    elif choice == "2":
        setup_whatsapp()
    elif choice == "3":
        setup_gmail()
    elif choice == "4":
        show_status()
    elif choice == "5":
        print("\nExiting...")
    else:
        print("\nInvalid choice")


if __name__ == "__main__":
    main()
