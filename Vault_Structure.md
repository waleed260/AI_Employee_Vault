# Vault Folder Structure

## Purpose

This Obsidian vault serves as the brain and memory of your AI Employee.

## Folder Descriptions

### Core Folders

| Folder | Purpose |
|--------|---------|
| `/Inbox` | Unprocessed items from any source |
| `/Needs_Action` | Items requiring AI attention or human approval |
| `/Done` | Completed items (audit trail) |
| `/Plans` | AI-generated plans and strategies |
| `/Approved` | Items approved by human for execution |
| `/Rejected` | Items rejected by human |
| `/Pending_Approval` | Items awaiting human decision |

### Business Folders

| Folder | Purpose |
|--------|---------|
| `/Accounting` | Financial records and transactions |
| `/Briefings` | AI-generated reports and briefings |
| `/Logs` | Action logs and audit trails |
| `/Drops` | Files dropped for processing |

## Workflow

1. **Watcher detects item** → Creates file in `/Needs_Action`
2. **AI reads item** → Creates plan in `/Plans`
3. **If approval needed** → Moves to `/Pending_Approval`
4. **Human approves** → Moves to `/Approved`
5. **AI executes action** → Logs to `/Logs`
6. **Task complete** → Moves to `/Done`

## File Naming Convention

- Emails: `EMAIL_{id}_{date}.md`
- WhatsApp: `WHATSAPP_{sender}_{date}.md`
- Files: `FILE_{original_name}.md`
- Payments: `PAYMENT_{recipient}_{date}.md`
- Plans: `PLAN_{topic}_{date}.md`

---

_Last updated: 2026-01-01_
