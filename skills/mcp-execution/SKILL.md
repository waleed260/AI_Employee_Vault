# SKILL.md - MCP Tool Execution

## Purpose
Execute external actions through the Model Context Protocol (MCP) server.

## Trigger
- Manual: "Run tool", "Execute MCP"
- Automated: Workflows requiring external actions

## Available Tools

### File Operations
- `create_file` - Create a new file
- `read_file` - Read file contents
- `list_files` - List directory contents
- `delete_file` - Delete a file
- `move_file` - Move file to another location
- `search_content` - Search for text in files

### Communication
- `send_email` - Send an email
- `send_whatsapp` - Send a WhatsApp message

### Task Management
- `create_task` - Create a new task
- `get_tasks` - List all tasks
- `update_task` - Update task status

### Workflow
- `run_automation` - Trigger an automation
- `get_dashboard` - Get vault status
- `get_approval_items` - List items pending approval
- `approve_item` - Approve an item
- `reject_item` - Reject an item

### Logging
- `log_action` - Log an action to vault

## Commands

```
# Execute a tool
Run MCP tool: {tool_name} with {parameters}

# Example
Run MCP tool: send_email with to="client@example.com", subject="Hello"

# Get tool list
List MCP tools

# Check MCP status
MCP status
```

## Parameters Format

Pass parameters as JSON or key=value pairs:
```
tool: send_email
parameters:
  to: "user@example.com"
  subject: "Meeting"
  body: "Let's meet tomorrow"
```

## MCP Server

The MCP server runs on port 8080 and exposes:
- REST endpoints for each tool
- WebSocket connections for real-time updates
- Resource endpoints for vault data
- Prompt templates for common tasks

## Example Workflows

### 1. Create and Send Report
```
1. Run MCP tool: read_file with path="Accounting/Records.md"
2. Run MCP tool: create_file with path="Briefings/report.md", content="{data}"
3. Run MCP tool: send_email with to="boss@company.com", subject="Weekly Report"
```

### 2. Process New Lead
```
1. Run MCP tool: create_task with title="Follow up with {lead}", priority="high"
2. Run MCP tool: send_whatsapp with to="{lead_number}", message="Thanks for reaching out!"
```

### 3. Approval Flow
```
1. Run MCP tool: get_approval_items
2. For each item, review content
3. Run MCP tool: approve_item with item_id="{item}"
```

## Error Handling

- Tool not found → Return available tools list
- Permission denied → Request human approval
- Network error → Retry with exponential backoff
- Invalid parameters → Show parameter requirements

## Success Criteria
- Tools executed successfully
- Results logged appropriately
- Errors handled gracefully
- Vault state updated correctly
