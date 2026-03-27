#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print(
        "Warning: Google API libraries not installed. Run: pip install google-api-python-client google-auth"
    )

sys.path.insert(0, str(Path(__file__).parent.parent))
from watchers.base_watcher import BaseWatcher


class GmailWatcher(BaseWatcher):
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    def __init__(
        self, vault_path: str, credentials_path: str, check_interval: int = 120
    ):
        super().__init__(vault_path, check_interval)
        self.credentials_path = Path(credentials_path)
        self.service = None
        self._init_gmail()

    def _init_gmail(self):
        if not GMAIL_AVAILABLE:
            raise RuntimeError("Gmail API libraries not installed")
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_path}"
            )
        creds = Credentials.from_authorized_user_file(
            str(self.credentials_path), self.SCOPES
        )
        self.service = build("gmail", "v1", credentials=creds)

    def check_for_updates(self) -> list:
        results = (
            self.service.users()
            .messages()
            .list(userId="me", q="is:unread is:important")
            .execute()
        )
        messages = results.get("messages", [])
        new_messages = [m for m in messages if not self._is_processed(m["id"])]
        if new_messages:
            self.trigger_claude(f"Found {len(new_messages)} new important emails")
        return new_messages

    def create_action_file(self, message) -> Path:
        msg = (
            self.service.users()
            .messages()
            .get(userId="me", id=message["id"], format="full")
            .execute()
        )

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

        body = self._extract_body(msg)
        priority = self._determine_priority(msg.get("snippet", ""))

        content = f"""---
type: email
source: gmail
id: {message["id"]}
from: {headers.get("From", "Unknown")}
to: {headers.get("To", "Unknown")}
subject: {headers.get("Subject", "No Subject")}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
---

## Email Content

{body}

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
- [ ] Mark as read

## Notes

_AI Employee will analyze this email and create a plan_
"""

        safe_subject = (
            headers.get("Subject", "No Subject")[:50]
            .replace("/", "-")
            .replace("\\", "-")
        )
        filepath = self.needs_action / f"EMAIL_{message['id']}_{safe_subject}.md"
        filepath.write_text(content)
        self._save_processed_id(message["id"])
        return filepath

    def _extract_body(self, msg) -> str:
        payload = msg.get("payload", {})
        parts = payload.get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    import base64

                    return base64.urlsafe_b64decode(data).decode(
                        "utf-8", errors="replace"
                    )
        return msg.get("snippet", "No preview available")

    def _determine_priority(self, text: str) -> str:
        urgent_keywords = ["urgent", "asap", "emergency", "immediately", "important"]
        text_lower = text.lower()
        if any(kw in text_lower for kw in urgent_keywords):
            return "high"
        return "medium"


def main():
    parser = argparse.ArgumentParser(description="Gmail Watcher for AI Employee")
    parser.add_argument("--vault", required=True, help="Path to Obsidian vault")
    parser.add_argument(
        "--credentials", required=True, help="Path to GCP credentials.json"
    )
    parser.add_argument(
        "--interval", type=int, default=120, help="Check interval in seconds"
    )
    args = parser.parse_args()

    watcher = GmailWatcher(args.vault, args.credentials, args.interval)
    watcher.run()


if __name__ == "__main__":
    main()
