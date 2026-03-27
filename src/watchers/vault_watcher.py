#!/usr/bin/env python3
"""
Vault Watcher - Monitors ALL vault folders for file changes
Triggers appropriate actions when files arrive in any folder
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.orchestrator import Orchestrator


class VaultFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str, orchestrator: Orchestrator):
        self.vault_path = Path(vault_path)
        self.orchestrator = orchestrator
        self.last_processed = {}
        self.cooldown = 2

        # Map folders to their handlers
        self.folder_handlers = {
            "Inbox": self._handle_inbox,
            "Needs_Action": self._handle_needs_action,
            "Pending_Approval": self._handle_pending_approval,
            "Plans": self._handle_plans,
            "Approved": self._handle_approved,
            "Done": self._handle_done,
            "Rejected": self._handle_rejected,
        }

    def on_created(self, event):
        if event.is_directory:
            return
        self._process_file(event.src_path, "created")

    def on_modified(self, event):
        if event.is_directory:
            return
        self._process_file(event.src_path, "modified")

    def _process_file(self, filepath, event_type):
        try:
            filepath = Path(filepath)
            if filepath.suffix != ".md":
                return

            # Get parent folder name
            parent = filepath.parent.name
            if parent not in self.folder_handlers:
                return

            # Cooldown check
            current_time = time.time()
            last_time = self.last_processed.get(str(filepath), 0)
            if current_time - last_time < self.cooldown:
                return
            self.last_processed[str(filepath)] = current_time

            # Small delay for file to be fully written
            time.sleep(0.5)

            # Call appropriate handler
            handler = self.folder_handlers[parent]
            handler(filepath, event_type)

        except Exception as e:
            print(f"[VaultWatcher] Error: {e}")

    def _handle_inbox(self, filepath, event_type):
        """Handle new files in Inbox - check for workflow checkboxes"""
        content = filepath.read_text()

        # Check for checked workflow boxes
        if "- [X] Move to Done" in content:
            if self.orchestrator.move_to_done(filepath.name, "Inbox"):
                print(f"[VaultWatcher] ✓ Inbox → Done: {filepath.name}")
                self._update_dashboard()
                return

        elif "- [X] Move to Needs_Action" in content:
            if self.orchestrator.move_to_needs_action(filepath.name):
                print(f"[VaultWatcher] ✓ Inbox → Needs_Action: {filepath.name}")
                self._update_dashboard()
                return

        elif "- [X] Move to Pending_Approval" in content:
            if self.orchestrator.move_to_pending_approval(filepath.name):
                print(f"[VaultWatcher] ✓ Inbox → Pending_Approval: {filepath.name}")
                self._update_dashboard()
                return

        elif "- [X] Move to Plans" in content:
            if self.orchestrator.move_to_plans(filepath.name, "Inbox"):
                print(f"[VaultWatcher] ✓ Inbox → Plans: {filepath.name}")
                self._update_dashboard()
                return

        elif "- [X] Move to Approved" in content:
            if self.orchestrator.move_to_approved(filepath.name, "Inbox"):
                print(f"[VaultWatcher] ✓ Inbox → Approved: {filepath.name}")
                self._update_dashboard()
                return

        elif "- [X] Move to Rejected" in content:
            if self.orchestrator.move_to_rejected(filepath.name):
                print(f"[VaultWatcher] ✓ Inbox → Rejected: {filepath.name}")
                self._update_dashboard()
                return

        elif "- [X] Move to Processed" in content:
            if self.orchestrator.move_to_processed(filepath.name, "Inbox"):
                print(f"[VaultWatcher] ✓ Inbox → Processed: {filepath.name}")
                self._update_dashboard()
                return

        elif "- [X] Move to Briefings" in content:
            if self.orchestrator.move_to_briefings(filepath.name, "Inbox"):
                print(f"[VaultWatcher] ✓ Inbox → Briefings: {filepath.name}")
                self._update_dashboard()
                return

        elif "- [X] Move to Accounting" in content:
            if self.orchestrator.move_to_accounting(filepath.name, "Inbox"):
                print(f"[VaultWatcher] ✓ Inbox → Accounting: {filepath.name}")
                self._update_dashboard()
                return

        # New email detected in inbox
        if event_type == "created":
            print(f"[VaultWatcher] 📥 New in Inbox: {filepath.name}")

    def _handle_needs_action(self, filepath, event_type):
        """Handle files in Needs_Action folder"""
        if event_type == "created":
            print(f"[VaultWatcher] ⚡ New in Needs_Action: {filepath.name}")
            # Could trigger Claude to process this

    def _handle_pending_approval(self, filepath, event_type):
        """Handle files in Pending_Approval folder"""
        if event_type == "created":
            print(f"[VaultWatcher] ⏳ New in Pending_Approval: {filepath.name}")

    def _handle_plans(self, filepath, event_type):
        """Handle files in Plans folder"""
        if event_type == "created":
            print(f"[VaultWatcher] 📋 New in Plans: {filepath.name}")

    def _handle_approved(self, filepath, event_type):
        """Handle files in Approved folder - execute action"""
        if event_type == "created":
            print(f"[VaultWatcher] ✅ New in Approved: {filepath.name}")
            # Could trigger execution of approved actions

    def _handle_done(self, filepath, event_type):
        """Handle files in Done folder"""
        if event_type == "created":
            print(f"[VaultWatcher] ✓ New in Done: {filepath.name}")

    def _handle_rejected(self, filepath, event_type):
        """Handle files in Rejected folder"""
        if event_type == "created":
            print(f"[VaultWatcher] ✗ New in Rejected: {filepath.name}")

    def _update_dashboard(self):
        try:
            self.orchestrator.update_dashboard()
        except:
            pass


class VaultWatcher:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.orchestrator = Orchestrator(vault_path)
        self.observer = Observer()
        self.handler = VaultFolderHandler(vault_path, self.orchestrator)

        # All folders to monitor
        self.folders = [
            "Inbox",
            "Needs_Action",
            "Pending_Approval",
            "Plans",
            "Approved",
            "Done",
            "Rejected",
            "Processed",
            "Briefings",
            "Accounting",
        ]

    def run(self):
        print(f"[VaultWatcher] Starting - monitoring vault: {self.vault_path}")

        # Monitor each folder
        for folder in self.folders:
            folder_path = self.vault_path / folder
            if folder_path.exists():
                self.observer.schedule(self.handler, str(folder_path), recursive=False)
                print(f"  Monitoring: {folder}/")

        self.observer.start()
        print("[VaultWatcher] Running... Press Ctrl+C to stop")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[VaultWatcher] Stopping...")
            self.observer.stop()
        self.observer.join()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Vault Watcher for AI Employee")
    parser.add_argument("--vault", required=True, help="Path to vault")
    parser.add_argument("--folder", help="Monitor specific folder only")
    args = parser.parse_args()

    watcher = VaultWatcher(args.vault)
    watcher.run()


if __name__ == "__main__":
    main()
