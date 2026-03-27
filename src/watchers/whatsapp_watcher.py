import os
import json
import logging
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import threading

logger = logging.getLogger("WhatsAppWatcher")


class WhatsAppWatcher:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.whatsapp_dir = self.vault_path / "WhatsApp"
        self.whatsapp_dir.mkdir(exist_ok=True)

        self.config_file = self.whatsapp_dir / "config.json"
        self.messages_file = self.whatsapp_dir / "messages.json"

        self.config = self._load_config()
        self.messages = self._load_messages()

        self.running = False
        self.poll_interval = 30

        logger.info("WhatsAppWatcher initialized - Silver Tier")

    def _load_config(self) -> Dict:
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())
        return {
            "api_url": None,
            "api_token": None,
            "phone_number_id": None,
            "webhook_verify_token": "whatsapp_webhook_verify",
            "enabled": False,
            "auto_reply": False,
        }

    def _save_config(self):
        self.config_file.write_text(json.dumps(self.config, indent=2))

    def _load_messages(self) -> List:
        if self.messages_file.exists():
            return json.loads(self.messages_file.read_text())
        return []

    def _save_messages(self):
        self.messages_file.write_text(json.dumps(self.messages, indent=2))

    def configure(
        self, api_url: str, api_token: str, phone_number_id: str = None
    ) -> Dict:
        self.config["api_url"] = api_url
        self.config["api_token"] = api_token
        self.config["phone_number_id"] = phone_number_id
        self.config["enabled"] = True
        self._save_config()

        logger.info("WhatsApp API configured")

        return {
            "status": "success",
            "message": "WhatsApp API configured",
        }

    def test_connection(self) -> Dict:
        if not self.config.get("api_url") or not self.config.get("api_token"):
            return {"status": "error", "message": "WhatsApp API not configured"}

        headers = {
            "Authorization": f"Bearer {self.config['api_token']}",
        }

        try:
            response = requests.get(
                f"{self.config['api_url']}/api/health", headers=headers, timeout=10
            )

            if response.status_code == 200:
                return {
                    "status": "success",
                    "connected": True,
                }
            else:
                return {
                    "status": "error",
                    "message": f"API error: {response.status_code}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def send_message(self, to: str, message: str) -> Dict:
        if not self.config.get("api_url") or not self.config.get("api_token"):
            return {"status": "error", "message": "WhatsApp API not configured"}

        headers = {
            "Authorization": f"Bearer {self.config['api_token']}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message},
        }

        try:
            response = requests.post(
                f"{self.config['api_url']}/api/messages",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code in [200, 201]:
                message_id = response.json().get("messages", [{}])[0].get("id")

                self.messages.append(
                    {
                        "id": message_id,
                        "to": to,
                        "from": self.config.get("phone_number_id"),
                        "message": message,
                        "direction": "outbound",
                        "timestamp": datetime.now().isoformat(),
                        "status": "sent",
                    }
                )
                self._save_messages()

                logger.info(f"Sent WhatsApp message to {to}")

                return {
                    "status": "success",
                    "message_id": message_id,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to send: {response.text}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def send_template(
        self, to: str, template_name: str, components: Dict = None
    ) -> Dict:
        if not self.config.get("api_url") or not self.config.get("api_token"):
            return {"status": "error", "message": "WhatsApp API not configured"}

        headers = {
            "Authorization": f"Bearer {self.config['api_token']}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en_US"},
            },
        }

        if components:
            payload["template"]["components"] = components

        try:
            response = requests.post(
                f"{self.config['api_url']}/api/messages",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code in [200, 201]:
                return {
                    "status": "success",
                    "message": f"Template {template_name} sent",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to send template: {response.text}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def handle_webhook(self, payload: Dict) -> Dict:
        entries = payload.get("entry", [])

        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                messages = change.get("value", {}).get("messages", [])

                for msg in messages:
                    self._process_incoming_message(msg)

        return {"status": "success", "processed": len(entries)}

    def _process_incoming_message(self, msg: Dict):
        msg_id = msg.get("id")
        from_number = msg.get("from")
        timestamp = msg.get("timestamp")

        msg_type = msg.get("type")
        text = None

        if msg_type == "text":
            text = msg.get("text", {}).get("body")
        elif msg_type == "image":
            text = "[Image]"
        elif msg_type == "audio":
            text = "[Audio]"
        elif msg_type == "video":
            text = "[Video]"
        elif msg_type == "document":
            text = "[Document]"

        message_entry = {
            "id": msg_id,
            "from": from_number,
            "type": msg_type,
            "text": text,
            "timestamp": timestamp,
            "direction": "inbound",
            "status": "received",
        }

        self.messages.append(message_entry)
        self._save_messages()

        self._save_to_vault(message_entry)

        logger.info(f"Processed WhatsApp message from {from_number}")

    def _save_to_vault(self, message: Dict):
        inbox_dir = self.vault_path / "Inbox"
        inbox_dir.mkdir(exist_ok=True)

        safe_name = message["from"][-20:].replace("+", "").replace("-", "")
        filename = f"WHATSAPP_{safe_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"

        content = f"""---
type: whatsapp
source: whatsapp
id: {message["id"]}
from: {message["from"]}
timestamp: {message["timestamp"]}
status: pending
---

## WhatsApp Message

**From:** {message["from"]}
**Type:** {message["type"]}
**Time:** {message["timestamp"]}

---

{message["text"]}

---

## Actions

### Quick Actions
- [ ] Mark as read
- [ ] Archive

### Workflow Actions
- [ ] Move to Needs_Action
- [ ] Move to Pending_Approval
- [ ] Move to Done
- [ ] Move to Rejected

### Reply Actions
- [ ] Send quick reply
- [ ] Send template message

"""

        (inbox_dir / filename).write_text(content)
        logger.info(f"Saved WhatsApp message to vault: {filename}")

    def get_conversations(self) -> List[Dict]:
        conversations = {}

        for msg in self.messages:
            contact = msg.get("from")
            if contact not in conversations:
                conversations[contact] = {
                    "phone": contact,
                    "last_message": msg.get("text", ""),
                    "last_timestamp": msg.get("timestamp"),
                    "message_count": 0,
                    "direction": msg.get("direction"),
                }
            conversations[contact]["message_count"] += 1

        return list(conversations.values())

    def get_messages(self, contact: str = None, limit: int = 50) -> List[Dict]:
        messages = self.messages

        if contact:
            messages = [m for m in messages if m.get("from") == contact]

        return messages[-limit:]

    def set_auto_reply(self, enabled: bool, templates: Dict = None) -> Dict:
        self.config["auto_reply"] = enabled
        if templates:
            self.config["reply_templates"] = templates
        self._save_config()

        return {
            "status": "success",
            "auto_reply_enabled": enabled,
        }

    def start_polling(self):
        self.running = True

        def poll():
            while self.running:
                self._poll_messages()
                time.sleep(self.poll_interval)

        thread = threading.Thread(target=poll, daemon=True)
        thread.start()

        logger.info("WhatsApp polling started")

        return {"status": "success", "polling": True}

    def stop_polling(self):
        self.running = False
        logger.info("WhatsApp polling stopped")

        return {"status": "success", "polling": False}

    def _poll_messages(self):
        if not self.config.get("api_url") or not self.config.get("api_token"):
            return

        headers = {
            "Authorization": f"Bearer {self.config['api_token']}",
        }

        try:
            response = requests.get(
                f"{self.config['api_url']}/api/messages", headers=headers, timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])

                for msg in messages:
                    if msg.get("direction") == "inbound":
                        self._process_incoming_message(msg)
        except Exception as e:
            logger.warning(f"Poll error: {e}")

    def get_status(self) -> Dict:
        return {
            "configured": bool(self.config.get("api_url")),
            "enabled": self.config.get("enabled", False),
            "auto_reply": self.config.get("auto_reply", False),
            "total_messages": len(self.messages),
            "conversations": len(self.get_conversations()),
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="WhatsApp Watcher for AI Employee")
    parser.add_argument("--vault", required=True, help="Path to vault")
    parser.add_argument("--api-url", help="WhatsApp API URL")
    parser.add_argument("--token", help="WhatsApp API token")
    parser.add_argument("--phone-id", help="Phone number ID")
    args = parser.parse_args()

    watcher = WhatsAppWatcher(args.vault)

    if args.api_url and args.token:
        watcher.configure(args.api_url, args.token, args.phone_id)

    print(f"WhatsApp Watcher ready")
    print(f"Status: {watcher.get_status()}")

    watcher.start_polling()


if __name__ == "__main__":
    main()
