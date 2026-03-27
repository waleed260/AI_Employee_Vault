# SKILL.md - Process Needs Action

## Purpose
Process all items in the `/Needs_Action` folder, create plans, and move items through the workflow.

## Trigger
- Manual: "Process Needs Action"
- Automated: When new files appear in `/Needs_Action`

## Workflow

1. **Read** all files in `/Needs_Action`
2. **Categorize** each item by type (email, file, payment, etc.)
3. **Create** a plan in `/Plans/PLAN_{item}_{timestamp}.md`
4. **Execute** non-sensitive actions automatically
5. **Request approval** for sensitive actions by moving to `/Pending_Approval`
6. **Move** completed items to `/Done`
7. **Update** Dashboard.md

## Approval Requirements

Always request approval for:
- Payments over $50
- New recipients
- Replies to new contacts
- Bulk actions
- Deleting files

## Example Plan Structure

```markdown
---
type: plan
item: EMAIL_{id}
created: {timestamp}
status: in_progress
---

## Objective
{clear description}

## Steps
- [ ] Step 1
- [ ] Step 2

## Approval Required
{yes/no} - {reason if yes}
```

## Success Criteria
- All items processed
- Plans created for complex tasks
- Approval requests filed for sensitive actions
- Items moved to `/Done` or `/Pending_Approval`
- Dashboard updated
