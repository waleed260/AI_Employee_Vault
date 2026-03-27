# SKILL.md - Handle Approval Request

## Purpose
Process items in `/Pending_Approval`, execute approved actions, and handle rejections.

## Trigger
- Manual: "Review Approvals"
- Automated: When files move to `/Approved` or `/Rejected`

## Workflow

### For Approved Items

1. **Read** the approval file
2. **Verify** the action details
3. **Execute** via appropriate MCP or script
4. **Log** the action in `/Logs/`
5. **Move** to `/Done`
6. **Update** Dashboard

### For Rejected Items

1. **Log** the rejection
2. **Move** to `/Rejected`
3. **Notify** (optional: send notification)

## Action Types & Handlers

| Type | Handler | Notes |
|------|---------|-------|
| email_send | email-mcp | Verify recipient and content |
| payment | bank-mcp | Double-check amount and recipient |
| social_post | social-mcp | Review content before posting |
| delete | filesystem | Confirm file path |

## Logging Format

```json
{
  "timestamp": "{iso8601}",
  "action_type": "{type}",
  "actor": "claude_code",
  "target": "{target}",
  "parameters": {},
  "approval_status": "approved|rejected",
  "approved_by": "human",
  "result": "success|failure"
}
```

## Success Criteria
- Approved actions executed successfully
- All actions logged
- Files moved appropriately
- Failures reported immediately
