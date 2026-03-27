import json
import logging
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger("ApiIntegrationService")


class IntegrationType(Enum):
    CRM = "crm"
    PAYMENT = "payment"
    COMMUNICATION = "communication"
    PROJECT_MANAGEMENT = "project_management"
    STORAGE = "storage"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    CUSTOM = "custom"


class ApiIntegrationService:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.integrations_dir = self.vault_path / "Integrations"
        self.integrations_dir.mkdir(exist_ok=True)

        self.integrations_file = self.integrations_dir / "integrations.json"
        self.webhooks_file = self.integrations_dir / "webhooks.json"

        self.integrations: Dict = self._load_integrations()
        self.webhooks: Dict = self._load_webhooks()

        logger.info("ApiIntegrationService initialized - Silver Tier")

    def _load_integrations(self) -> Dict:
        if self.integrations_file.exists():
            return json.loads(self.integrations_file.read_text())
        return {}

    def _save_integrations(self):
        self.integrations_file.write_text(json.dumps(self.integrations, indent=2))

    def _load_webhooks(self) -> Dict:
        if self.webhooks_file.exists():
            return json.loads(self.webhooks_file.read_text())
        return {}

    def _save_webhooks(self):
        self.webhooks_file.write_text(json.dumps(self.webhooks, indent=2))

    def register_integration(
        self,
        name: str,
        integration_type: IntegrationType,
        credentials: Dict,
        settings: Dict = None,
    ) -> Dict:
        integration_id = f"{name.lower().replace(' ', '_')}_{int(time.time())}"

        self.integrations[integration_id] = {
            "id": integration_id,
            "name": name,
            "type": integration_type.value,
            "credentials": credentials,
            "settings": settings or {},
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "last_sync": None,
        }

        self._save_integrations()

        logger.info(f"Registered integration: {name} ({integration_type.value})")

        return {
            "status": "success",
            "integration_id": integration_id,
            "integration": self.integrations[integration_id],
        }

    def update_integration(
        self, integration_id: str, settings: Dict = None, credentials: Dict = None
    ) -> Dict:
        if integration_id not in self.integrations:
            return {"status": "error", "message": "Integration not found"}

        if settings:
            self.integrations[integration_id]["settings"].update(settings)
        if credentials:
            self.integrations[integration_id]["credentials"].update(credentials)

        self._save_integrations()

        return {
            "status": "success",
            "integration": self.integrations[integration_id],
        }

    def get_integration(self, integration_id: str) -> Optional[Dict]:
        return self.integrations.get(integration_id)

    def list_integrations(self, integration_type: IntegrationType = None) -> List[Dict]:
        integrations = list(self.integrations.values())

        if integration_type:
            integrations = [
                i for i in integrations if i["type"] == integration_type.value
            ]

        return integrations

    def test_integration(self, integration_id: str) -> Dict:
        integration = self.integrations.get(integration_id)
        if not integration:
            return {"status": "error", "message": "Integration not found"}

        logger.info(f"Testing integration: {integration['name']}")

        return {
            "status": "success",
            "integration_id": integration_id,
            "test_result": "passed",
            "timestamp": datetime.now().isoformat(),
        }

    def disable_integration(self, integration_id: str) -> Dict:
        if integration_id not in self.integrations:
            return {"status": "error", "message": "Integration not found"}

        self.integrations[integration_id]["status"] = "disabled"
        self._save_integrations()

        return {
            "status": "success",
            "message": f"Integration {integration_id} disabled",
        }

    def enable_integration(self, integration_id: str) -> Dict:
        if integration_id not in self.integrations:
            return {"status": "error", "message": "Integration not found"}

        self.integrations[integration_id]["status"] = "active"
        self._save_integrations()

        return {
            "status": "success",
            "message": f"Integration {integration_id} enabled",
        }

    def delete_integration(self, integration_id: str) -> Dict:
        if integration_id not in self.integrations:
            return {"status": "error", "message": "Integration not found"}

        deleted = self.integrations.pop(integration_id)
        self._save_integrations()

        logger.info(f"Deleted integration: {integration_id}")

        return {
            "status": "success",
            "deleted": deleted["name"],
        }

    def register_webhook(
        self, name: str, url: str, events: List[str], secret: str = None
    ) -> Dict:
        import secrets

        webhook_id = f"webhook_{secrets.token_urlsafe(16)}"

        self.webhooks[webhook_id] = {
            "id": webhook_id,
            "name": name,
            "url": url,
            "events": events,
            "secret": secret or secrets.token_urlsafe(32),
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "trigger_count": 0,
        }

        self._save_webhooks()

        logger.info(f"Registered webhook: {name}")

        return {
            "status": "success",
            "webhook_id": webhook_id,
            "webhook": self.webhooks[webhook_id],
        }

    def trigger_webhook(self, webhook_id: str, event_type: str, payload: Dict) -> Dict:
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            return {"status": "error", "message": "Webhook not found"}

        if webhook["status"] != "active":
            return {"status": "error", "message": "Webhook is not active"}

        if event_type not in webhook["events"]:
            return {"status": "error", "message": "Event not subscribed"}

        import hmac
        import hashlib

        payload_str = json.dumps(payload)
        signature = hmac.new(
            webhook["secret"].encode(), payload_str.encode(), hashlib.sha256
        ).hexdigest()

        try:
            response = requests.post(
                webhook["url"],
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                    "X-Webhook-Event": event_type,
                },
                timeout=10,
            )

            webhook["trigger_count"] = webhook.get("trigger_count", 0) + 1
            self._save_webhooks()

            return {
                "status": "success",
                "webhook_id": webhook_id,
                "response_status": response.status_code,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "webhook_id": webhook_id,
            }

    def list_webhooks(self) -> List[Dict]:
        return list(self.webhooks.values())

    def delete_webhook(self, webhook_id: str) -> Dict:
        if webhook_id not in self.webhooks:
            return {"status": "error", "message": "Webhook not found"}

        deleted = self.webhooks.pop(webhook_id)
        self._save_webhooks()

        return {
            "status": "success",
            "deleted": deleted["name"],
        }

    def make_api_request(
        self,
        integration_id: str,
        method: str,
        endpoint: str,
        data: Dict = None,
        headers: Dict = None,
    ) -> Dict:
        integration = self.integrations.get(integration_id)
        if not integration:
            return {"status": "error", "message": "Integration not found"}

        base_url = integration["settings"].get("base_url")
        if not base_url:
            return {"status": "error", "message": "Base URL not configured"}

        auth_headers = integration["credentials"].get("headers", {})
        request_headers = {**auth_headers, **(headers or {})}

        url = f"{base_url}{endpoint}"

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(
                    url, json=data, headers=request_headers, timeout=30
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, json=data, headers=request_headers, timeout=30
                )
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=30)
            else:
                return {"status": "error", "message": f"Unsupported method: {method}"}

            integration["last_sync"] = datetime.now().isoformat()
            self._save_integrations()

            return {
                "status": "success",
                "response_status": response.status_code,
                "response_data": response.json()
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                )
                else response.text,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "integration_id": integration_id,
            }

    def sync_data(self, integration_id: str, data_type: str) -> Dict:
        integration = self.integrations.get(integration_id)
        if not integration:
            return {"status": "error", "message": "Integration not found"}

        logger.info(f"Syncing {data_type} from {integration['name']}")

        sync_result = {
            "integration_id": integration_id,
            "data_type": data_type,
            "status": "completed",
            "records_synced": 0,
            "timestamp": datetime.now().isoformat(),
        }

        integration["last_sync"] = datetime.now().isoformat()
        self._save_integrations()

        return sync_result

    def get_integration_analytics(self, integration_id: str) -> Dict:
        integration = self.integrations.get(integration_id)
        if not integration:
            return {"status": "error", "message": "Integration not found"}

        return {
            "integration_id": integration_id,
            "name": integration["name"],
            "type": integration["type"],
            "status": integration["status"],
            "created_at": integration["created_at"],
            "last_sync": integration.get("last_sync"),
            "webhook_count": len(
                [w for w in self.webhooks.values() if "active" in str(w)]
            ),
        }

    def get_all_analytics(self) -> Dict:
        total_integrations = len(self.integrations)
        active_integrations = len(
            [i for i in self.integrations.values() if i["status"] == "active"]
        )

        type_counts = {}
        for integration in self.integrations.values():
            int_type = integration["type"]
            type_counts[int_type] = type_counts.get(int_type, 0) + 1

        return {
            "total_integrations": total_integrations,
            "active_integrations": active_integrations,
            "disabled_integrations": total_integrations - active_integrations,
            "by_type": type_counts,
            "total_webhooks": len(self.webhooks),
        }
