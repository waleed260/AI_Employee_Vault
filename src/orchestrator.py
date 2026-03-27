import os
import sys
import time
import logging
import subprocess
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

sys.path.insert(0, str(Path(__file__).parent))
from gmail_service import GmailService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Orchestrator")


class Orchestrator:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = True
        self.gmail_service = GmailService(
            credentials_path=str(Path(__file__).parent / "credentials.json"),
            token_path=str(Path(__file__).parent / "gmail_token.json"),
        )
        self._unread_emails: List[dict] = []

    def check_unread_emails(self) -> List[dict]:
        try:
            self._unread_emails = self.gmail_service.get_recent_unread(5)
            return self._unread_emails
        except Exception as e:
            logger.warning(f"Failed to check emails: {e}")
            return []

    def sync_inbox(self):
        inbox = self.vault_path / "Inbox"
        inbox.mkdir(exist_ok=True)
        logger.info(f"Syncing emails to: {inbox}")

        try:
            emails = self.gmail_service.get_inbox_emails(limit=20)
            logger.info(f"Retrieved {len(emails)} emails from Gmail")
        except Exception as e:
            logger.error(f"Failed to get inbox emails: {e}")
            return

        existing_ids = set()
        for f in inbox.glob("EMAIL_*.md"):
            parts = f.stem.split("_")
            if len(parts) >= 2:
                existing_ids.add(parts[1])

        for email in emails:
            email_id = email["id"]
            safe_subject = email["subject"][:50].replace("/", "-").replace("\\", "-")
            filepath = inbox / f"EMAIL_{email_id}_{safe_subject}.md"

            if email_id not in existing_ids:
                content = f"""---
type: email
source: gmail
id: {email_id}
from: {email["from"]}
date: {email.get("date", "Unknown")}
unread: {email["unread"]}
status: pending
---

## {email["subject"]}

**From:** {email["from"]}  
**Date:** {email.get("date", "Unknown")}

---

{email["body"]}

---

## Actions

### Quick Actions
- [ ] Mark as read
- [ ] Archive

### Workflow Actions
- [ ] Move to Needs_Action
- [ ] Move to Pending_Approval
- [ ] Move to Plans
- [ ] Move to Approved
- [ ] Move to Done
- [ ] Move to Rejected

### Special Actions
- [ ] Move to Processed
- [ ] Move to Briefings
- [ ] Move to Accounting

"""
                filepath.write_text(content)
                logger.info(f"Saved email to Inbox: {email['subject']}")
            else:
                existing_content = filepath.read_text()
                import re

                has_checked_boxes = bool(re.search(r"- \[X\]", existing_content))
                if has_checked_boxes:
                    logger.info(f"Skipping {email_id} - has user actions")
                elif f"unread: {email['unread']}" not in existing_content:
                    updated_content = existing_content.replace(
                        "unread: ", f"unread: {email['unread']}"
                    )
                    filepath.write_text(updated_content)
                    logger.info(f"Updated email status: {email_id}")

    def setup_folders(self):
        folders = [
            "Inbox",
            "Needs_Action",
            "Done",
            "Plans",
            "Approved",
            "Rejected",
            "Pending_Approval",
            "Accounting",
            "Briefings",
            "Logs",
            "Drops",
        ]
        for folder in folders:
            folder_path = self.vault_path / folder
            folder_path.mkdir(exist_ok=True)
        logger.info(f"Vault folders ready: {self.vault_path}")

    def check_needs_action(self) -> list:
        needs_action = self.vault_path / "Needs_Action"
        items = list(needs_action.glob("*.md"))
        items = [f for f in items if not f.name.startswith(".")]
        return items

    def check_pending_approval(self) -> list:
        pending = self.vault_path / "Pending_Approval"
        items = list(pending.glob("*.md"))
        return items

    def move_to_needs_action(self, filename: str) -> bool:
        inbox = self.vault_path / "Inbox"
        needs_action = self.vault_path / "Needs_Action"
        source = inbox / filename
        if not source.exists():
            logger.warning(f"File not found in Inbox: {filename}")
            return False
        dest = needs_action / filename
        source.rename(dest)
        self._update_email_status(dest, "needs_action")
        logger.info(f"Moved to Needs_Action: {filename}")
        return True

    def move_to_done(self, filename: str, from_folder: str = "Inbox") -> bool:
        source_folder = self.vault_path / from_folder
        if from_folder == "Needs_Action":
            source_folder = self.vault_path / "Needs_Action"
        done_folder = self.vault_path / "Done"
        source = source_folder / filename
        if not source.exists():
            logger.warning(f"File not found: {filename} in {from_folder}")
            return False
        dest = done_folder / filename
        source.rename(dest)
        self._update_email_status(dest, "done")
        logger.info(f"Moved to Done: {filename}")
        return True

    def move_to_inbox(self, filename: str) -> bool:
        needs_action = self.vault_path / "Needs_Action"
        inbox = self.vault_path / "Inbox"
        source = needs_action / filename
        if not source.exists():
            logger.warning(f"File not found in Needs_Action: {filename}")
            return False
        dest = inbox / filename
        source.rename(dest)
        self._update_email_status(dest, "pending")
        logger.info(f"Moved to Inbox: {filename}")
        return True

    def _update_email_status(self, filepath: Path, status: str):
        if not filepath.exists():
            return
        content = filepath.read_text()
        import re

        new_content = re.sub(r"status:\s*\w+", f"status: {status}", content)
        if "status:" not in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("---") and i > 0:
                    lines.insert(i + 1, f"status: {status}")
                    break
            new_content = "\n".join(lines)
        filepath.write_text(new_content)

    def check_done(self) -> list:
        done = self.vault_path / "Done"
        items = list(done.glob("*.md"))
        return items

    def check_inbox_checkboxes(self) -> Dict[str, List[str]]:
        inbox = self.vault_path / "Inbox"
        actions = {
            "needs_action": [],
            "done": [],
            "rejected": [],
            "pending_approval": [],
        }

        import re

        for f in inbox.glob("*.md"):
            content = f.read_text()

            if re.search(r"- \[X\] Move to Needs_Action", content):
                actions["needs_action"].append(f.name)
            if re.search(r"- \[X\] Move to Done", content):
                actions["done"].append(f.name)
            if re.search(r"- \[X\] Move to Rejected", content):
                actions["rejected"].append(f.name)
            if re.search(r"- \[X\] Move to Pending_Approval", content):
                actions["pending_approval"].append(f.name)

        return actions

    def process_inbox_checkboxes(self):
        actions = self.check_inbox_checkboxes()
        moved_count = 0

        for filename in actions["needs_action"]:
            if self.move_to_needs_action(filename):
                self.log_action("move", f"moved {filename} to Needs_Action")
                moved_count += 1

        for filename in actions["done"]:
            if self.move_to_done(filename, "Inbox"):
                self.log_action("done", f"marked {filename} as done")
                moved_count += 1

        for filename in actions["pending_approval"]:
            if self.move_to_pending_approval(filename):
                self.log_action("pending", f"moved {filename} to Pending_Approval")
                moved_count += 1

        for filename in actions["rejected"]:
            if self.move_to_rejected(filename):
                self.log_action("rejected", f"moved {filename} to Rejected")
                moved_count += 1

        if moved_count > 0:
            logger.info(f"Processed {moved_count} inbox checkbox actions")

    def move_to_pending_approval(self, filename: str) -> bool:
        inbox = self.vault_path / "Inbox"
        pending = self.vault_path / "Pending_Approval"
        source = inbox / filename
        if not source.exists():
            logger.warning(f"File not found in Inbox: {filename}")
            return False
        dest = pending / filename
        source.rename(dest)
        self._update_email_status(dest, "pending_approval")
        logger.info(f"Moved to Pending_Approval: {filename}")
        return True

    def move_to_rejected(self, filename: str) -> bool:
        inbox = self.vault_path / "Inbox"
        rejected = self.vault_path / "Rejected"
        source = inbox / filename
        if not source.exists():
            logger.warning(f"File not found in Inbox: {filename}")
            return False
        dest = rejected / filename
        source.rename(dest)
        self._update_email_status(dest, "rejected")
        logger.info(f"Moved to Rejected: {filename}")
        return True

    def move_to_plans(self, filename: str, from_folder: str = "Needs_Action") -> bool:
        source_folder = self.vault_path / from_folder
        plans = self.vault_path / "Plans"
        source = source_folder / filename
        if not source.exists():
            logger.warning(f"File not found in {from_folder}: {filename}")
            return False
        dest = plans / filename
        source.rename(dest)
        self._update_email_status(dest, "planned")
        logger.info(f"Moved to Plans: {filename}")
        return True

    def move_to_approved(
        self, filename: str, from_folder: str = "Pending_Approval"
    ) -> bool:
        source_folder = self.vault_path / from_folder
        approved = self.vault_path / "Approved"
        source = source_folder / filename
        if not source.exists():
            logger.warning(f"File not found in {from_folder}: {filename}")
            return False
        dest = approved / filename
        source.rename(dest)
        self._update_email_status(dest, "approved")
        logger.info(f"Moved to Approved: {filename}")
        return True

    def move_to_processed(self, filename: str, from_folder: str = "Plans") -> bool:
        source_folder = self.vault_path / from_folder
        processed = self.vault_path / "Processed"
        source = source_folder / filename
        if not source.exists():
            logger.warning(f"File not found in {from_folder}: {filename}")
            return False
        dest = processed / filename
        source.rename(dest)
        self._update_email_status(dest, "processed")
        logger.info(f"Moved to Processed: {filename}")
        return True

    def move_to_briefings(self, filename: str, from_folder: str = "Plans") -> bool:
        source_folder = self.vault_path / from_folder
        briefings = self.vault_path / "Briefings"
        source = source_folder / filename
        if not source.exists():
            logger.warning(f"File not found in {from_folder}: {filename}")
            return False
        dest = briefings / filename
        source.rename(dest)
        self._update_email_status(dest, "briefed")
        logger.info(f"Moved to Briefings: {filename}")
        return True

    def move_to_accounting(self, filename: str, from_folder: str = "Approved") -> bool:
        source_folder = self.vault_path / from_folder
        accounting = self.vault_path / "Accounting"
        source = source_folder / filename
        if not source.exists():
            logger.warning(f"File not found in {from_folder}: {filename}")
            return False
        dest = accounting / filename
        source.rename(dest)
        self._update_email_status(dest, "accounted")
        logger.info(f"Moved to Accounting: {filename}")
        return True

    def check_plans(self) -> list:
        plans = self.vault_path / "Plans"
        return list(plans.glob("*.md"))

    def check_approved(self) -> list:
        approved = self.vault_path / "Approved"
        return list(approved.glob("*.md"))

    def check_processed(self) -> list:
        processed = self.vault_path / "Processed"
        return list(processed.glob("*.md"))

    def check_rejected(self) -> list:
        rejected = self.vault_path / "Rejected"
        return list(rejected.glob("*.md"))

    def check_briefings(self) -> list:
        briefings = self.vault_path / "Briefings"
        return list(briefings.glob("*.md"))

    def check_accounting(self) -> list:
        accounting = self.vault_path / "Accounting"
        return list(accounting.glob("*.md"))

    def check_needs_action_from_folder(self, folder: str) -> list:
        folder_path = self.vault_path / folder
        items = list(folder_path.glob("*.md"))
        items = [f for f in items if not f.name.startswith(".")]
        return items

    def check_inbox_checkboxes(self) -> Dict[str, List[str]]:
        inbox = self.vault_path / "Inbox"
        actions = {
            "needs_action": [],
            "done": [],
            "rejected": [],
            "pending_approval": [],
            "plans": [],
            "approved": [],
            "processed": [],
            "briefings": [],
            "accounting": [],
        }

        import re

        for f in inbox.glob("*.md"):
            content = f.read_text()

            if re.search(r"- \[X\] Move to Needs_Action", content):
                actions["needs_action"].append(f.name)
            if re.search(r"- \[X\] Move to Done", content):
                actions["done"].append(f.name)
            if re.search(r"- \[X\] Move to Rejected", content):
                actions["rejected"].append(f.name)
            if re.search(r"- \[X\] Move to Pending_Approval", content):
                actions["pending_approval"].append(f.name)
            if re.search(r"- \[X\] Move to Plans", content):
                actions["plans"].append(f.name)
            if re.search(r"- \[X\] Move to Approved", content):
                actions["approved"].append(f.name)
            if re.search(r"- \[X\] Move to Processed", content):
                actions["processed"].append(f.name)
            if re.search(r"- \[X\] Move to Briefings", content):
                actions["briefings"].append(f.name)
            if re.search(r"- \[X\] Move to Accounting", content):
                actions["accounting"].append(f.name)

        return actions

    def process_inbox_checkboxes(self):
        actions = self.check_inbox_checkboxes()
        moved_count = 0

        for filename in actions["needs_action"]:
            if self.move_to_needs_action(filename):
                self.log_action("move", f"moved {filename} to Needs_Action")
                moved_count += 1

        for filename in actions["done"]:
            if self.move_to_done(filename, "Inbox"):
                self.log_action("done", f"marked {filename} as done")
                moved_count += 1

        for filename in actions["pending_approval"]:
            if self.move_to_pending_approval(filename):
                self.log_action("pending", f"moved {filename} to Pending_Approval")
                moved_count += 1

        for filename in actions["rejected"]:
            if self.move_to_rejected(filename):
                self.log_action("rejected", f"moved {filename} to Rejected")
                moved_count += 1

        for filename in actions["plans"]:
            if self.move_to_plans(filename, "Inbox"):
                self.log_action("plans", f"moved {filename} to Plans")
                moved_count += 1

        for filename in actions["approved"]:
            if self.move_to_approved(filename, "Inbox"):
                self.log_action("approved", f"moved {filename} to Approved")
                moved_count += 1

        for filename in actions["processed"]:
            if self.move_to_processed(filename, "Inbox"):
                self.log_action("processed", f"moved {filename} to Processed")
                moved_count += 1

        for filename in actions["briefings"]:
            if self.move_to_briefings(filename, "Inbox"):
                self.log_action("briefings", f"moved {filename} to Briefings")
                moved_count += 1

        for filename in actions["accounting"]:
            if self.move_to_accounting(filename, "Inbox"):
                self.log_action("accounting", f"moved {filename} to Accounting")
                moved_count += 1

        if moved_count > 0:
            logger.info(f"Processed {moved_count} inbox checkbox actions")

    def process_approved_items(self):
        approved = self.vault_path / "Approved"
        for item in approved.glob("*.md"):
            logger.info(f"Processing approved item: {item.name}")
            item.unlink()

    def update_dashboard(self):
        dashboard = self.vault_path / "Dashboard.md"
        pending_count = len(self.check_needs_action())
        approved_count = len(self.check_pending_approval())
        done_count = len(self.check_done())
        plans_count = len(self.check_plans())
        processed_count = len(self.check_processed())
        rejected_count = len(self.check_rejected())
        briefings_count = len(self.check_briefings())
        accounting_count = len(self.check_accounting())

        inbox = self.vault_path / "Inbox"
        inbox_emails = list(inbox.glob("EMAIL_*.md"))
        unread_count = 0
        for f in inbox_emails:
            content = f.read_text()
            if "unread: True" in content:
                unread_count += 1

        email_rows = ""
        inbox_emails = self._get_inbox_for_dashboard()
        for email in inbox_emails:
            status = "🔴" if email.get("unread") else "⚪"
            email_rows += f"| {status} | {email['from']} | {email['subject']} |\n"

        if not email_rows:
            email_rows = "| | _No emails_ | _None_ |\n"

        needs_action_items = self._get_needs_action_items()
        needs_action_rows = ""
        for item in needs_action_items:
            needs_action_rows += f"| {item['name']} |\n"
        if not needs_action_rows:
            needs_action_rows = "| _No items_ |\n"

        done_items = self._get_done_items()
        done_rows = ""
        for item in done_items:
            done_rows += f"| {item['name']} |\n"
        if not done_rows:
            done_rows = "| _No items_ |\n"

        plans_items = self._get_folder_items("Plans")
        plans_rows = ""
        for item in plans_items:
            plans_rows += f"| {item['name']} |\n"
        if not plans_rows:
            plans_rows = "| _No items_ |\n"

        approved_items = self._get_folder_items("Approved")
        approved_rows = ""
        for item in approved_items:
            approved_rows += f"| {item['name']} |\n"
        if not approved_rows:
            approved_rows = "| _No items_ |\n"

        pending_items = self._get_folder_items("Pending_Approval")
        pending_rows = ""
        for item in pending_items:
            pending_rows += f"| {item['name']} |\n"
        if not pending_rows:
            pending_rows = "| _No items_ |\n"

        rejected_items = self._get_folder_items("Rejected")
        rejected_rows = ""
        for item in rejected_items:
            rejected_rows += f"| {item['name']} |\n"
        if not rejected_rows:
            rejected_rows = "| _No items_ |\n"

        briefings_items = self._get_folder_items("Briefings")
        briefings_rows = ""
        for item in briefings_items:
            briefings_rows += f"| {item['name']} |\n"
        if not briefings_rows:
            briefings_rows = "| _No items_ |\n"

        accounting_items = self._get_folder_items("Accounting")
        accounting_rows = ""
        for item in accounting_items:
            accounting_rows += f"| {item['name']} |\n"
        if not accounting_rows:
            accounting_rows = "| _No items_ |\n"

        processed_items = self._get_folder_items("Processed")
        processed_rows = ""
        for item in processed_items:
            processed_rows += f"| {item['name']} |\n"
        if not processed_rows:
            processed_rows = "| _No items_ |\n"

        content = f"""---
created: 2026-01-01
last_updated: {datetime.now().isoformat()}
---

# AI Employee Dashboard

## Current Status

| Metric | Value |
|--------|-------|
| **Needs Action** | {pending_count} |
| **Pending Approval** | {approved_count} |
| **Plans** | {plans_count} |
| **Approved** | {len(approved_items)} |
| **Inbox Emails** | {len(inbox_emails)} |

## All Folders Summary

| Folder | Count |
|--------|-------|
| Needs_Action | {pending_count} |
| Pending_Approval | {approved_count} |
| Plans | {plans_count} |
| Approved | {len(approved_items)} |
| Rejected | {rejected_count} |
| Done | {done_count} |
| Processed | {processed_count} |
| Briefings | {briefings_count} |
| Accounting | {accounting_count} |

## Inbox

| Status | From | Subject |
|--------|------|---------|
{email_rows}

## Needs Action

| Item |
|------|
{needs_action_rows}

## Pending Approval

| Item |
|------|
{pending_rows}

## Plans

| Item |
|------|
{plans_rows}

## Approved

| Item |
|------|
{approved_rows}

## Rejected

| Item |
|------|
{rejected_rows}

## Done

| Item |
|------|
{done_rows}

## Processed

| Item |
|------|
{processed_rows}

## Briefings

| Item |
|------|
{briefings_rows}

## Accounting

| Item |
|------|
{accounting_rows}

## System Health

| Service | Status |
|---------|--------|
| Orchestrator | Running |
| Gmail | {len(inbox_emails)} emails |
| Unread | {unread_count} |

## Quick Commands

- **Process Tasks**: claude --cwd {self.vault_path} "Process all items in Needs_Action folder"
- **Generate Briefing**: claude --cwd {self.vault_path} "Create a weekly briefing report"
- **Check Status**: claude --cwd {self.vault_path} "Summarize current status"

---

_Generated by AI Employee v0.1_
"""
        dashboard.write_text(content)
        logger.info("Dashboard updated")

    def log_action(self, action_type: str, details: str):
        log_file = (
            self.vault_path / "Logs" / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        )
        log_entry = f'{{"timestamp": "{datetime.now().isoformat()}", "action": "{action_type}", "details": "{details}"}}\n'
        with open(log_file, "a") as f:
            f.write(log_entry)
        self._update_logs_markdown()

    def _update_logs_markdown(self):
        import json

        logs_dir = self.vault_path / "Logs"
        logs_md = self.vault_path / "Logs.md"

        all_logs = []
        for log_file in sorted(logs_dir.glob("*.json")):
            try:
                with open(log_file) as f:
                    for line in f:
                        if line.strip():
                            all_logs.append(json.loads(line))
            except:
                pass

        all_logs.sort(key=lambda x: x["timestamp"], reverse=True)

        md_content = f"""# Action Logs

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Recent Activity

| Timestamp | Action | Details |
|-----------|--------|---------|
"""

        for log in all_logs[:100]:
            ts = log["timestamp"].replace("T", " ").split(".")[0]
            action = log["action"]
            details = log["details"]
            md_content += f"| {ts} | {action} | {details} |\n"

        md_content += f"""
---

_Total entries: {len(all_logs)}_
"""

        logs_md.write_text(md_content)

    def _get_inbox_for_dashboard(self) -> List[dict]:
        inbox = self.vault_path / "Inbox"
        emails = []
        for f in inbox.glob("EMAIL_*.md"):
            content = f.read_text()
            import re

            from_match = re.search(r"from:\s*(.+)", content)
            subject_match = re.search(r"##\s*(.+)", content)
            unread_match = re.search(r"unread:\s*(True|False)", content)
            if from_match and subject_match:
                emails.append(
                    {
                        "from": from_match.group(1),
                        "subject": subject_match.group(1),
                        "unread": unread_match.group(1) == "True"
                        if unread_match
                        else False,
                    }
                )
        return emails

    def _get_needs_action_items(self) -> List[dict]:
        needs_action = self.vault_path / "Needs_Action"
        items = []
        for f in needs_action.glob("*.md"):
            items.append({"name": f.name})
        return items

    def _get_done_items(self) -> List[dict]:
        done = self.vault_path / "Done"
        items = []
        for f in done.glob("*.md"):
            items.append({"name": f.name})
        return items

    def _get_folder_items(self, folder_name: str) -> List[dict]:
        folder = self.vault_path / folder_name
        items = []
        for f in folder.glob("*.md"):
            items.append({"name": f.name})
        return items

    def run_watcher(self, name: str, command: list):
        logger.info(f"Starting watcher: {name}")
        try:
            proc = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.processes[name] = proc
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")

    def check_processes(self):
        for name, proc in list(self.processes.items()):
            if proc.poll() is not None:
                logger.warning(f"{name} stopped, restarting...")
                del self.processes[name]

    def signal_handler(self, signum, frame):
        logger.info("Shutdown signal received")
        self.running = False
        for name, proc in self.processes.items():
            proc.terminate()
        sys.exit(0)

    def run(self, check_interval: int = 60):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.setup_folders()
        self.update_dashboard()

        logger.info(f"Orchestrator running - Vault: {self.vault_path}")

        while self.running:
            try:
                pending = self.check_pending_approval()
                if pending:
                    logger.info(f"Awaiting approval: {len(pending)} items")

                needs_action = self.check_needs_action()
                if needs_action:
                    logger.info(f"Needs action: {len(needs_action)} items")

                inbox = self.vault_path / "Inbox"
                inbox_emails = list(inbox.glob("EMAIL_*.md"))
                unread_count = 0
                for f in inbox_emails:
                    content = f.read_text()
                    if "unread: True" in content:
                        unread_count += 1
                if unread_count > 0:
                    logger.info(f"Unread emails: {unread_count}")

                self.sync_inbox()
                self.process_inbox_checkboxes()
                self.update_dashboard()
                self.check_processes()

            except Exception as e:
                logger.error(f"Error in main loop: {e}")

            time.sleep(check_interval)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AI Employee Orchestrator")
    parser.add_argument("--vault", required=True, help="Path to Obsidian vault")
    parser.add_argument(
        "--interval", type=int, default=60, help="Check interval in seconds"
    )
    args = parser.parse_args()

    orchestrator = Orchestrator(args.vault)
    orchestrator.run(args.interval)


if __name__ == "__main__":
    main()
