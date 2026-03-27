# SKILL.md - Team Collaboration

## Purpose
Manage team members, assignments, permissions, and collaboration.

## Trigger
- Manual: "Add team member", "Assign task"
- Automated: Task assignments, notifications

## Workflow

### 1. Team Management
- Add/remove members
- Assign roles (Admin, Manager, Member, Viewer, Guest)
- Manage invitations

### 2. Task Assignment
- Create tasks for team members
- Set priorities and deadlines
- Track progress
- Update status

### 3. Permissions
- Role-based access control
- Grant/revoke permissions
- Audit access

### 4. Analytics
- Team performance
- Task completion rates
- Activity logs

## Roles & Permissions

| Role | Read | Write | Approve | Manage Team | Analytics |
|------|------|-------|---------|-------------|-----------|
| Admin | ✓ | ✓ | ✓ | ✓ | ✓ |
| Manager | ✓ | ✓ | ✓ | ✗ | ✓ |
| Member | ✓ | ✓ | ✗ | ✗ | ✗ |
| Viewer | ✓ | ✗ | ✗ | ✗ | ✗ |
| Guest | ✓ | ✗ | ✗ | ✗ | ✗ |

## Commands

```
# Team management
Add team member: {name}, {email}, {role}
Remove team member: {email}
Update role: {email} to {role}
List team members

# Task management
Create task: {title}, {assignee}, {priority}
List tasks
Update task: {task_id} to {status}
Complete task: {task_id}

# Permissions
Check permission: {user} for {action}
Grant permission: {user} to {action}

# Invitations
Invite user: {email} as {role}
List pending invitations
```

## Task Properties

- **Title** - Task name
- **Description** - Details
- **Assignee** - Team member
- **Priority** - High, Medium, Low
- **Due Date** - Deadline
- **Status** - Pending, In Progress, Completed

## Team Directory

Team data stored in:
- `/Team/members.json`
- `/Team/invites.json`
- `/Team/Tasks/`
- `/Team/activities.json`

## Approval Workflow

Team tasks follow:
1. Create task → `/Needs_Action`
2. Review → Approve/Reject
3. Assign → Team member
4. Complete → `/Done`

## Success Criteria
- Team members added correctly
- Tasks assigned and tracked
- Permissions enforced
- Analytics available
