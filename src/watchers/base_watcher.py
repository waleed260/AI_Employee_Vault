#!/usr/bin/env python3
import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.processed_ids = self.vault_path / ".processed_ids"
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self._load_processed_ids()

    def _load_processed_ids(self):
        if self.processed_ids.exists():
            with open(self.processed_ids, "r") as f:
                self._processed = set(line.strip() for line in f)
        else:
            self._processed = set()

    def _save_processed_id(self, id_str: str):
        self._processed.add(id_str)
        with open(self.processed_ids, "a") as f:
            f.write(f"{id_str}\n")

    def _is_processed(self, id_str: str) -> bool:
        return id_str in self._processed

    @abstractmethod
    def check_for_updates(self) -> list:
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        pass

    def run(self):
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Monitoring: {self.vault_path}")
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    try:
                        filepath = self.create_action_file(item)
                        self.logger.info(f"Created action file: {filepath}")
                    except Exception as e:
                        self.logger.error(f"Error creating action file: {e}")
            except Exception as e:
                self.logger.error(f"Error in check loop: {e}")
            time.sleep(self.check_interval)

    def trigger_claude(self, message: str = "New items detected"):
        self.logger.info(f"[CLAUDE] {message}")
