import os
import json
import logging
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import threading

logger = logging.getLogger("AutomationScheduler")


class TaskFrequency(Enum):
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AutomationScheduler:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.scheduler_dir = self.vault_path / "Automation"
        self.scheduler_dir.mkdir(exist_ok=True)

        self.tasks_file = self.scheduler_dir / "scheduled_tasks.json"
        self.history_file = self.scheduler_dir / "execution_history.json"

        self.tasks: List[Dict] = self._load_tasks()
        self.history: List[Dict] = self._load_history()

        self.running = False
        self.check_interval = 60

        self._register_default_tasks()

        logger.info("AutomationScheduler initialized - Silver Tier")

    def _load_tasks(self) -> List:
        if self.tasks_file.exists():
            return json.loads(self.tasks_file.read_text())
        return []

    def _save_tasks(self):
        self.tasks_file.write_text(json.dumps(self.tasks, indent=2))

    def _load_history(self) -> List:
        if self.history_file.exists():
            return json.loads(self.history_file.read_text())
        return []

    def _save_history(self):
        self.history_file.write_text(json.dumps(self.history, indent=2))

    def _register_default_tasks(self):
        default_tasks = [
            {
                "name": "Sync Inbox",
                "command": "sync_inbox",
                "frequency": "hourly",
                "enabled": True,
                "description": "Sync emails from Gmail",
            },
            {
                "name": "Update Dashboard",
                "command": "update_dashboard",
                "frequency": "hourly",
                "enabled": True,
                "description": "Update vault dashboard",
            },
            {
                "name": "Process Checkboxes",
                "command": "process_checkboxes",
                "frequency": "minutely",
                "enabled": True,
                "description": "Process workflow checkboxes",
            },
            {
                "name": "Weekly Briefing",
                "command": "generate_briefing",
                "frequency": "weekly",
                "enabled": False,
                "description": "Generate Monday CEO briefing",
            },
            {
                "name": "LinkedIn Sync",
                "command": "linkedin_sync",
                "frequency": "daily",
                "enabled": False,
                "description": "Sync LinkedIn notifications",
            },
            {
                "name": "WhatsApp Sync",
                "command": "whatsapp_sync",
                "frequency": "hourly",
                "enabled": False,
                "description": "Sync WhatsApp messages",
            },
            {
                "name": "Clean Old Logs",
                "command": "clean_logs",
                "frequency": "monthly",
                "enabled": True,
                "description": "Clean logs older than 90 days",
            },
        ]

        for task in default_tasks:
            if not any(t.get("name") == task["name"] for t in self.tasks):
                self.tasks.append(task)

        self._save_tasks()

    def add_task(
        self,
        name: str,
        command: str,
        frequency: str,
        enabled: bool = True,
        description: str = "",
        custom_time: str = None,
        params: Dict = None,
    ) -> Dict:
        task = {
            "id": f"task_{len(self.tasks) + 1}",
            "name": name,
            "command": command,
            "frequency": frequency,
            "enabled": enabled,
            "description": description,
            "custom_time": custom_time,
            "params": params or {},
            "last_run": None,
            "next_run": self._calculate_next_run(frequency, custom_time),
            "created_at": datetime.now().isoformat(),
        }

        self.tasks.append(task)
        self._save_tasks()

        logger.info(f"Added scheduled task: {name}")

        return {
            "status": "success",
            "task": task,
        }

    def remove_task(self, task_id: str) -> Dict:
        self.tasks = [t for t in self.tasks if t.get("id") != task_id]
        self._save_tasks()

        return {
            "status": "success",
            "message": f"Task {task_id} removed",
        }

    def enable_task(self, task_id: str) -> Dict:
        for task in self.tasks:
            if task.get("id") == task_id:
                task["enabled"] = True
                self._save_tasks()
                return {"status": "success", "message": f"Task {task_id} enabled"}

        return {"status": "error", "message": "Task not found"}

    def disable_task(self, task_id: str) -> Dict:
        for task in self.tasks:
            if task.get("id") == task_id:
                task["enabled"] = False
                self._save_tasks()
                return {"status": "success", "message": f"Task {task_id} disabled"}

        return {"status": "error", "message": "Task not found"}

    def get_tasks(self, enabled_only: bool = False) -> List[Dict]:
        if enabled_only:
            return [t for t in self.tasks if t.get("enabled")]
        return self.tasks

    def get_due_tasks(self) -> List[Dict]:
        now = datetime.now()
        due = []

        for task in self.tasks:
            if not task.get("enabled"):
                continue

            next_run_str = task.get("next_run")
            if not next_run_str:
                continue

            try:
                next_run = datetime.fromisoformat(next_run_str)
                if now >= next_run:
                    due.append(task)
            except:
                pass

        return due

    def run_task(self, task_id: str, executor: Callable = None) -> Dict:
        task = None
        for t in self.tasks:
            if t.get("id") == task_id:
                task = t
                break

        if not task:
            return {"status": "error", "message": "Task not found"}

        logger.info(f"Executing task: {task['name']}")

        result = {
            "task_id": task_id,
            "task_name": task["name"],
            "command": task["command"],
            "executed_at": datetime.now().isoformat(),
            "status": "running",
        }

        try:
            if executor:
                output = executor(task)
                result["output"] = output
            else:
                result["output"] = f"Command: {task['command']} - No executor provided"

            result["status"] = "success"

            task["last_run"] = datetime.now().isoformat()
            task["next_run"] = self._calculate_next_run(
                task["frequency"], task.get("custom_time")
            )
            self._save_tasks()

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"Task {task_id} failed: {e}")

        self.history.append(result)
        if len(self.history) > 100:
            self.history = self.history[-100:]
        self._save_history()

        return result

    def _calculate_next_run(self, frequency: str, custom_time: str = None) -> str:
        now = datetime.now()

        if frequency == "minutely":
            next_time = now + timedelta(minutes=1)
        elif frequency == "hourly":
            next_time = now + timedelta(hours=1)
            if custom_time:
                hour = int(custom_time.split(":")[0])
                next_time = now.replace(hour=hour, minute=0, second=0)
                if next_time <= now:
                    next_time += timedelta(hours=1)
        elif frequency == "daily":
            if custom_time:
                hour, minute = map(int, custom_time.split(":"))
                next_time = now.replace(hour=hour, minute=minute, second=0)
                if next_time <= now:
                    next_time += timedelta(days=1)
            else:
                next_time = now + timedelta(days=1)
        elif frequency == "weekly":
            days_ahead = (7 - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            next_time = now + timedelta(days=days_ahead)
            if custom_time:
                hour, minute = map(int, custom_time.split(":"))
                next_time = next_time.replace(hour=hour, minute=minute)
        elif frequency == "monthly":
            if now.month == 12:
                next_time = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_time = now.replace(month=now.month + 1, day=1)
            if custom_time:
                day = int(custom_time.split(":")[0])
                next_time = next_time.replace(day=min(day, 28))
        else:
            next_time = now + timedelta(days=1)

        return next_time.isoformat()

    def execute_due_tasks(self, executor: Callable = None):
        due_tasks = self.get_due_tasks()

        for task in due_tasks:
            self.run_task(task["id"], executor)

        return {
            "status": "success",
            "tasks_executed": len(due_tasks),
            "tasks": [t["name"] for t in due_tasks],
        }

    def get_history(self, limit: int = 50) -> List[Dict]:
        return self.history[-limit:]

    def get_task_status(self) -> Dict:
        enabled = len([t for t in self.tasks if t.get("enabled")])
        disabled = len(self.tasks) - enabled
        due_now = len(self.get_due_tasks())

        return {
            "total_tasks": len(self.tasks),
            "enabled": enabled,
            "disabled": disabled,
            "due_now": due_now,
            "last_check": datetime.now().isoformat(),
        }

    def start(self, executor: Callable = None):
        self.running = True

        def run_scheduler():
            while self.running:
                try:
                    self.execute_due_tasks(executor)
                except Exception as e:
                    logger.warning(f"Scheduler error: {e}")
                time.sleep(self.check_interval)

        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()

        logger.info("Automation scheduler started")

        return {"status": "success", "scheduler": "running"}

    def stop(self):
        self.running = False
        logger.info("Automation scheduler stopped")

        return {"status": "success", "scheduler": "stopped"}

    def generate_cron_config(self) -> str:
        cron_entries = []

        for task in self.tasks:
            if not task.get("enabled"):
                continue

            frequency = task.get("frequency", "daily")
            command = task.get("command", "")

            if frequency == "minutely":
                schedule = "* * * * *"
            elif frequency == "hourly":
                schedule = "0 * * * *"
            elif frequency == "daily":
                schedule = "0 0 * * *"
            elif frequency == "weekly":
                schedule = "0 0 * * 1"
            elif frequency == "monthly":
                schedule = "0 0 1 * *"
            else:
                schedule = "0 0 * * *"

            cron_entries.append(
                f"{schedule} # {task['name']}: {task.get('description', '')}"
            )

        return "\n".join(cron_entries)

    def install_cron(self, python_path: str = None) -> Dict:
        cron_config = self.generate_cron_config()

        script_content = f"""#!/bin/bash
# AI Employee Vault Automation
# Add to crontab: crontab -e

{python_path or "python3"} -m src.orchestrator --vault /home/waleed/Documents/AI_Employee_Vault/vault_data --interval 60
"""

        script_path = self.scheduler_dir / "run_automation.sh"
        script_path.write_text(script_content)

        logger.info("Generated automation script")

        return {
            "status": "success",
            "cron_config": cron_config,
            "script_path": str(script_path),
            "message": "Add the cron config to crontab",
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Automation Scheduler for AI Employee")
    parser.add_argument("--vault", required=True, help="Path to vault")
    parser.add_argument("--task", help="Run specific task")
    parser.add_argument("--list", action="store_true", help="List tasks")
    args = parser.parse_args()

    scheduler = AutomationScheduler(args.vault)

    if args.list:
        print("Scheduled Tasks:")
        for task in scheduler.get_tasks():
            print(
                f"  [{'X' if task.get('enabled') else ' '}] {task['name']} ({task['frequency']})"
            )
    elif args.task:
        scheduler.run_task(args.task)
    else:
        print(f"Scheduler status: {scheduler.get_task_status()}")
        scheduler.start()


if __name__ == "__main__":
    main()
