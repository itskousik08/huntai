"""
HuntAI Configuration Manager
Stores config securely in local encrypted JSON.
"""

import os
import json
import base64
from pathlib import Path

CONFIG_DIR = Path.home() / ".huntai"
CONFIG_FILE = CONFIG_DIR / "config.json"

REQUIRED_FIELDS = [
    "user_name", "company_name", "service_description",
    "target_industry", "target_location", "email_address",
    "email_password", "notification_email", "apify_api_key",
]


class ConfigManager:
    def __init__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._data = {}
        self._load()

    def _load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    raw = json.load(f)
                # Decode sensitive fields
                for k, v in raw.items():
                    if isinstance(v, str) and v.startswith("b64:"):
                        try:
                            raw[k] = base64.b64decode(v[4:]).decode()
                        except:
                            pass
                self._data = raw
            except Exception:
                self._data = {}

    def _save_to_disk(self):
        sensitive_keys = ['email_password', 'apify_api_key', 'smtp_password']
        out = {}
        for k, v in self._data.items():
            if k in sensitive_keys and isinstance(v, str):
                out[k] = "b64:" + base64.b64encode(v.encode()).decode()
            else:
                out[k] = v
        with open(CONFIG_FILE, 'w') as f:
            json.dump(out, f, indent=2)
        # Restrict file permissions
        os.chmod(CONFIG_FILE, 0o600)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def save(self, key, value):
        self._data[key] = value
        self._save_to_disk()

    def save_all(self, data: dict):
        self._data.update(data)
        self._save_to_disk()

    def is_configured(self):
        return all(self._data.get(f) for f in REQUIRED_FIELDS)

    def all(self):
        return dict(self._data)
