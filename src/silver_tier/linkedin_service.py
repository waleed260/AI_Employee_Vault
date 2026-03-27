import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("LinkedInService")

LINKEDIN_API_BASE = "https://api.linkedin.com/v2"


class LinkedInService:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.linkedin_dir = self.vault_path / "LinkedIn"
        self.linkedin_dir.mkdir(exist_ok=True)

        self.config_file = self.linkedin_dir / "config.json"
        self.posts_file = self.linkedin_dir / "posts.json"
        self.scheduled_file = self.linkedin_dir / "scheduled.json"

        self.config = self._load_config()
        self.posts = self._load_posts()
        self.scheduled = self._load_scheduled()

        logger.info("LinkedInService initialized - Silver Tier")

    def _load_config(self) -> Dict:
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())
        return {
            "access_token": None,
            "company_id": None,
            "profile_id": None,
            "auto_post_enabled": False,
            "post_templates": [],
            "posting_schedule": {},
        }

    def _save_config(self):
        self.config_file.write_text(json.dumps(self.config, indent=2))

    def _load_posts(self) -> List:
        if self.posts_file.exists():
            return json.loads(self.posts_file.read_text())
        return []

    def _save_posts(self):
        self.posts_file.write_text(json.dumps(self.posts, indent=2))

    def _load_scheduled(self) -> List:
        if self.scheduled_file.exists():
            return json.loads(self.scheduled_file.read_text())
        return []

    def _save_scheduled(self):
        self.scheduled_file.write_text(json.dumps(self.scheduled, indent=2))

    def set_credentials(
        self, access_token: str, company_id: str = None, profile_id: str = None
    ) -> Dict:
        self.config["access_token"] = access_token
        self.config["company_id"] = company_id
        self.config["profile_id"] = profile_id
        self._save_config()

        logger.info("LinkedIn credentials updated")

        return {
            "status": "success",
            "message": "LinkedIn credentials saved",
        }

    def test_connection(self) -> Dict:
        if not self.config.get("access_token"):
            return {"status": "error", "message": "No access token configured"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                f"{LINKEDIN_API_BASE}/me", headers=headers, timeout=10
            )

            if response.status_code == 200:
                profile_data = response.json()
                return {
                    "status": "success",
                    "connected": True,
                    "profile": profile_data,
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

    def create_post(self, content: str, visibility: str = "PUBLIC") -> Dict:
        if not self.config.get("access_token"):
            return {"status": "error", "message": "LinkedIn not authenticated"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        owner = self.config.get("profile_id") or "urn:li:person:ME"

        post_data = {
            "author": owner,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }

        try:
            response = requests.post(
                f"{LINKEDIN_API_BASE}/ugcPosts",
                headers=headers,
                json=post_data,
                timeout=30,
            )

            if response.status_code == 201:
                post_id = response.json().get("id")

                post_entry = {
                    "post_id": post_id,
                    "content": content,
                    "visibility": visibility,
                    "created_at": datetime.now().isoformat(),
                    "status": "published",
                }
                self.posts.append(post_entry)
                self._save_posts()

                logger.info(f"Posted to LinkedIn: {post_id}")

                return {
                    "status": "success",
                    "post_id": post_id,
                    "post": post_entry,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to post: {response.text}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def create_post_with_image(
        self, content: str, image_url: str, title: str = None
    ) -> Dict:
        if not self.config.get("access_token"):
            return {"status": "error", "message": "LinkedIn not authenticated"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        owner = self.config.get("profile_id") or "urn:li:person:ME"

        post_data = {
            "author": owner,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "originalUrl": image_url,
                            "title": {"text": title or "Image"},
                        }
                    ],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        try:
            response = requests.post(
                f"{LINKEDIN_API_BASE}/ugcPosts",
                headers=headers,
                json=post_data,
                timeout=30,
            )

            if response.status_code == 201:
                post_id = response.json().get("id")

                post_entry = {
                    "post_id": post_id,
                    "content": content,
                    "image_url": image_url,
                    "created_at": datetime.now().isoformat(),
                    "status": "published",
                }
                self.posts.append(post_entry)
                self._save_posts()

                return {
                    "status": "success",
                    "post_id": post_id,
                    "post": post_entry,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to post: {response.text}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def schedule_post(
        self, content: str, scheduled_time: str, visibility: str = "PUBLIC"
    ) -> Dict:
        scheduled_entry = {
            "id": f"scheduled_{len(self.scheduled)}",
            "content": content,
            "scheduled_time": scheduled_time,
            "visibility": visibility,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
        }

        self.scheduled.append(scheduled_entry)
        self._save_scheduled()

        logger.info(f"Scheduled LinkedIn post for {scheduled_time}")

        return {
            "status": "success",
            "scheduled": scheduled_entry,
        }

    def get_scheduled_posts(self) -> List[Dict]:
        return self.scheduled

    def cancel_scheduled_post(self, scheduled_id: str) -> Dict:
        self.scheduled = [s for s in self.scheduled if s["id"] != scheduled_id]
        self._save_scheduled()

        return {
            "status": "success",
            "message": f"Cancelled scheduled post {scheduled_id}",
        }

    def get_posts(self, limit: int = 10) -> List[Dict]:
        return self.posts[-limit:]

    def delete_post(self, post_id: str) -> Dict:
        if not self.config.get("access_token"):
            return {"status": "error", "message": "LinkedIn not authenticated"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        try:
            response = requests.delete(
                f"{LINKEDIN_API_BASE}/ugcPosts/{post_id}", headers=headers, timeout=10
            )

            if response.status_code == 204:
                self.posts = [p for p in self.posts if p.get("post_id") != post_id]
                self._save_posts()

                return {
                    "status": "success",
                    "message": "Post deleted",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to delete: {response.status_code}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def get_post_analytics(self, post_id: str) -> Dict:
        if not self.config.get("access_token"):
            return {"status": "error", "message": "LinkedIn not authenticated"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                f"{LINKEDIN_API_BASE}/networkUpdates/{post_id}/networkStats",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                return {
                    "status": "success",
                    "post_id": post_id,
                    "analytics": response.json(),
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get analytics: {response.status_code}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def add_post_template(self, name: str, template: str) -> Dict:
        templates = self.config.get("post_templates", [])
        templates.append(
            {
                "name": name,
                "template": template,
                "created_at": datetime.now().isoformat(),
            }
        )
        self.config["post_templates"] = templates
        self._save_config()

        return {
            "status": "success",
            "template": {"name": name, "template": template},
        }

    def get_post_templates(self) -> List[Dict]:
        return self.config.get("post_templates", [])

    def auto_generate_post(self, template_name: str, context: Dict) -> str:
        templates = self.get_post_templates()

        template_obj = None
        for t in templates:
            if t["name"] == template_name:
                template_obj = t
                break

        if not template_obj:
            template_obj = {
                "template": "Exciting news from {company}! {news}. Learn more at {link}",
                "name": "default",
            }

        template = template_obj["template"]

        for key, value in context.items():
            template = template.replace(f"{{{key}}}", str(value))

        return template

    def enable_auto_post(self, enabled: bool) -> Dict:
        self.config["auto_post_enabled"] = enabled
        self._save_config()

        return {
            "status": "success",
            "auto_post_enabled": enabled,
        }

    def get_company_page_info(self) -> Dict:
        if not self.config.get("company_id") or not self.config.get("access_token"):
            return {"status": "error", "message": "Company ID or token not configured"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                f"{LINKEDIN_API_BASE}/companies/{self.config['company_id']}",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                return {
                    "status": "success",
                    "company": response.json(),
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get company info: {response.status_code}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def get_profile_info(self) -> Dict:
        if not self.config.get("access_token"):
            return {"status": "error", "message": "Not authenticated"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(
                f"{LINKEDIN_API_BASE}/me", headers=headers, timeout=10
            )

            if response.status_code == 200:
                return {
                    "status": "success",
                    "profile": response.json(),
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get profile: {response.status_code}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def process_business_update(self, update_data: Dict) -> Dict:
        update_type = update_data.get("type", "news")

        templates = {
            "product_launch": "🎉 Big news! We're thrilled to announce {product_name}! {description} #Innovation #TechNews",
            "milestone": "🎯 Milestone achieved! {milestone}. Thank you to our amazing team and customers! {celebration}",
            "testimonial": '💬 What our customers are saying: "{quote}" - {customer_name}. Thank you for your trust!',
            "tip": "💡 Quick tip: {tip}. Share this with anyone who could benefit! #Tips #Advice",
            "behind_scenes": "👀 Behind the scenes at {company}! {content} #Team #Culture",
            "news": "📢 Update from {company}: {news}. Stay tuned for more! {hashtags}",
            "promotion": "🔥 Don't miss out! {offer}. Limited time only! {cta_link}",
        }

        template = templates.get(update_type, templates["news"])

        for key, value in update_data.items():
            if key != "type":
                template = template.replace(f"{{{key}}}", str(value))

        if self.config.get("auto_post_enabled"):
            result = self.create_post(template)
            return result
        else:
            return {
                "status": "ready",
                "content": template,
                "message": "Post ready - enable auto_post to publish automatically",
            }

    def get_status(self) -> Dict:
        return {
            "authenticated": bool(self.config.get("access_token")),
            "company_id": bool(self.config.get("company_id")),
            "auto_post_enabled": self.config.get("auto_post_enabled", False),
            "total_posts": len(self.posts),
            "scheduled_posts": len(self.scheduled),
            "templates_count": len(self.config.get("post_templates", [])),
        }
