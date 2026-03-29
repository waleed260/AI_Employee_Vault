import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


class GmailService:
    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.service = None

    def authenticate(self):
        creds = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(self.token_path), ["https://www.googleapis.com/auth/gmail.readonly"]
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    ["https://www.googleapis.com/auth/gmail.readonly"],
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)

    def get_unread_count(self) -> int:
        if not self.service:
            self.authenticate()

        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q="is:unread", maxResults=1)
                .execute()
            )
            return int(results.get("resultSizeEstimate", 0))
        except Exception:
            return 0

    def get_recent_unread(self, limit: int = 5) -> list:
        if not self.service:
            self.authenticate()

        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q="is:unread", maxResults=limit)
                .execute()
            )
            messages = results.get("messages", [])
            unread = []
            for msg in messages:
                msg_data = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )
                headers = msg_data.get("payload", {}).get("headers", [])
                subject = next(
                    (h["value"] for h in headers if h["name"] == "Subject"),
                    "No Subject",
                )
                sender = next(
                    (h["value"] for h in headers if h["name"] == "From"), "Unknown"
                )
                body = self._extract_body(msg_data)
                unread.append(
                    {"id": msg["id"], "subject": subject, "from": sender, "body": body}
                )
            return unread
        except Exception:
            return []

    def _extract_body(self, msg) -> str:
        import base64

        payload = msg.get("payload", {})
        parts = payload.get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode(
                        "utf-8", errors="replace"
                    )
        return msg.get("snippet", "No preview available")

    def get_inbox_emails(self, limit: int = 10) -> list:
        if not self.service:
            self.authenticate()

        try:
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q="in:inbox", maxResults=limit)
                .execute()
            )
            messages = results.get("messages", [])
            emails = []
            for msg in messages:
                msg_data = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="full")
                    .execute()
                )
                headers = msg_data.get("payload", {}).get("headers", [])
                subject = next(
                    (h["value"] for h in headers if h["name"] == "Subject"),
                    "No Subject",
                )
                sender = next(
                    (h["value"] for h in headers if h["name"] == "From"), "Unknown"
                )
                date = next(
                    (h["value"] for h in headers if h["name"] == "Date"), "Unknown"
                )
                body = self._extract_body(msg_data)
                is_unread = "UNREAD" in msg_data.get("labelIds", [])
                emails.append(
                    {
                        "id": msg["id"],
                        "subject": subject,
                        "from": sender,
                        "date": date,
                        "body": body,
                        "unread": is_unread,
                    }
                )
            return emails
        except Exception as e:
            print(f"Error fetching inbox: {e}")
            return []
