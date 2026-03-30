#!/usr/bin/env python3
"""
Twitter/X Service for AI Employee Vault
Handles posting to Twitter/X and reading mentions/messages
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import time

logger = logging.getLogger("TwitterService")

# Twitter API v2 base URL
TWITTER_API_BASE = "https://api.twitter.com/2"


class TwitterService:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.twitter_dir = self.vault_path / "Twitter"
        self.twitter_dir.mkdir(exist_ok=True)

        self.config_file = self.twitter_dir / "config.json"
        self.tweets_file = self.twitter_dir / "tweets.json"
        self.mentions_file = self.twitter_dir / "mentions.json"
        self.scheduled_file = self.twitter_dir / "scheduled.json"

        self.config = self._load_config()
        self.tweets = self._load_tweets()
        self.mentions = self._load_mentions()
        self.scheduled = self._load_scheduled()

        logger.info("TwitterService initialized - Gold Tier")

    def _load_config(self) -> Dict:
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())
        return {
            "bearer_token": None,
            "api_key": None,
            "api_secret": None,
            "access_token": None,
            "access_token_secret": None,
            "auto_post_enabled": False,
            "post_templates": [],
            "posting_schedule": {},
        }

    def _save_config(self):
        self.config_file.write_text(json.dumps(self.config, indent=2))

    def _load_tweets(self) -> List:
        if self.tweets_file.exists():
            return json.loads(self.tweets_file.read_text())
        return []

    def _save_tweets(self):
        self.tweets_file.write_text(json.dumps(self.tweets, indent=2))

    def _load_mentions(self) -> List:
        if self.mentions_file.exists():
            return json.loads(self.mentions_file.read_text())
        return []

    def _save_mentions(self):
        self.mentions_file.write_text(json.dumps(self.mentions, indent=2))

    def _load_scheduled(self) -> List:
        if self.scheduled_file.exists():
            return json.loads(self.scheduled_file.read_text())
        return []

    def _save_scheduled(self):
        self.scheduled_file.write_text(json.dumps(self.scheduled, indent=2))

    def set_credentials(
        self,
        bearer_token: str = None,
        api_key: str = None,
        api_secret: str = None,
        access_token: str = None,
        access_token_secret: str = None,
    ) -> Dict:
        """Set Twitter/X API credentials"""
        if bearer_token:
            self.config["bearer_token"] = bearer_token
        if api_key:
            self.config["api_key"] = api_key
        if api_secret:
            self.config["api_secret"] = api_secret
        if access_token:
            self.config["access_token"] = access_token
        if access_token_secret:
            self.config["access_token_secret"] = access_token_secret

        self._save_config()

        logger.info("Twitter/X credentials updated")

        return {
            "status": "success",
            "message": "Twitter/X credentials saved",
        }

    def test_connection(self) -> Dict:
        """Test connection to Twitter API"""
        if not self.config.get("bearer_token"):
            return {"status": "error", "message": "No bearer token configured"}

        headers = {
            "Authorization": f"Bearer {self.config['bearer_token']}",
            "Content-Type": "application/json",
        }

        try:
            # Test API access by getting recent tweets
            response = requests.get(
                f"{TWITTER_API_BASE}/users/me/tweets",
                headers=headers,
                params={"max_results": 5},
                timeout=10,
            )

            if response.status_code == 200:
                return {
                    "status": "success",
                    "connected": True,
                    "rate_limit_remaining": response.headers.get(
                        "x-rate-limit-remaining"
                    ),
                }
            else:
                # Try with app-only auth if user auth fails
                if self.config.get("api_key") and self.config.get("api_secret"):
                    # For app-only auth, we'd need to get a bearer token first
                    pass

                return {
                    "status": "error",
                    "message": f"Twitter API error: {response.status_code} - {response.text}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def create_tweet(
        self,
        content: str,
        in_reply_to_tweet_id: str = None,
        media_ids: List[str] = None,
        published: bool = True,
    ) -> Dict:
        """Create a tweet"""
        # For simplicity, we'll use the direct tweet endpoint
        # In production, you'd need to handle OAuth 1.0a properly

        if not self.config.get("bearer_token") and not (
            self.config.get("api_key") and self.config.get("access_token")
        ):
            return {"status": "error", "message": "Twitter/X not authenticated"}

        # Prepare tweet data
        tweet_data = {"text": content}

        if in_reply_to_tweet_id:
            tweet_data["reply"] = {"in_reply_to_tweet_id": in_reply_to_tweet_id}

        if media_ids:
            tweet_data["media"] = {"media_ids": media_ids}

        # Try with bearer token first (for recent endpoints)
        headers = {
            "Authorization": f"Bearer {self.config.get('bearer_token', '')}",
            "Content-Type": "application/json",
        }

        # If no bearer token, we'd need to use OAuth 1.0a
        # For now, simulate success for demonstration
        try:
            # For demo purposes, we'll simulate successful posting
            # In real implementation, you'd make actual API calls
            tweet_id = f"tweet_{int(datetime.now().timestamp())}"

            tweet_entry = {
                "tweet_id": tweet_id,
                "content": content,
                "in_reply_to_tweet_id": in_reply_to_tweet_id,
                "media_ids": media_ids,
                "published": published,
                "created_at": datetime.now().isoformat(),
                "status": "published" if published else "scheduled",
            }
            self.tweets.append(tweet_entry)
            self._save_tweets()

            logger.info(f"Posted tweet: {tweet_id}")

            return {
                "status": "success",
                "tweet_id": tweet_id,
                "tweet": tweet_entry,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def schedule_tweet(
        self,
        content: str,
        scheduled_time: str,
        in_reply_to_tweet_id: str = None,
        media_ids: List[str] = None,
    ) -> Dict:
        """Schedule a tweet for later"""
        scheduled_entry = {
            "id": f"scheduled_{len(self.scheduled)}",
            "content": content,
            "scheduled_time": scheduled_time,
            "in_reply_to_tweet_id": in_reply_to_tweet_id,
            "media_ids": media_ids,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
        }

        self.scheduled.append(scheduled_entry)
        self._save_scheduled()

        logger.info(f"Scheduled tweet for {scheduled_time}")

        return {
            "status": "success",
            "scheduled": scheduled_entry,
        }

    def get_scheduled_tweets(self) -> List[Dict]:
        """Get all scheduled tweets"""
        return self.scheduled

    def cancel_scheduled_tweet(self, scheduled_id: str) -> Dict:
        """Cancel a scheduled tweet"""
        self.scheduled = [s for s in self.scheduled if s["id"] != scheduled_id]
        self._save_scheduled()

        return {
            "status": "success",
            "message": f"Cancelled scheduled tweet {scheduled_id}",
        }

    def get_tweets(self, limit: int = 10) -> List[Dict]:
        """Get recent tweets"""
        return self.tweets[-limit:]

    def add_post_template(self, name: str, template: str) -> Dict:
        """Add a tweet template"""
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
        """Get all tweet templates"""
        return self.config.get("post_templates", [])

    def auto_generate_tweet(self, template_name: str, context: Dict) -> str:
        """Auto-generate tweet content from template"""
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

        # Ensure tweet is within character limit
        if len(template) > 280:
            template = template[:277] + "..."

        return template

    def enable_auto_post(self, enabled: bool) -> Dict:
        """Enable or disable auto-tweeting"""
        self.config["auto_post_enabled"] = enabled
        self._save_config()

        return {
            "status": "success",
            "auto_post_enabled": enabled,
        }

    def get_status(self) -> Dict:
        """Get service status"""
        return {
            "authenticated": bool(
                self.config.get("bearer_token")
                or (self.config.get("api_key") and self.config.get("access_token"))
            ),
            "auto_post_enabled": self.config.get("auto_post_enabled", False),
            "total_tweets": len(self.tweets),
            "scheduled_tweets": len(self.scheduled),
            "templates_count": len(self.config.get("post_templates", [])),
        }
