#!/usr/bin/env python3
import os
import sys
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CLIENT_SECRETS = "client_secrets.json"
TOKEN_FILE = "gmail_token.json"

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False


def check_dependencies():
    if not GMAIL_AVAILABLE:
        print("Error: Required libraries not installed.")
        print(
            "Run: pip install --break-system-packages google-api-python-client google-auth google-auth-oauthlib"
        )
        sys.exit(1)


def check_client_secrets():
    secrets_path = Path(CLIENT_SECRETS)
    if not secrets_path.exists():
        print(f"Error: {CLIENT_SECRETS} not found.")
        print("\nTo get client_secrets.json:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a project or select existing one")
        print(
            "3. Enable Gmail API: APIS & Services > Library > Search 'Gmail API' > Enable"
        )
        print(
            "4. Create OAuth credentials: APIS & Services > Credentials > Create Credentials > OAuth Client ID"
        )
        print("5. Application type: Desktop app")
        print("6. Download the JSON and save as client_secrets.json in this directory")
        sys.exit(1)


def run_oauth_flow():
    print("\nStarting OAuth authentication flow...")
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
    creds = flow.run_local_server(port=8080, prompt="consent")

    with open(TOKEN_FILE, "w") as token:
        token.write(creds.to_json())

    print(f"\nSuccess! Credentials saved to {TOKEN_FILE}")
    return creds


def verify_connection(creds):
    print("\nVerifying Gmail connection...")
    try:
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        print(f"Connected as: {profile.get('emailAddress')}")
        print("Setup complete!")
    except Exception as e:
        print(f"Warning: Could not verify connection: {e}")
        print("You may need to delete the token and try again.")


def main():
    print("=" * 50)
    print("Gmail OAuth Setup for AI Employee Vault")
    print("=" * 50)

    check_dependencies()
    check_client_secrets()

    if Path(TOKEN_FILE).exists():
        response = input(f"\n{TOKEN_FILE} already exists. Regenerate? (y/n): ")
        if response.lower() != "y":
            print("Keeping existing token.")
            return

    creds = run_oauth_flow()
    verify_connection(creds)


if __name__ == "__main__":
    main()
