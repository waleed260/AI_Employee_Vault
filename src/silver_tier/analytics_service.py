import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger("AnalyticsService")


class AnalyticsService:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.analytics_dir = self.vault_path / "Analytics"
        self.analytics_dir.mkdir(exist_ok=True)

        self.metrics_file = self.analytics_dir / "metrics.json"
        self.reports_file = self.analytics_dir / "reports.json"

        self.metrics: Dict = self._load_metrics()

        logger.info("AnalyticsService initialized - Silver Tier")

    def _load_metrics(self) -> Dict:
        if self.metrics_file.exists():
            return json.loads(self.metrics_file.read_text())
        return {
            "daily": defaultdict(list),
            "weekly": defaultdict(list),
            "monthly": defaultdict(list),
        }

    def _save_metrics(self):
        self.metrics_file.write_text(json.dumps(dict(self.metrics), indent=2))

    def track_event(self, event_type: str, details: Dict):
        timestamp = datetime.now()
        date_key = timestamp.strftime("%Y-%m-%d")

        self.metrics["daily"][date_key].append(
            {
                "timestamp": timestamp.isoformat(),
                "event_type": event_type,
                "details": details,
            }
        )

        self._save_metrics()
        logger.info(f"Tracked event: {event_type}")

    def get_daily_summary(self, date: str = None) -> Dict:
        date = date or datetime.now().strftime("%Y-%m-%d")
        events = self.metrics["daily"].get(date, [])

        event_counts = defaultdict(int)
        for event in events:
            event_counts[event["event_type"]] += 1

        return {
            "date": date,
            "total_events": len(events),
            "event_breakdown": dict(event_counts),
            "events": events,
        }

    def get_weekly_summary(self) -> Dict:
        today = datetime.now()
        week_ago = today - timedelta(days=7)

        weekly_events = []
        for i in range(7):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            events = self.metrics["daily"].get(date, [])
            weekly_events.extend(events)

        event_counts = defaultdict(int)
        for event in weekly_events:
            event_counts[event["event_type"]] += 1

        return {
            "start_date": week_ago.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "total_events": len(weekly_events),
            "event_breakdown": dict(event_counts),
            "daily_average": len(weekly_events) / 7,
        }

    def get_monthly_summary(self, year: int = None, month: int = None) -> Dict:
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        monthly_events = []
        for date_key, events in self.metrics["daily"].items():
            try:
                event_date = datetime.strptime(date_key, "%Y-%m-%d")
                if event_date.year == year and event_date.month == month:
                    monthly_events.extend(events)
            except:
                pass

        event_counts = defaultdict(int)
        for event in monthly_events:
            event_counts[event["event_type"]] += 1

        return {
            "year": year,
            "month": month,
            "total_events": len(monthly_events),
            "event_breakdown": dict(event_counts),
            "daily_average": len(monthly_events) / 30,
        }

    def get_workflow_analytics(self) -> Dict:
        folders = [
            "Inbox",
            "Needs_Action",
            "Pending_Approval",
            "Done",
            "Plans",
            "Approved",
        ]
        folder_stats = {}

        for folder in folders:
            folder_path = self.vault_path / folder
            if folder_path.exists():
                items = list(folder_path.glob("*.md"))
                folder_stats[folder] = {
                    "count": len(items),
                    "percentage": 0,
                }

        total = sum(f["count"] for f in folder_stats.values())
        if total > 0:
            for folder in folder_stats:
                folder_stats[folder]["percentage"] = round(
                    folder_stats[folder]["count"] / total * 100, 1
                )

        return {
            "total_items": total,
            "folder_distribution": folder_stats,
            "timestamp": datetime.now().isoformat(),
        }

    def get_email_analytics(self) -> Dict:
        inbox = self.vault_path / "Inbox"
        if not inbox.exists():
            return {"total": 0, "unread": 0}

        emails = list(inbox.glob("EMAIL_*.md"))
        unread = 0
        from_counts = defaultdict(int)

        for email in emails:
            content = email.read_text()
            if "unread: True" in content:
                unread += 1

            import re

            from_match = re.search(r"from:\s*(.+)", content)
            if from_match:
                from_counts[from_match.group(1).strip()] += 1

        top_senders = sorted(from_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_emails": len(emails),
            "unread_emails": unread,
            "read_emails": len(emails) - unread,
            "read_percentage": round((len(emails) - unread) / len(emails) * 100, 1)
            if emails
            else 0,
            "top_senders": [{"email": e[0], "count": e[1]} for e in top_senders],
        }

    def get_task_completion_analytics(self) -> Dict:
        needs_action = self.vault_path / "Needs_Action"
        done = self.vault_path / "Done"

        needs_count = (
            len(list(needs_action.glob("*.md"))) if needs_action.exists() else 0
        )
        done_count = len(list(done.glob("*.md"))) if done.exists() else 0

        total = needs_count + done_count
        completion_rate = round(done_count / total * 100, 1) if total > 0 else 0

        return {
            "pending_tasks": needs_count,
            "completed_tasks": done_count,
            "total_tasks": total,
            "completion_rate": completion_rate,
            "pending_percentage": 100 - completion_rate,
        }

    def get_performance_metrics(self) -> Dict:
        logs_dir = self.vault_path / "Logs"
        if not logs_dir.exists():
            return {"total_actions": 0}

        total_actions = 0
        action_types = defaultdict(int)

        for log_file in logs_dir.glob("*.json"):
            try:
                content = log_file.read_text()
                for line in content.strip().split("\n"):
                    if line.strip():
                        entry = json.loads(line)
                        total_actions += 1
                        action_types[entry.get("action", "unknown")] += 1
            except:
                pass

        return {
            "total_actions": total_actions,
            "action_breakdown": dict(action_types),
            "timestamp": datetime.now().isoformat(),
        }

    def generate_report(self, report_type: str = "weekly") -> Dict:
        report_id = f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if report_type == "daily":
            summary = self.get_daily_summary()
        elif report_type == "weekly":
            summary = self.get_weekly_summary()
        elif report_type == "monthly":
            summary = self.get_monthly_summary()
        else:
            summary = {}

        workflow = self.get_workflow_analytics()
        email = self.get_email_analytics()
        tasks = self.get_task_completion_analytics()
        performance = self.get_performance_metrics()

        report = {
            "report_id": report_id,
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "workflow": workflow,
            "email": email,
            "tasks": tasks,
            "performance": performance,
        }

        reports = []
        if self.reports_file.exists():
            reports = json.loads(self.reports_file.read_text())

        reports.append(report)
        self.reports_file.write_text(json.dumps(reports, indent=2))

        logger.info(f"Generated {report_type} report: {report_id}")

        return report

    def get_dashboard_data(self) -> Dict:
        return {
            "workflow": self.get_workflow_analytics(),
            "email": self.get_email_analytics(),
            "tasks": self.get_task_completion_analytics(),
            "performance": self.get_performance_metrics(),
            "last_updated": datetime.now().isoformat(),
        }

    def clear_old_data(self, days: int = 90):
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        removed_count = 0
        for date_key in list(self.metrics["daily"].keys()):
            if date_key < cutoff_str:
                removed_count += len(self.metrics["daily"].pop(date_key, []))

        self._save_metrics()

        logger.info(f"Cleared {removed_count} old metric entries")

        return {
            "status": "success",
            "removed_entries": removed_count,
            "cutoff_date": cutoff_str,
        }
