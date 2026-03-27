# AI Employee Vault

A personal AI assistant that manages your emails, tasks, and business operations automatically.

## What It Does

- **Reads your emails** from Gmail and processes them automatically
- **Monitors WhatsApp** for messages and leads
- **Posts to LinkedIn** for business growth
- **Creates plans** for tasks using AI reasoning
- **Handles approvals** for sensitive actions (payments, new contacts)
- **Generates reports** - daily and weekly briefings
- **Runs on schedule** - automated workflows via cron

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the main system
python src/orchestrator.py --vault ./vault_data

# 3. Use with Claude Code
claude --cwd ~/Documents/AI_Employee_Vault "Process my inbox"
```

## Project Structure

```
AI_Employee_Vault/
├── vault_data/              # Your data lives here
│   ├── Inbox/              # New emails & messages
│   ├── Needs_Action/       # Items to process
│   ├── Pending_Approval/   # Waiting for your approval
│   ├── Done/               # Completed items
│   ├── Plans/              # AI-generated plans
│   ├── Approved/           # Approved actions
│   ├── LinkedIn/          # LinkedIn posts & analytics
│   ├── WhatsApp/           # WhatsApp messages
│   ├── Analytics/          # Business metrics
│   └── Dashboard.md        # Your command center
├── src/
│   ├── orchestrator.py     # Main brain
│   ├── gmail_service.py   # Gmail connection
│   ├── silver_tier/       # Advanced features
│   │   ├── linkedin_service.py
│   │   ├── mcp_server.py
│   │   ├── whatsapp_watcher.py
│   │   ├── analytics_service.py
│   │   └── ...
│   └── watchers/           # Monitoring scripts
├── skills/                 # AI capabilities (Agent Skills)
└── Drops/                  # Drop files here for processing
```

## Tiers

### Bronze (Basic)
- Gmail watcher
- File drop watcher
- Human-in-loop approval
- Basic dashboard

### Silver (This Version)
Everything in Bronze, plus:
- **WhatsApp integration** - Handle messages automatically
- **LinkedIn automation** - Post updates, track engagement
- **MCP Server** - External API connections
- **Analytics** - Business intelligence dashboards
- **Scheduling** - Cron-based automation
- **Team collaboration** - Multi-user support
- **Claude reasoning** - Smart plan generation

## How It Works

```
1. Email/Message arrives → Saved to Inbox
2. You check checkbox → Item moves to correct folder
3. AI analyzes → Creates a plan
4. If sensitive → Asks for your approval
5. After approval → Executes action
6. Logs result → Updates dashboard
```

## Commands

```bash
# Process pending items
"Process all items in Needs_Action"

# Generate weekly report
"Create a Monday morning briefing"

# Check status
"Show me the dashboard"

# Post to LinkedIn
"Post to LinkedIn about our new product"

# Send WhatsApp
"Send WhatsApp to +1234567890: Thanks for reaching out!"
```

## Setting Up Services

### Gmail API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project → Enable Gmail API
3. Create OAuth credentials → Download as `credentials.json`

### WhatsApp API
1. Get WhatsApp Business API credentials
2. Edit `vault_data/WhatsApp/config.json`

### LinkedIn
1. Create LinkedIn Developer app
2. Get access token
3. Edit `vault_data/LinkedIn/config.json`

## Running on Schedule

```bash
# Add to crontab
crontab -e

# Run every hour
0 * * * * cd ~/Documents/AI_Employee_Vault && python src/orchestrator.py --vault ./vault_data --interval 3600
```

## Security

- **Local data** - Everything stays on your machine
- **Human approval** - You control sensitive actions
- **Audit logs** - Every action recorded in `/Logs/`
- **No secrets in git** - Uses `.gitignore`

## Files Created by AI

| Folder | What Goes Here |
|--------|----------------|
| `Inbox` | New emails, messages |
| `Needs_Action` | Items you need to handle |
| `Pending_Approval` | Waiting for your OK |
| `Done` | Completed items |
| `Plans` | AI-generated action plans |
| `Briefings` | Weekly/monthly reports |

## Need Help?

- Check `vault_data/Dashboard.md` for current status
- Read `CLAUDE.md` for technical details
- Review `skills/` folder for all AI capabilities
