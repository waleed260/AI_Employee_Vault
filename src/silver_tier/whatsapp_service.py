import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("WhatsAppService")


class WhatsAppService:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.whatsapp_dir = self.vault_path / "WhatsApp"
        self.whatsapp_dir.mkdir(exist_ok=True)

        self.config_file = self.whatsapp_dir / "config.json"
        self.messages_file = self.whatsapp_dir / "messages.json"

        self.config = self._load_config()
        self.messages = self._load_messages()

        logger.info("WhatsAppService initialized")

    def _load_config(self) -> Dict:
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())
        return {}

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
                return {"status": "success", "connected": True}
            else:
                return {
                    "status": "error",
                    "message": f"API error: {response.status_code}",
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}

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
                        "message": message,
                        "direction": "outbound",
                        "timestamp": datetime.now().isoformat(),
                        "status": "sent",
                    }
                )
                self._save_messages()

                logger.info(f"Sent WhatsApp message to {to}")

                return {"status": "success", "message_id": message_id}
            else:
                return {"status": "error", "message": f"Failed: {response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

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
                return {"status": "success", "template": template_name}
            else:
                return {"status": "error", "message": f"Failed: {response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_quick_reply(self, template_key: str) -> str:
        templates = self.config.get("reply_templates", {})
        return templates.get(template_key, "")

    def set_auto_reply(self, enabled: bool, templates: Dict = None) -> Dict:
        self.config["auto_reply"] = enabled
        if templates:
            self.config["reply_templates"] = templates
        self._save_config()

        return {"status": "success", "auto_reply_enabled": enabled}

    def get_conversations(self) -> List[Dict]:
        conversations = {}
        for msg in self.messages:
            contact = msg.get("from") or msg.get("to")
            if contact not in conversations:
                conversations[contact] = {
                    "phone": contact,
                    "last_message": msg.get("message", ""),
                    "last_timestamp": msg.get("timestamp"),
                    "message_count": 0,
                }
            conversations[contact]["message_count"] += 1
        return list(conversations.values())

    def get_messages(self, contact: str = None, limit: int = 50) -> List[Dict]:
        messages = self.messages
        if contact:
            messages = [
                m
                for m in messages
                if m.get("from") == contact or m.get("to") == contact
            ]
        return messages[-limit:]

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

    parser = argparse.ArgumentParser(description="WhatsApp Service")
    parser.add_argument("--vault", required=True, help="Path to vault")
    parser.add_argument("--send", help="Send message")
    parser.add_argument("--to", help="Recipient phone")
    args = parser.parse_args()

    service = WhatsAppService(args.vault)

    if args.send and args.to:
        result = service.send_message(args.to, args.send)
        print(result)
    else:
        print(service.get_status())


if __name__ == "__main__":
    main()
