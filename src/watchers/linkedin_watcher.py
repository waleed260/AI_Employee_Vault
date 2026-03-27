import os
import json
import logging
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import threading

logger = logging.getLogger("LinkedInWatcher")


class LinkedInWatcher:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.linkedin_dir = self.vault_path / "LinkedIn"
        self.linkedin_dir.mkdir(exist_ok=True)

        self.config_file = self.linkedin_dir / "config.json"
        self.activity_file = self.linkedin_dir / "activity.json"

        self.config = self._load_config()
        self.activity = self._load_activity()

        self.running = False
        self.poll_interval = 300

        logger.info("LinkedInWatcher initialized - Silver Tier")

    def _load_config(self) -> Dict:
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())
        return {
            "access_token": None,
            "company_id": None,
            "profile_id": None,
            "enabled": False,
            "auto_like": False,
            "auto_comment": False,
            "notifications": {
                "new_comments": True,
                "new_connections": True,
                "post_engagement": True,
            },
        }

    def _save_config(self):
        self.config_file.write_text(json.dumps(self.config, indent=2))

    def _load_activity(self) -> List:
        if self.activity_file.exists():
            return json.loads(self.activity_file.read_text())
        return []

    def _save_activity(self):
        self.activity_file.write_text(json.dumps(self.activity, indent=2))

    def configure(
        self, access_token: str, company_id: str = None, profile_id: str = None
    ) -> Dict:
        self.config["access_token"] = access_token
        self.config["company_id"] = company_id
        self.config["profile_id"] = profile_id
        self.config["enabled"] = True
        self._save_config()

        logger.info("LinkedIn configured")

        return {
            "status": "success",
            "message": "LinkedIn API configured",
        }

    def test_connection(self) -> Dict:
        if not self.config.get("access_token"):
            return {"status": "error", "message": "LinkedIn not configured"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                "https://api.linkedin.com/v2/me", headers=headers, timeout=10
            )

            if response.status_code == 200:
                profile_data = response.json()
                return {
                    "status": "success",
                    "connected": True,
                    "profile": {
                        "id": profile_data.get("id"),
                        "firstName": profile_data.get("firstName"),
                        "lastName": profile_data.get("lastName"),
                    },
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

    def get_notifications(self) -> List[Dict]:
        if not self.config.get("access_token"):
            return []

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                "https://api.linkedin.com/v2/notifications", headers=headers, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("elements", [])
            else:
                return []
        except Exception as e:
            logger.warning(f"Failed to get notifications: {e}")
            return []

    def get_company_analytics(self) -> Dict:
        if not self.config.get("company_id") or not self.config.get("access_token"):
            return {"status": "error", "message": "Company ID or token not configured"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                f"https://api.linkedin.com/v2/organizationalEntityFollowerStatistics"
                f"?q=organizationalEntity&organizationalEntity=urn:li:organization:{self.config['company_id']}",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                return {
                    "status": "success",
                    "analytics": response.json(),
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

    def get_post_analytics(self, post_urn: str) -> Dict:
        if not self.config.get("access_token"):
            return {"status": "error", "message": "Not configured"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                f"https://api.linkedin.com/v2/socialActions/{post_urn}",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                return {
                    "status": "success",
                    "analytics": response.json(),
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

    def like_post(self, post_urn: str) -> Dict:
        if not self.config.get("access_token"):
            return {"status": "error", "message": "Not configured"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
        }

        payload = {
            "actor": f"urn:li:person:{self.config.get('profile_id', 'ME')}",
            "object": post_urn,
            "verb": "like",
        }

        try:
            response = requests.post(
                "https://api.linkedin.com/v2/socialActions",
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                self._log_activity("like", {"post": post_urn})
                return {"status": "success", "action": "liked"}
            else:
                return {"status": "error", "message": str(response.text)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def comment_on_post(self, post_urn: str, comment: str) -> Dict:
        if not self.config.get("access_token"):
            return {"status": "error", "message": "Not configured"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
        }

        payload = {
            "actor": f"urn:li:person:{self.config.get('profile_id', 'ME')}",
            "object": post_urn,
            "message": {"text": comment},
        }

        try:
            response = requests.post(
                "https://api.linkedin.com/v2/socialActions",
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code in [200, 201]:
                comment_urn = response.json().get("id")
                self._log_activity("comment", {"post": post_urn, "comment": comment})
                return {"status": "success", "comment_urn": comment_urn}
            else:
                return {"status": "error", "message": str(response.text)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_mentions(self) -> List[Dict]:
        if not self.config.get("access_token"):
            return []

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                "https://api.linkedin.com/v2/ugcPosts?q=mentions&type=MENTIONS",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("elements", [])
            else:
                return []
        except Exception as e:
            logger.warning(f"Failed to get mentions: {e}")
            return []

    def get_recent_posts(self, limit: int = 10) -> List[Dict]:
        if not self.config.get("access_token"):
            return []

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
        }

        profile_id = self.config.get("profile_id") or "me"

        try:
            response = requests.get(
                f"https://api.linkedin.com/v2/ugcPosts"
                f"?q=authors&authors=urn:li:person:{profile_id}"
                f"&count={limit}&sortBy=CREATED",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                posts = []

                for post in data.get("elements", []):
                    posts.append(
                        {
                            "id": post.get("id"),
                            "text": post.get("specificContent", {})
                            .get("com.linkedin.ugc.ShareContent", {})
                            .get("shareCommentary", {})
                            .get("text", ""),
                            "created": post.get("created", {}).get("time", 0),
                            "url": f"https://www.linkedin.com/feed/update/{post.get('id')}",
                        }
                    )

                return posts
            else:
                return []
        except Exception as e:
            logger.warning(f"Failed to get posts: {e}")
            return []

    def _log_activity(self, activity_type: str, details: Dict):
        entry = {
            "type": activity_type,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }

        self.activity.append(entry)
        self._save_activity()

    def get_activity_log(self, limit: int = 50) -> List[Dict]:
        return self.activity[-limit:]

    def process_notifications(self):
        notifications = self.get_notifications()
        processed_count = 0

        for notif in notifications:
            notif_type = notif.get("category")

            if notif_type == "COMMENT":
                self._handle_comment_notification(notif)
                processed_count += 1
            elif notif_type == "CONNECTION":
                self._handle_connection_notification(notif)
                processed_count += 1
            elif notif_type == "LIKE":
                self._handle_like_notification(notif)
                processed_count += 1

        logger.info(f"Processed {processed_count} LinkedIn notifications")

        return {
            "status": "success",
            "processed": processed_count,
        }

    def _handle_comment_notification(self, notif: Dict):
        actor = notif.get("actor", {})
        target = notif.get("target", {})

        self._save_to_vault(
            {
                "type": "comment",
                "from": actor.get("name", "Unknown"),
                "post": target.get("name", ""),
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _handle_connection_notification(self, notif: Dict):
        actor = notif.get("actor", {})

        self._save_to_vault(
            {
                "type": "connection",
                "from": actor.get("name", "Unknown"),
                "profile_url": actor.get("subDescription", ""),
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _handle_like_notification(self, notif: Dict):
        actor = notif.get("actor", {})

        self._save_to_vault(
            {
                "type": "like",
                "from": actor.get("name", "Unknown"),
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _save_to_vault(self, data: Dict):
        inbox_dir = self.vault_path / "Inbox"
        inbox_dir.mkdir(exist_ok=True)

        safe_type = data.get("type", "notification")
        filename = f"LINKEDIN_{safe_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"

        content = f"""---
type: linkedin
source: linkedin
id: {data.get("timestamp", "")}
status: pending
---

## LinkedIn Notification

**Type:** {data.get("type", "notification").title()}

{data.get("from", "Unknown")} - {datetime.now().strftime("%Y-%m-%d %H:%M")}

"""

        if data.get("post"):
            content += f"**Post:** {data.get('post')}\n\n"
        if data.get("profile_url"):
            content += f"**Profile:** {data.get('profile_url')}\n\n"

        content += """---

## Actions

- [ ] Review
- [ ] Respond
- [ ] Move to Done

"""

        (inbox_dir / filename).write_text(content)

    def enable_auto_engagement(self, like: bool = True, comment: bool = False) -> Dict:
        self.config["auto_like"] = like
        self.config["auto_comment"] = comment
        self._save_config()

        return {
            "status": "success",
            "auto_like": like,
            "auto_comment": comment,
        }

    def start_polling(self):
        self.running = True

        def poll():
            while self.running:
                try:
                    self.process_notifications()
                except Exception as e:
                    logger.warning(f"Poll error: {e}")
                time.sleep(self.poll_interval)

        thread = threading.Thread(target=poll, daemon=True)
        thread.start()

        logger.info("LinkedIn polling started")

        return {"status": "success", "polling": True}

    def stop_polling(self):
        self.running = False
        logger.info("LinkedIn polling stopped")

        return {"status": "success", "polling": False}

    def get_status(self) -> Dict:
        return {
            "configured": bool(self.config.get("access_token")),
            "enabled": self.config.get("enabled", False),
            "company_id": bool(self.config.get("company_id")),
            "auto_like": self.config.get("auto_like", False),
            "auto_comment": self.config.get("auto_comment", False),
            "activity_count": len(self.activity),
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn Watcher for AI Employee")
    parser.add_argument("--vault", required=True, help="Path to vault")
    parser.add_argument("--token", help="LinkedIn access token")
    parser.add_argument("--company-id", help="Company ID")
    args = parser.parse_args()

    watcher = LinkedInWatcher(args.vault)

    if args.token:
        watcher.configure(args.token, args.company_id)

    print(f"LinkedIn Watcher ready")
    print(f"Status: {watcher.get_status()}")

    watcher.start_polling()


if __name__ == "__main__":
    main()
