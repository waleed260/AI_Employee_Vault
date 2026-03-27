import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger("TeamService")


class Role(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    GUEST = "guest"
    VIEWER = "viewer"


class Permission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    APPROVE = "approve"
    MANAGE_USERS = "manage_users"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_FINANCES = "manage_finances"
    SEND_MESSAGES = "send_messages"
    MANAGE_TEAM = "manage_team"


ROLE_PERMISSIONS = {
    Role.ADMIN: [p for p in Permission],
    Role.MANAGER: [
        Permission.READ,
        Permission.WRITE,
        Permission.APPROVE,
        Permission.VIEW_ANALYTICS,
        Permission.SEND_MESSAGES,
        Permission.MANAGE_TEAM,
    ],
    Role.MEMBER: [Permission.READ, Permission.WRITE, Permission.SEND_MESSAGES],
    Role.VIEWER: [Permission.READ],
    Role.GUEST: [Permission.READ],
}


class TeamMember:
    def __init__(self, user_id: str, name: str, email: str, role: Role = Role.MEMBER):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.role = role
        self.created_at = datetime.now().isoformat()
        self.last_active = datetime.now().isoformat()
        self.status = "active"
        self.preferences = {}
        self.stats = {
            "tasks_completed": 0,
            "messages_sent": 0,
            "hours_active": 0,
        }

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "status": self.status,
            "preferences": self.preferences,
            "stats": self.stats,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TeamMember":
        member = cls(
            data["user_id"],
            data["name"],
            data["email"],
            Role(data.get("role", "member")),
        )
        member.created_at = data.get("created_at", datetime.now().isoformat())
        member.last_active = data.get("last_active", datetime.now().isoformat())
        member.status = data.get("status", "active")
        member.preferences = data.get("preferences", {})
        member.stats = data.get("stats", {})
        return member


class TeamService:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.team_dir = self.vault_path / "Team"
        self.team_dir.mkdir(exist_ok=True)

        self.members_file = self.team_dir / "members.json"
        self.invites_file = self.team_dir / "invites.json"
        self.activities_file = self.team_dir / "activities.json"

        self.members: Dict[str, TeamMember] = {}
        self._load_members()

        logger.info("TeamService initialized - Silver Tier")

    def _load_members(self):
        if self.members_file.exists():
            data = json.loads(self.members_file.read_text())
            self.members = {k: TeamMember.from_dict(v) for k, v in data.items()}

    def _save_members(self):
        data = {k: v.to_dict() for k, v in self.members.items()}
        self.members_file.write_text(json.dumps(data, indent=2))

    def add_member(
        self, user_id: str, name: str, email: str, role: Role = Role.MEMBER
    ) -> Dict:
        if user_id in self.members:
            return {"status": "error", "message": f"User {user_id} already exists"}

        member = TeamMember(user_id, name, email, role)
        self.members[user_id] = member
        self._save_members()

        self._log_activity(user_id, "member_added", {"name": name, "role": role.value})

        logger.info(f"Added team member: {name} ({role.value})")

        return {
            "status": "success",
            "member": member.to_dict(),
        }

    def remove_member(self, user_id: str) -> Dict:
        if user_id not in self.members:
            return {"status": "error", "message": f"User {user_id} not found"}

        member = self.members.pop(user_id)
        self._save_members()

        self._log_activity(user_id, "member_removed", {"name": member.name})

        logger.info(f"Removed team member: {member.name}")

        return {
            "status": "success",
            "removed_member": member.name,
        }

    def update_member_role(self, user_id: str, new_role: Role) -> Dict:
        if user_id not in self.members:
            return {"status": "error", "message": f"User {user_id} not found"}

        old_role = self.members[user_id].role
        self.members[user_id].role = new_role
        self._save_members()

        self._log_activity(
            user_id,
            "role_changed",
            {"old_role": old_role.value, "new_role": new_role.value},
        )

        logger.info(f"Updated role for {user_id}: {old_role.value} -> {new_role.value}")

        return {
            "status": "success",
            "old_role": old_role.value,
            "new_role": new_role.value,
        }

    def get_member(self, user_id: str) -> Optional[TeamMember]:
        return self.members.get(user_id)

    def list_members(self, role: Role = None, status: str = None) -> List[Dict]:
        members = list(self.members.values())

        if role:
            members = [m for m in members if m.role == role]
        if status:
            members = [m for m in members if m.status == status]

        return [m.to_dict() for m in members]

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        member = self.get_member(user_id)
        if not member or member.status != "active":
            return False
        return permission in ROLE_PERMISSIONS.get(member.role, [])

    def check_permission(self, user_id: str, permission: Permission) -> Dict:
        has_perm = self.has_permission(user_id, permission)
        return {
            "user_id": user_id,
            "permission": permission.value,
            "granted": has_perm,
        }

    def assign_task(self, assignee_id: str, task_data: Dict, assigned_by: str) -> Dict:
        if not self.has_permission(assigned_by, Permission.WRITE):
            return {"status": "error", "message": "Permission denied"}

        if assignee_id not in self.members:
            return {"status": "error", "message": f"Assignee {assignee_id} not found"}

        tasks_dir = self.team_dir / "Tasks"
        tasks_dir.mkdir(exist_ok=True)

        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        task = {
            "task_id": task_id,
            "title": task_data.get("title"),
            "description": task_data.get("description"),
            "assignee": assignee_id,
            "assigned_by": assigned_by,
            "status": "pending",
            "priority": task_data.get("priority", "medium"),
            "due_date": task_data.get("due_date"),
            "created_at": datetime.now().isoformat(),
        }

        task_file = tasks_dir / f"{task_id}.json"
        task_file.write_text(json.dumps(task, indent=2))

        self._log_activity(
            assignee_id, "task_assigned", {"task_id": task_id, "title": task["title"]}
        )

        logger.info(f"Task assigned: {task_id} to {assignee_id}")

        return {
            "status": "success",
            "task": task,
        }

    def get_team_tasks(self, user_id: str = None, status: str = None) -> List[Dict]:
        tasks_dir = self.team_dir / "Tasks"
        if not tasks_dir.exists():
            return []

        tasks = []
        for task_file in tasks_dir.glob("*.json"):
            task = json.loads(task_file.read_text())

            if user_id and task.get("assignee") != user_id:
                continue
            if status and task.get("status") != status:
                continue

            tasks.append(task)

        return tasks

    def update_task_status(self, task_id: str, status: str, user_id: str) -> Dict:
        tasks_dir = self.team_dir / "Tasks"
        task_file = tasks_dir / f"{task_id}.json"

        if not task_file.exists():
            return {"status": "error", "message": f"Task {task_id} not found"}

        task = json.loads(task_file.read_text())
        task["status"] = status
        task["updated_at"] = datetime.now().isoformat()
        task["updated_by"] = user_id

        task_file.write_text(json.dumps(task, indent=2))

        self._log_activity(
            user_id, "task_updated", {"task_id": task_id, "new_status": status}
        )

        return {
            "status": "success",
            "task": task,
        }

    def invite_user(
        self, email: str, invited_by: str, role: Role = Role.MEMBER
    ) -> Dict:
        if not self.has_permission(invited_by, Permission.MANAGE_USERS):
            return {"status": "error", "message": "Permission denied"}

        invites = {}
        if self.invites_file.exists():
            invites = json.loads(self.invites_file.read_text())

        invite_id = f"invite_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        invites[email] = {
            "invite_id": invite_id,
            "email": email,
            "role": role.value,
            "invited_by": invited_by,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "expires_at": datetime.now().isoformat(),
        }

        self.invites_file.write_text(json.dumps(invites, indent=2))

        logger.info(f"Invited user: {email} with role {role.value}")

        return {
            "status": "success",
            "invite": invites[email],
        }

    def accept_invite(self, email: str, user_id: str, name: str) -> Dict:
        invites = {}
        if self.invites_file.exists():
            invites = json.loads(self.invites_file.read_text())

        if email not in invites:
            return {"status": "error", "message": "No pending invite for this email"}

        invite = invites[email]
        role = Role(invite["role"])

        self.add_member(user_id, name, email, role)

        del invites[email]
        self.invites_file.write_text(json.dumps(invites, indent=2))

        return {
            "status": "success",
            "message": f"Welcome {name}! You've joined the team as {role.value}",
        }

    def get_team_analytics(self) -> Dict:
        total_members = len(self.members)
        active_members = len([m for m in self.members.values() if m.status == "active"])

        role_distribution = {}
        for role in Role:
            count = len([m for m in self.members.values() if m.role == role])
            role_distribution[role.value] = count

        tasks = self.get_team_tasks()
        task_stats = {
            "total": len(tasks),
            "pending": len([t for t in tasks if t.get("status") == "pending"]),
            "completed": len([t for t in tasks if t.get("status") == "completed"]),
            "in_progress": len([t for t in tasks if t.get("status") == "in_progress"]),
        }

        return {
            "total_members": total_members,
            "active_members": active_members,
            "role_distribution": role_distribution,
            "tasks": task_stats,
        }

    def _log_activity(self, user_id: str, activity_type: str, details: Dict):
        activities = []
        if self.activities_file.exists():
            activities = json.loads(self.activities_file.read_text())

        activities.append(
            {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "activity_type": activity_type,
                "details": details,
            }
        )

        if len(activities) > 1000:
            activities = activities[-1000:]

        self.activities_file.write_text(json.dumps(activities, indent=2))

    def get_recent_activities(self, limit: int = 50) -> List[Dict]:
        if not self.activities_file.exists():
            return []

        activities = json.loads(self.activities_file.read_text())
        return activities[-limit:]
