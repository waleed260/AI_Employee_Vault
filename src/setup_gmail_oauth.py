#!/usr/bin/env python3
import os
import sys
import threading
import time
import webbrowser
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
        print("Run: pip install --break-system-packages google-api-python-client google-auth google-auth-oauthlib")
        sys.exit(1)


def check_client_secrets():
    for path in [CLIENT_SECRETS, "../" + CLIENT_SECRETS]:
        if Path(path).exists():
            return str(Path(path).resolve())
    print(f"Error: {CLIENT_SECRETS} not found.")
    print("Looking in:", Path.cwd())
    sys.exit(1)


def verify_connection(creds):
    print("\nVerifying Gmail connection...")
    try:
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        print(f"✅ Connected as: {profile.get('emailAddress')}")
        print("Setup complete!")
        return True
    except Exception as e:
        print(f"⚠️ Warning: Could not verify connection: {e}")
        return False


def run_oauth_flow():
    secrets_path = check_client_secrets()
    print(f"\nStarting Gmail OAuth...")

    flow = InstalledAppFlow.from_client_secrets_file(
        secrets_path, SCOPES, redirect_uri="http://localhost:0"
    )

    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    print(f"\n🌐 Open this link in your browser to authorize:\n")
    print(f"  {auth_url}")
    print()

    try:
        webbrowser.open(auth_url)
        print("(Browser opened)")
    except Exception:
        pass

    code = input("📋 Paste the authorization code from Google here: ").strip()
    flow.fetch_token(code=code)
    creds = flow.credentials

    token_path = Path(TOKEN_FILE)
    with open(token_path, "w") as f:
        f.write(creds.to_json())
    print(f"\n✅ Token saved to {token_path.resolve()}")

    return creds


def main():
    print("=" * 50)
    print("Gmail OAuth Setup for AI Employee Vault")
    print("=" * 50)

    check_dependencies()

    if Path(TOKEN_FILE).exists():
        print(f"\nExisting token found. Testing it first...")
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            if creds.valid:
                print("Token is still valid!")
                verify_connection(creds)
                return
            elif creds.expired and creds.refresh_token:
                print("Token expired. Attempting refresh...")
                from google.auth.transport.requests import Request
                creds.refresh(Request())
                with open(TOKEN_FILE, "w") as f:
                    f.write(creds.to_json())
                print("Token refreshed!")
                verify_connection(creds)
                return
            else:
                print("Token invalid. Need to re-authenticate.")
        except Exception as e:
            print(f"Token error: {e}. Need to re-authenticate.")

    creds = run_oauth_flow()
    verify_connection(creds)


if __name__ == "__main__":
    main()
