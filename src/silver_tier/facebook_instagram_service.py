#!/usr/bin/env python3
"""
Facebook & Instagram Service for AI Employee Vault
Handles posting to Facebook Pages and Instagram Business Accounts
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("FacebookInstagramService")

# Facebook Graph API base URL
FACEBOOK_GRAPH_API = "https://graph.facebook.com/v18.0"


class FacebookInstagramService:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.fb_ig_dir = self.vault_path / "Facebook_Instagram"
        self.fb_ig_dir.mkdir(exist_ok=True)

        self.config_file = self.fb_ig_dir / "config.json"
        self.posts_file = self.fb_ig_dir / "posts.json"
        self.scheduled_file = self.fb_ig_dir / "scheduled.json"

        self.config = self._load_config()
        self.posts = self._load_posts()
        self.scheduled = self._load_scheduled()

        logger.info("FacebookInstagramService initialized - Gold Tier")

    def _load_config(self) -> Dict:
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())
        return {
            "access_token": None,
            "page_id": None,
            "instagram_account_id": None,
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
        self, access_token: str, page_id: str = None, instagram_account_id: str = None
    ) -> Dict:
        """Set Facebook/Instagram API credentials"""
        self.config["access_token"] = access_token
        self.config["page_id"] = page_id
        self.config["instagram_account_id"] = instagram_account_id
        self._save_config()

        logger.info("Facebook/Instagram credentials updated")

        return {
            "status": "success",
            "message": "Facebook/Instagram credentials saved",
        }

    def test_connection(self) -> Dict:
        """Test connection to Facebook Graph API"""
        if not self.config.get("access_token"):
            return {"status": "error", "message": "No access token configured"}

        if not self.config.get("page_id"):
            return {"status": "error", "message": "No Page ID configured"}

        headers = {
            "Authorization": f"Bearer {self.config['access_token']}",
        }

        try:
            # Test Facebook Page access
            fb_response = requests.get(
                f"{FACEBOOK_GRAPH_API}/{self.config['page_id']}",
                params={"fields": "id,name,fan_count"},
                headers=headers,
                timeout=10,
            )

            # Test Instagram access if configured
            ig_data = None
            if self.config.get("instagram_account_id"):
                ig_response = requests.get(
                    f"{FACEBOOK_GRAPH_API}/{self.config['instagram_account_id']}",
                    params={"fields": "id,username,followers_count"},
                    headers=headers,
                    timeout=10,
                )
                if ig_response.status_code == 200:
                    ig_data = ig_response.json()

            if fb_response.status_code == 200:
                fb_data = fb_response.json()
                return {
                    "status": "success",
                    "connected": True,
                    "facebook_page": fb_data,
                    "instagram_account": ig_data,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Facebook API error: {fb_response.status_code} - {fb_response.text}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def create_facebook_post(
        self,
        content: str,
        link: str = None,
        image_url: str = None,
        video_url: str = None,
        published: bool = True,
    ) -> Dict:
        """Create a Facebook Page post"""
        if not self.config.get("access_token"):
            return {"status": "error", "message": "Facebook not authenticated"}

        if not self.config.get("page_id"):
            return {"status": "error", "message": "Facebook Page ID not configured"}

        # Prepare post data
        post_data = {
            "message": content,
            "published": str(published).lower(),
            "access_token": self.config["access_token"],
        }

        # Add link if provided
        if link:
            post_data["link"] = link

        # Determine endpoint based on media type
        if video_url:
            endpoint = f"{FACEBOOK_GRAPH_API}/{self.config['page_id']}/videos"
            post_data["file_url"] = video_url
            post_data["description"] = content
        elif image_url:
            endpoint = f"{FACEBOOK_GRAPH_API}/{self.config['page_id']}/photos"
            post_data["url"] = image_url
            post_data["caption"] = content
        else:
            endpoint = f"{FACEBOOK_GRAPH_API}/{self.config['page_id']}/feed"

        try:
            response = requests.post(endpoint, data=post_data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                post_id = result.get("id")

                post_entry = {
                    "post_id": post_id,
                    "content": content,
                    "link": link,
                    "image_url": image_url,
                    "video_url": video_url,
                    "platform": "facebook",
                    "published": published,
                    "created_at": datetime.now().isoformat(),
                    "status": "published" if published else "scheduled",
                }
                self.posts.append(post_entry)
                self._save_posts()

                logger.info(f"Posted to Facebook: {post_id}")

                return {
                    "status": "success",
                    "post_id": post_id,
                    "post": post_entry,
                    "platform": "facebook",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to post to Facebook: {response.text}",
                    "platform": "facebook",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "platform": "facebook",
            }

    def create_instagram_post(
        self, content: str, image_url: str, published: bool = True
    ) -> Dict:
        """Create an Instagram post (requires Facebook Page connection)"""
        if not self.config.get("access_token"):
            return {"status": "error", "message": "Instagram not authenticated"}

        if not self.config.get("instagram_account_id"):
            return {"status": "error", "message": "Instagram Account ID not configured"}

        # First, create a media container
        container_data = {
            "image_url": image_url,
            "caption": content,
            "access_token": self.config["access_token"],
        }

        try:
            # Step 1: Create media container
            container_response = requests.post(
                f"{FACEBOOK_GRAPH_API}/{self.config['instagram_account_id']}/media",
                data=container_data,
                timeout=30,
            )

            if container_response.status_code != 200:
                return {
                    "status": "error",
                    "message": f"Failed to create Instagram media container: {container_response.text}",
                    "platform": "instagram",
                }

            container_id = container_response.json().get("id")

            # Step 2: Publish the media container
            publish_data = {
                "creation_id": container_id,
                "access_token": self.config["access_token"],
            }

            publish_response = requests.post(
                f"{FACEBOOK_GRAPH_API}/{self.config['instagram_account_id']}/media_publish",
                data=publish_data,
                timeout=30,
            )

            if publish_response.status_code == 200:
                result = publish_response.json()
                post_id = result.get("id")

                post_entry = {
                    "post_id": post_id,
                    "content": content,
                    "image_url": image_url,
                    "platform": "instagram",
                    "published": published,
                    "created_at": datetime.now().isoformat(),
                    "status": "published" if published else "scheduled",
                }
                self.posts.append(post_entry)
                self._save_posts()

                logger.info(f"Posted to Instagram: {post_id}")

                return {
                    "status": "success",
                    "post_id": post_id,
                    "post": post_entry,
                    "platform": "instagram",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to publish Instagram post: {publish_response.text}",
                    "platform": "instagram",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "platform": "instagram",
            }

    def schedule_post(
        self,
        content: str,
        scheduled_time: str,
        platform: str = "facebook",
        image_url: str = None,
        video_url: str = None,
        link: str = None,
    ) -> Dict:
        """Schedule a post for Facebook or Instagram"""
        scheduled_entry = {
            "id": f"scheduled_{len(self.scheduled)}",
            "content": content,
            "scheduled_time": scheduled_time,
            "platform": platform,
            "image_url": image_url,
            "video_url": video_url,
            "link": link,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
        }

        self.scheduled.append(scheduled_entry)
        self._save_scheduled()

        logger.info(f"Scheduled {platform} post for {scheduled_time}")

        return {
            "status": "success",
            "scheduled": scheduled_entry,
            "platform": platform,
        }

    def get_scheduled_posts(self) -> List[Dict]:
        """Get all scheduled posts"""
        return self.scheduled

    def cancel_scheduled_post(self, scheduled_id: str) -> Dict:
        """Cancel a scheduled post"""
        self.scheduled = [s for s in self.scheduled if s["id"] != scheduled_id]
        self._save_scheduled()

        return {
            "status": "success",
            "message": f"Cancelled scheduled post {scheduled_id}",
        }

    def get_posts(self, limit: int = 10, platform: str = None) -> List[Dict]:
        """Get posts, optionally filtered by platform"""
        posts = self.posts
        if platform:
            posts = [p for p in posts if p.get("platform") == platform]
        return posts[-limit:]

    def add_post_template(self, name: str, template: str) -> Dict:
        """Add a post template"""
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
        """Get all post templates"""
        return self.config.get("post_templates", [])

    def auto_generate_post(self, template_name: str, context: Dict) -> str:
        """Auto-generate post content from template"""
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
        """Enable or disable auto-posting"""
        self.config["auto_post_enabled"] = enabled
        self._save_config()

        return {
            "status": "success",
            "auto_post_enabled": enabled,
        }

    def get_status(self) -> Dict:
        """Get service status"""
        return {
            "authenticated": bool(self.config.get("access_token")),
            "facebook_page_configured": bool(self.config.get("page_id")),
            "instagram_account_configured": bool(
                self.config.get("instagram_account_id")
            ),
            "auto_post_enabled": self.config.get("auto_post_enabled", False),
            "total_posts": len(self.posts),
            "facebook_posts": len(
                [p for p in self.posts if p.get("platform") == "facebook"]
            ),
            "instagram_posts": len(
                [p for p in self.posts if p.get("platform") == "instagram"]
            ),
            "scheduled_posts": len(self.scheduled),
            "templates_count": len(self.config.get("post_templates", [])),
        }
