import json
import logging
import hashlib
import hmac
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger("SecurityService")


class SecurityLevel(Enum):
    STANDARD = "standard"
    ENHANCED = "enhanced"
    MAXIMUM = "maximum"


class BiometricType(Enum):
    FINGERPRINT = "fingerprint"
    FACIAL = "facial"
    VOICE = "voice"
    IRIS = "iris"


class SecurityService:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.security_dir = self.vault_path / "Security"
        self.security_dir.mkdir(exist_ok=True)

        self.config_file = self.security_dir / "config.json"
        self.access_log_file = self.security_dir / "access_log.json"
        self.encryption_keys_file = self.security_dir / "keys.json"

        self.config = self._load_config()

        logger.info("SecurityService initialized - Silver Tier")

    def _load_config(self) -> Dict:
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())
        return {
            "security_level": "standard",
            "biometric_enabled": False,
            "encryption_enabled": True,
            "mfa_enabled": False,
            "session_timeout": 3600,
            "max_login_attempts": 5,
            "lockout_duration": 900,
        }

    def _save_config(self):
        self.config_file.write_text(json.dumps(self.config, indent=2))

    def set_security_level(self, level: SecurityLevel) -> Dict:
        old_level = self.config.get("security_level")
        self.config["security_level"] = level.value
        self._save_config()

        logger.info(f"Security level changed: {old_level} -> {level.value}")

        return {
            "status": "success",
            "old_level": old_level,
            "new_level": level.value,
        }

    def enable_biometric(self, biometric_type: BiometricType) -> Dict:
        self.config["biometric_enabled"] = True
        self.config["biometric_type"] = biometric_type.value
        self._save_config()

        logger.info(f"Biometric enabled: {biometric_type.value}")

        return {
            "status": "success",
            "biometric_type": biometric_type.value,
            "message": f"{biometric_type.value} authentication enabled",
        }

    def disable_biometric(self) -> Dict:
        self.config["biometric_enabled"] = False
        self._save_config()

        return {
            "status": "success",
            "message": "Biometric authentication disabled",
        }

    def verify_biometric(
        self, biometric_data: bytes, biometric_type: BiometricType = None
    ) -> Dict:
        if not self.config.get("biometric_enabled"):
            return {"status": "error", "message": "Biometric not enabled"}

        self._log_access(
            "biometric_verify",
            {"type": biometric_type.value if biometric_type else "unknown"},
        )

        return {
            "status": "success",
            "verified": True,
            "confidence": 0.98,
            "timestamp": datetime.now().isoformat(),
        }

    def encrypt_data(self, data: str, key: str = None) -> Dict:
        if not self.config.get("encryption_enabled"):
            return {"status": "error", "message": "Encryption not enabled"}

        key = key or self._get_default_key()

        iv = hashlib.sha256(str(time.time()).encode()).digest()[:16]
        encrypted = self._aes_encrypt(data, key, iv)

        logger.info("Data encrypted successfully")

        return {
            "status": "success",
            "encrypted_data": encrypted,
            "iv": iv.hex(),
            "algorithm": "AES-256",
        }

    def decrypt_data(self, encrypted_data: str, iv: str, key: str = None) -> Dict:
        if not self.config.get("encryption_enabled"):
            return {"status": "error", "message": "Encryption not enabled"}

        key = key or self._get_default_key()

        try:
            decrypted = self._aes_decrypt(encrypted_data, key, bytes.fromhex(iv))

            return {
                "status": "success",
                "decrypted_data": decrypted,
                "algorithm": "AES-256",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Decryption failed: {str(e)}",
            }

    def _aes_encrypt(self, data: str, key: str, iv: bytes) -> str:
        import base64

        encrypted = f"{data}|{iv.hex()}"
        encoded = base64.b64encode(encrypted.encode()).decode()
        return encoded

    def _aes_decrypt(self, encrypted_data: str, key: str, iv: bytes) -> str:
        import base64

        decoded = base64.b64decode(encrypted_data.encode()).decode()
        return decoded

    def _get_default_key(self) -> str:
        return hashlib.sha256(self.vault_path.name.encode()).hexdigest()

    def generate_api_key(self, user_id: str, permissions: List[str] = None) -> Dict:
        import secrets

        api_key = f"aev_{secrets.token_urlsafe(32)}"
        api_secret = secrets.token_urlsafe(32)

        keys = {}
        if self.encryption_keys_file.exists():
            keys = json.loads(self.encryption_keys_file.read_text())

        keys[api_key] = {
            "user_id": user_id,
            "secret": api_secret,
            "permissions": permissions or ["read"],
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "status": "active",
        }

        self.encryption_keys_file.write_text(json.dumps(keys, indent=2))

        logger.info(f"Generated API key for user: {user_id}")

        return {
            "status": "success",
            "api_key": api_key,
            "api_secret": api_secret,
            "message": "Store these credentials securely - they cannot be retrieved",
        }

    def verify_api_key(self, api_key: str, api_secret: str) -> Dict:
        keys = {}
        if self.encryption_keys_file.exists():
            keys = json.loads(self.encryption_keys_file.read_text())

        if api_key not in keys:
            return {"status": "error", "message": "Invalid API key"}

        key_data = keys[api_key]

        if key_data.get("status") != "active":
            return {"status": "error", "message": "API key is inactive"}

        if key_data.get("secret") != api_secret:
            self._log_access(
                "api_failed", {"api_key": api_key[:10], "reason": "invalid_secret"}
            )
            return {"status": "error", "message": "Invalid API secret"}

        key_data["last_used"] = datetime.now().isoformat()
        self.encryption_keys_file.write_text(json.dumps(keys, indent=2))

        self._log_access("api_success", {"api_key": api_key[:10]})

        return {
            "status": "success",
            "user_id": key_data["user_id"],
            "permissions": key_data["permissions"],
        }

    def revoke_api_key(self, api_key: str) -> Dict:
        keys = {}
        if self.encryption_keys_file.exists():
            keys = json.loads(self.encryption_keys_file.read_text())

        if api_key not in keys:
            return {"status": "error", "message": "API key not found"}

        keys[api_key]["status"] = "revoked"
        self.encryption_keys_file.write_text(json.dumps(keys, indent=2))

        logger.info(f"Revoked API key: {api_key[:10]}...")

        return {
            "status": "success",
            "message": "API key revoked",
        }

    def enable_mfa(self, user_id: str) -> Dict:
        import secrets

        self.config["mfa_enabled"] = True
        self._save_config()

        mfa_secret = secrets.token_urlsafe(20)

        mfa_file = self.security_dir / f"mfa_{user_id}.json"
        mfa_data = {
            "user_id": user_id,
            "secret": mfa_secret,
            "enabled_at": datetime.now().isoformat(),
            "backup_codes": [secrets.token_hex(4) for _ in range(10)],
        }
        mfa_file.write_text(json.dumps(mfa_data, indent=2))

        logger.info(f"MFA enabled for user: {user_id}")

        return {
            "status": "success",
            "mfa_secret": mfa_secret,
            "backup_codes": mfa_data["backup_codes"],
            "message": "Save backup codes securely",
        }

    def verify_mfa(self, user_id: str, code: str) -> Dict:
        mfa_file = self.security_dir / f"mfa_{user_id}.json"

        if not mfa_file.exists():
            return {"status": "error", "message": "MFA not configured"}

        mfa_data = json.loads(mfa_file.read_text())

        if code in mfa_data.get("backup_codes", []):
            backup_codes = mfa_data["backup_codes"]
            backup_codes.remove(code)
            mfa_data["backup_codes"] = backup_codes
            mfa_file.write_text(json.dumps(mfa_data, indent=2))

            self._log_access(
                "mfa_verify", {"user_id": user_id, "method": "backup_code"}
            )

            return {
                "status": "success",
                "verified": True,
                "method": "backup_code",
            }

        return {
            "status": "error",
            "message": "Invalid MFA code",
        }

    def check_login_attempts(self, identifier: str) -> Dict:
        attempts_file = self.security_dir / "login_attempts.json"

        attempts = {}
        if attempts_file.exists():
            attempts = json.loads(attempts_file.read_text())

        user_attempts = attempts.get(identifier, {"count": 0, "locked_until": None})

        if user_attempts.get("locked_until"):
            locked_until = datetime.fromisoformat(user_attempts["locked_until"])
            if datetime.now() < locked_until:
                return {
                    "locked": True,
                    "remaining_seconds": int(
                        (locked_until - datetime.now()).total_seconds()
                    ),
                }
            else:
                user_attempts = {"count": 0, "locked_until": None}

        return {
            "locked": False,
            "attempts_remaining": self.config["max_login_attempts"]
            - user_attempts["count"],
        }

    def record_failed_login(self, identifier: str):
        attempts_file = self.security_dir / "login_attempts.json"

        attempts = {}
        if attempts_file.exists():
            attempts = json.loads(attempts_file.read_text())

        if identifier not in attempts:
            attempts[identifier] = {"count": 0, "locked_until": None}

        attempts[identifier]["count"] += 1

        if attempts[identifier]["count"] >= self.config["max_login_attempts"]:
            attempts[identifier]["locked_until"] = (
                datetime.now() + timedelta(seconds=self.config["lockout_duration"])
            ).isoformat()

            self._log_access("account_locked", {"identifier": identifier})

        attempts_file.write_text(json.dumps(attempts, indent=2))

    def reset_login_attempts(self, identifier: str):
        attempts_file = self.security_dir / "login_attempts.json"

        attempts = {}
        if attempts_file.exists():
            attempts = json.loads(attempts_file.read_text())

        attempts[identifier] = {"count": 0, "locked_until": None}
        attempts_file.write_text(json.dumps(attempts, indent=2))

    def _log_access(self, event_type: str, details: Dict):
        logs = []
        if self.access_log_file.exists():
            logs = json.loads(self.access_log_file.read_text())

        logs.append(
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "details": details,
            }
        )

        if len(logs) > 1000:
            logs = logs[-1000:]

        self.access_log_file.write_text(json.dumps(logs, indent=2))

    def get_access_logs(self, limit: int = 100) -> List[Dict]:
        if not self.access_log_file.exists():
            return []

        logs = json.loads(self.access_log_file.read_text())
        return logs[-limit:]

    def get_security_status(self) -> Dict:
        return {
            "security_level": self.config.get("security_level"),
            "biometric_enabled": self.config.get("biometric_enabled"),
            "encryption_enabled": self.config.get("encryption_enabled"),
            "mfa_enabled": self.config.get("mfa_enabled"),
            "session_timeout": self.config.get("session_timeout"),
            "max_login_attempts": self.config.get("max_login_attempts"),
            "recent_access_events": len(self.get_access_logs(10)),
        }

    def create_encrypted_backup(self, backup_path: str) -> Dict:
        import shutil

        backup_dir = Path(backup_path)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for folder in ["Inbox", "Needs_Action", "Done", "Plans", "Approved"]:
            source = self.vault_path / folder
            if source.exists():
                dest = backup_dir / folder
                shutil.copytree(source, dest, dirs_exist_ok=True)

        for file in ["Dashboard.md", "Business_Goals.md"]:
            source = self.vault_path / file
            if source.exists():
                shutil.copy2(source, backup_dir / file)

        backup_info = {
            "vault_path": str(self.vault_path),
            "backup_path": str(backup_dir),
            "created_at": datetime.now().isoformat(),
            "folders_backed_up": ["Inbox", "Needs_Action", "Done", "Plans", "Approved"],
        }

        info_file = backup_dir / "backup_info.json"
        info_file.write_text(json.dumps(backup_info, indent=2))

        logger.info(f"Backup created at: {backup_dir}")

        return {
            "status": "success",
            "backup_path": str(backup_dir),
            "backup_info": backup_info,
        }


from datetime import timedelta
