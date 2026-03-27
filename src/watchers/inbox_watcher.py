#!/usr/bin/env python3
"""
Inbox Watcher - Monitors Inbox folder for checkbox changes
Processes immediately when user checks a box in Obsidian
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed. Run: pip install watchdog")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.orchestrator import Orchestrator


class InboxHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str, orchestrator: Orchestrator):
        self.vault_path = Path(vault_path)
        self.inbox = self.vault_path / "Inbox"
        self.orchestrator = orchestrator
        self.last_processed = {}  # Track last modification time
        self.cooldown = 2  # Seconds to wait after file change

    def on_modified(self, event):
        if event.is_directory:
            return

        source = Path(event.src_path)
        if source.parent != self.inbox:
            return

        if not source.suffix == ".md":
            return

        # Check cooldown to avoid processing while file is being written
        current_time = time.time()
        last_time = self.last_processed.get(str(source), 0)

        if current_time - last_time < self.cooldown:
            return

        self.last_processed[str(source)] = current_time

        # Small delay to ensure file is fully written
        time.sleep(0.5)
        self._process_checkboxes(source)

    def on_created(self, event):
        if event.is_directory:
            return

        source = Path(event.src_path)
        if source.parent != self.inbox:
            return

        if source.suffix == ".md":
            time.sleep(0.5)
            print(f"[InboxWatcher] New file detected: {source.name}")

    def _process_checkboxes(self, filepath):
        try:
            # Ensure filepath is a Path object
            if isinstance(filepath, str):
                filepath = Path(filepath)

            # Check if file has any checked boxes
            content = filepath.read_text()

            # Check for each action checkbox
            actions = {
                "needs_action": "- [X] Move to Needs_Action" in content,
                "done": "- [X] Move to Done" in content,
                "pending_approval": "- [X] Move to Pending_Approval" in content,
                "rejected": "- [X] Move to Rejected" in content,
                "plans": "- [X] Move to Plans" in content,
                "approved": "- [X] Move to Approved" in content,
                "processed": "- [X] Move to Processed" in content,
                "briefings": "- [X] Move to Briefings" in content,
                "accounting": "- [X] Move to Accounting" in content,
            }

            moved = False

            if actions["done"]:
                if self.orchestrator.move_to_done(filepath.name, "Inbox"):
                    print(f"[InboxWatcher] ✓ Moved to Done: {filepath.name}")
                    moved = True

            elif actions["needs_action"]:
                if self.orchestrator.move_to_needs_action(filepath.name):
                    print(f"[InboxWatcher] ✓ Moved to Needs_Action: {filepath.name}")
                    moved = True

            elif actions["pending_approval"]:
                if self.orchestrator.move_to_pending_approval(filepath.name):
                    print(
                        f"[InboxWatcher] ✓ Moved to Pending_Approval: {filepath.name}"
                    )
                    moved = True

            elif actions["rejected"]:
                if self.orchestrator.move_to_rejected(filepath.name):
                    print(f"[InboxWatcher] ✓ Moved to Rejected: {filepath.name}")
                    moved = True

            elif actions["plans"]:
                if self.orchestrator.move_to_plans(filepath.name, "Inbox"):
                    print(f"[InboxWatcher] ✓ Moved to Plans: {filepath.name}")
                    moved = True

            elif actions["approved"]:
                if self.orchestrator.move_to_approved(filepath.name, "Inbox"):
                    print(f"[InboxWatcher] ✓ Moved to Approved: {filepath.name}")
                    moved = True

            elif actions["processed"]:
                if self.orchestrator.move_to_processed(filepath.name, "Inbox"):
                    print(f"[InboxWatcher] ✓ Moved to Processed: {filepath.name}")
                    moved = True

            elif actions["briefings"]:
                if self.orchestrator.move_to_briefings(filepath.name, "Inbox"):
                    print(f"[InboxWatcher] ✓ Moved to Briefings: {filepath.name}")
                    moved = True

            elif actions["accounting"]:
                if self.orchestrator.move_to_accounting(filepath.name, "Inbox"):
                    print(f"[InboxWatcher] ✓ Moved to Accounting: {filepath.name}")
                    moved = True

            if moved:
                # Update dashboard after moving
                self.orchestrator.update_dashboard()

        except Exception as e:
            print(f"[InboxWatcher] Error processing {filepath}: {e}")


class InboxWatcher:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.inbox = self.vault_path / "Inbox"
        self.inbox.mkdir(exist_ok=True)

        self.orchestrator = Orchestrator(vault_path)
        self.observer = Observer()
        self.handler = InboxHandler(vault_path, self.orchestrator)

    def run(self):
        if not WATCHDOG_AVAILABLE:
            print("Error: watchdog library required")
            return

        print(f"[InboxWatcher] Starting - monitoring: {self.inbox}")
        self.observer.schedule(self.handler, str(self.inbox), recursive=False)
        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[InboxWatcher] Stopping...")
            self.observer.stop()
        self.observer.join()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Inbox Watcher for AI Employee")
    parser.add_argument("--vault", required=True, help="Path to vault")
    args = parser.parse_args()

    if not WATCHDOG_AVAILABLE:
        print("Error: watchdog required. Run: pip install watchdog")
        sys.exit(1)

    watcher = InboxWatcher(args.vault)
    watcher.run()


if __name__ == "__main__":
    main()
