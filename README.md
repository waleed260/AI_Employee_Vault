# AI Employee Vault

> A personal AI assistant that autonomously manages emails, tasks, social media, accounting, and business operations — transforming from a functional assistant into a **Gold Tier Autonomous Employee**.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tiers](https://img.shields.io/badge/Tiers-Bronze%20%7C%20Silver%20%7C%20Gold-orange.svg)](#tiers)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Tier System](#tier-system)
- [Service Integrations](#service-integrations)
- [Commands & Workflows](#commands--workflows)
- [Security & Safety](#security--safety)
- [Configuration](#configuration)
- [Running on Schedule](#running-on-schedule)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

AI Employee Vault is a **self-hosted, file-based AI assistant** built around Claude Code and an Obsidian-like vault system. It monitors multiple communication channels (Gmail, WhatsApp, LinkedIn), autonomously reasons about tasks using the **Ralph Wiggum Loop**, manages finances via **Odoo accounting**, posts to social media platforms (LinkedIn, Facebook, Instagram, Twitter/X), and generates comprehensive CEO briefings — all while keeping data **local and private**.

### Design Philosophy

- **Local-first**: All data lives on your machine
- **Human-in-the-loop**: Sensitive actions require explicit approval
- **Graceful degradation**: System continues during partial outages
- **Audit-everything**: Every action logged with multi-level categorization

---

## Key Features

### Communication Management
- **Gmail integration** — Auto-syncs emails, categorizes by urgency, drafts responses
- **WhatsApp monitoring** — Handles customer inquiries, lead tracking, automated replies
- **Multi-channel inbox** — Unified view of all incoming messages

### Social Media Automation
- **LinkedIn** — Post updates, track engagement, auto-generate posts from templates
- **Facebook & Instagram** — Visual content posting, scheduling, analytics via Graph API
- **Twitter/X** — Real-time engagement, scheduled tweets, media attachments

### Business Operations
- **Odoo Accounting** — Self-hosted financial management via JSON-RPC (invoices, expenses, P&L reports)
- **Analytics Dashboard** — Real-time business metrics, workflow distribution, performance tracking
- **Weekly CEO Briefings** — Comprehensive Friday reports with revenue, social performance, and AI-generated recommendations

### Autonomous Reasoning
- **Ralph Wiggum Loop** — Multi-step reasoning engine that breaks complex tasks into sub-tasks, self-corrects on failure, and escalates to human when needed
- **Plan Generation** — Creates detailed markdown plans with reasoning, execution steps, risk assessments, and audit trails

### Team & Security
- **Role-based access** — Admin, Manager, Member, Guest, Viewer with 10 permission types
- **Enhanced audit logging** — Buffered, categorized, multi-level logging with error recovery and backup file writing
- **Approval workflows** — Smart routing of sensitive actions (payments >$50, new contacts, legal matters)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLAUDE (Main Agent)                   │
│  Reasoning Loop, Task Planning, Decision Making          │
└─────────────────────────────────────────────────────────┘
                            ↓
    ┌───────────────────────┼───────────────────────┬───────────────────────┐
    ↓                       ↓                       ↓                       ↓
┌─────────────┐      ┌──────────────┐      ┌───────────────┐      ┌──────────────┐
│  MCP Server │      │  MCP Server  │      │  MCP Server   │      │  MCP Server  │
│  (Core)     │      │  (Social)    │      │  (Odoo)       │      │  (Email)   │
│  :8080      │      │  :8081       │      │               │      │            │
└─────────────┘      └──────────────┘      └───────────────┘      └──────────────┘
    ↓                       ↓                       ↓                       ↓
┌─────────────┐      ┌──────────────┐      ┌───────────────┐      ┌──────────────┐
│Gmail/SMTP   │      │FB/IG/Twitter │      │Odoo Instance  │      │IMAP/SMTP   │
│WhatsApp API │      │(Social APIs) │      │(Accounting)   │      │(Calendar)  │
└─────────────┘      └──────────────┘      └───────────────┘      └──────────────┘
    ↓                       ↓                       ↓                       ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    Obsidian Vault (Central Knowledge Base)                │
│  Dashboard.md, Plan.md, Audit Logs, Briefings, Templates, Configs         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Gmail API credentials (OAuth2)
- Claude Code access

### Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd AI_Employee_Vault

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the main system (orchestrator)
python src/orchestrator.py --vault ./vault_data

# 5. Start MCP servers (in separate terminals)
python src/silver_tier/mcp_server_fixed.py --vault ./vault_data --port 8080
python src/gold_tier/mcp_server_social.py --vault ./vault_data --port 8081

# 6. Use with Claude Code
claude --cwd ~/Documents/AI_Employee_Vault "Process my inbox"
```

---

## Project Structure

```
AI_Employee_Vault/
├── vault_data/                    # Your data lives here
│   ├── Inbox/                     # New emails & messages (read-only sync)
│   ├── Needs_Action/              # Items requiring your attention
│   ├── Pending_Approval/          # Awaiting human approval
│   ├── Approved/                  # Human-approved actions
│   ├── Rejected/                  # Rejected items
│   ├── Done/                      # Completed items
│   ├── Processed/                 # Processed items
│   ├── Plans/                     # AI-generated action plans
│   ├── Briefings/                 # CEO briefings and reports
│   ├── Accounting/                # Financial records (invoices, expenses)
│   ├── Analytics/                 # Business metrics and reports
│   ├── Logs/                      # Audit logs (daily, error, performance, security)
│   ├── Drops/                     # Drop files here for processing
│   ├── Sent/                      # Sent items
│   ├── LinkedIn/                  # LinkedIn config & analytics
│   ├── Facebook_Instagram/        # FB/IG config & analytics
│   ├── Twitter/                   # Twitter/X config & analytics
│   ├── WhatsApp/                  # WhatsApp config & messages
│   ├── Automation/                # Scheduled tasks configuration
│   └── Dashboard.md               # Your command center
├── src/
│   ├── orchestrator.py            # Main brain — vault lifecycle, Gmail sync, checkbox workflow
│   ├── setup_gmail_oauth.py       # OAuth setup for Gmail API
│   ├── ai_employee_vault/         # Storage layer (SQLite-backed)
│   │   ├── storage.py             # MemoryStore, TaskStore, ChatStore, PreferenceStore
│   │   └── __init__.py
│   ├── silver_tier/               # Advanced features (Silver Tier)
│   │   ├── mcp_server.py          # Core MCP server (16 tools, port 8080)
│   │   ├── mcp_server_fixed.py    # Fixed MCP server with LinkedIn Playwright automation
│   │   ├── linkedin_service.py    # LinkedIn API v2 integration
│   │   ├── whatsapp_watcher.py    # WhatsApp message monitoring
│   │   ├── analytics_service.py   # Event tracking, workflow analytics
│   │   ├── automation_scheduler.py# Cron-like task scheduler
│   │   ├── claude_reasoning.py    # Task complexity analysis & plan generation
│   │   ├── facebook_instagram_service.py  # FB/IG Graph API v18.0
│   │   ├── twitter_service.py     # Twitter/X API v2 integration
│   │   ├── api_integration_service.py  # Third-party integration manager
│   │   ├── multimodal_service.py  # Text/image/video/audio/document processing
│   │   ├── security_service.py    # Encryption, MFA, access logging
│   │   ├── team_service.py        # Role-based team management
│   │   └── voice_service.py       # Multi-language voice interaction
│   ├── gold_tier/                 # Autonomous Employee features (Gold Tier)
│   │   ├── mcp_server_social.py   # Social media MCP server (14 tools, port 8081)
│   │   ├── enhanced_audit_logger.py  # Production-grade buffered audit logging
│   │   └── ralph_wiggum_loop_template.md  # Autonomous reasoning template
│   └── watchers/                  # File system monitors
│       ├── base_watcher.py        # Abstract base class for watchers
│       ├── gmail_watcher.py       # Gmail inbox monitoring
│       ├── filesystem_watcher.py  # Drop folder monitoring
│       ├── inbox_watcher.py       # Inbox checkbox processing
│       ├── linkedin_watcher.py    # LinkedIn notification polling
│       └── vault_watcher.py       # Comprehensive vault folder monitoring
├── skills/                        # AI capability definitions (Agent Skills)
│   ├── process-needs-action/      # Process items, create plans, execute actions
│   ├── handle-approval/           # Approval workflow management
│   ├── generate-briefing/         # CEO briefing generation
│   ├── update-dashboard/          # Dashboard metrics updates
│   ├── linkedin-automation/       # LinkedIn posting & engagement
│   ├── whatsapp-automation/       # WhatsApp messaging & responses
│   ├── mcp-execution/             # External action via MCP server
│   ├── analytics-reporting/       # Business intelligence reports
│   └── team-collaboration/        # Team management & task assignment
├── setup_integrations.py          # Interactive setup for LinkedIn, WhatsApp, Gmail
├── test_mcp.py                    # MCP server tests
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project metadata and build config
├── package.json                   # Node.js dependencies (optional)
├── CLAUDE.md                      # Claude Code interface documentation
├── Company_Handbook.md            # Business rules and communication policies
├── Business_Goals.md              # Quarterly objectives and key metrics
├── Dashboard.md                   # Current system status
└── README.md                      # This file
```

---

## Tier System

### 🥉 Bronze (Basic)

| Feature | Description |
|---------|-------------|
| Gmail watcher | Monitors inbox, syncs emails to vault |
| File drop watcher | Detects new files, creates metadata |
| Human-in-loop approval | Sensitive actions require review |
| Basic dashboard | Task counts and system health |

### 🥈 Silver (Intermediate)

Everything in Bronze, plus:

| Feature | Description |
|---------|-------------|
| **WhatsApp integration** | Handle messages automatically |
| **LinkedIn automation** | Post updates, track engagement |
| **MCP Server** | External API connections (16 tools) |
| **Analytics** | Business intelligence dashboards |
| **Scheduling** | Cron-based automation |
| **Team collaboration** | Multi-user support with RBAC |
| **Claude reasoning** | Smart plan generation |
| **Security services** | Encryption, MFA, access logging |
| **Multimodal processing** | Text, image, audio, video analysis |

### 🥇 Gold (Autonomous Employee)

Everything in Silver, plus:

| Feature | Description |
|---------|-------------|
| **Full cross-domain integration** | Personal + business operations unified |
| **Odoo accounting** | Self-hosted financial management via JSON-RPC |
| **Facebook & Instagram** | Visual content posting & analytics |
| **Twitter/X** | Real-time engagement & monitoring |
| **Multiple MCP servers** | Separate servers for different action types |
| **Enhanced audit logging** | Multi-level, categorized, buffered with error recovery |
| **Ralph Wiggum Loop** | Autonomous multi-step reasoning engine |
| **Weekly CEO Briefing** | Comprehensive Friday reports with business audit |
| **Error recovery** | Graceful degradation during partial outages |

---

## Service Integrations

### Gmail API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project → Enable Gmail API
3. Create OAuth credentials (Desktop app) → Download as `credentials.json`
4. Place in project root or run `python src/setup_gmail_oauth.py`

### WhatsApp Business API
1. Get credentials from [Meta for Developers](https://developers.facebook.com/)
2. Run `python setup_integrations.py` → Option 2
3. Or manually edit `vault_data/WhatsApp/config.json`:
   ```json
   {
     "api_url": "YOUR_WHATSAPP_API_URL",
     "api_token": "YOUR_WHATSAPP_TOKEN",
     "phone_number_id": "YOUR_PHONE_NUMBER_ID",
     "enabled": true
   }
   ```

### LinkedIn
1. Create app at [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps)
2. Get access token
3. Run `python setup_integrations.py` → Option 1
4. Or edit `vault_data/LinkedIn/config.json`:
   ```json
   {
     "access_token": "YOUR_ACCESS_TOKEN",
     "company_id": "YOUR_COMPANY_ID",
     "profile_id": "YOUR_PROFILE_ID",
     "enabled": true
   }
   ```

### Facebook & Instagram
1. Create Facebook Developer app at [Meta for Developers](https://developers.facebook.com/)
2. Create Facebook Page and connect Instagram Business Account
3. Edit `vault_data/Facebook_Instagram/config.json`:
   ```json
   {
     "access_token": "YOUR_FB_IG_ACCESS_TOKEN",
     "page_id": "YOUR_FACEBOOK_PAGE_ID",
     "instagram_account_id": "YOUR_INSTAGRAM_BUSINESS_ID",
     "auto_post_enabled": false
   }
   ```

### Twitter/X
1. Create Twitter Developer app
2. Get Bearer Token (Essential) or API Key/Secret + Access Token/Secret
3. Edit `vault_data/Twitter/config.json`:
   ```json
   {
     "bearer_token": "YOUR_TWITTER_BEARER_TOKEN",
     "api_key": "YOUR_API_KEY (optional)",
     "api_secret": "YOUR_API_SECRET (optional)",
     "access_token": "YOUR_ACCESS_TOKEN (optional)",
     "access_token_secret": "YOUR_ACCESS_TOKEN_SECRET (optional)",
     "auto_post_enabled": false
   }
   ```

### Odoo Accounting
1. Install [Odoo Community Edition](https://www.odoo.com/page/download)
2. Create database and set up chart of accounts
3. Configure JSON-RPC connection (auto-generated on first use):
   ```json
   {
     "url": "http://localhost:8069",
     "database": "your_db_name",
     "username": "admin",
     "password": "your_password"
   }
   ```

---

## Commands & Workflows

### Common Commands

```bash
# Process pending items
claude --cwd . "Process all items in Needs_Action"

# Generate weekly report
claude --cwd . "Create a Monday morning briefing"

# Check status
claude --cwd . "Show me the dashboard"

# Post to social media
claude --cwd . "Post to LinkedIn about our new product"
claude --cwd . "Post to Facebook and Instagram: Our new service is live! [image_url]"
claude --cwd . "Post to Twitter/X: Excited to announce our partnership!"

# Send WhatsApp
claude --cwd . "Send WhatsApp to +1234567890: Thanks for reaching out!"

# View audit logs
claude --cwd . "Show me today's audit log"
```

### Autonomous Workflow Example

```
1. 9:00 AM - Customer WhatsApp: "Do you offer payment plans for consulting?"
2. Claude reads message, checks Odoo for pricing policies
3. Drafts response with options, moves to Pending_Approval
4. You approve → Claude sends message via WhatsApp
5. Claude logs interaction in audit trail
6. If customer agrees → Claude auto-creates invoice in Odoo
7. Claude posts case study to LinkedIn/Facebook (approved template)
8. Friday 5 PM - You receive CEO briefing with revenue, social performance, insights
```

### How It Works

```
1. Email/Message arrives → Saved to Inbox (via watchers)
2. You check checkbox → Item moves to correct folder (or AI suggests)
3. AI analyzes → Creates a plan using Ralph Wiggum Loop
4. If sensitive → Requests your approval (Pending_Approval)
5. After approval → Executes action via appropriate MCP server
6. Logs result → Updates audit logs & Dashboard
7. Generates insights → Weekly CEO Briefing
```

---

## Security & Safety

### Protection Rules

| Rule | Description |
|------|-------------|
| **Local data** | Everything stays on your machine |
| **Human approval** | You control sensitive actions (payments >$50, new contacts, legal matters) |
| **Audit logs** | Every action recorded with multi-level logging |
| **No secrets in git** | `.gitignore` excludes all config files and credentials |
| **Graceful degradation** | If one service fails, others continue |

### What the AI Will NOT Do Without Approval

- Send payments
- Delete files outside the vault
- Reply to legal matters
- Share personal data
- Make commitments over $500

### Alert Keywords

The system flags messages containing: `urgent`, `asap`, `emergency`, `help`, `invoice`, `payment`, `overdue`, `late`, `contract`, `legal`, `lawyer`, `resign`, `terminate`, `cancel`.

### Approval Thresholds

| Action | Auto-Approved | Requires Approval |
|--------|--------------|-------------------|
| Customer responses | ✅ Yes | ❌ New contacts |
| Social media posts | ✅ Scheduled posts | ❌ Sensitive topics |
| Expense logging | ✅ Under $100 | ❌ Over $50 |
| Contracts | ❌ Never | ✅ All contracts |
| Refunds | ❌ Never | ✅ All refunds |
| File deletion | ❌ Outside vault | ✅ Inside vault |

---

## Configuration

### MCP Servers

The system uses multiple MCP (Model Context Protocol) servers for different action types:

| Server | Port | Tools | Purpose |
|--------|------|-------|---------|
| Core MCP | 8080 | 16 | Email, files, tasks, approvals, logging |
| Social MCP | 8081 | 14 | Facebook, Instagram, Twitter, analytics |

Start them with:

```bash
# Core MCP Server
python src/silver_tier/mcp_server_fixed.py --vault ./vault_data --port 8080

# Social MCP Server
python src/gold_tier/mcp_server_social.py --vault ./vault_data --port 8081
```

### Automation Scheduler

Scheduled tasks are configured in `vault_data/Automation/scheduled_tasks.json`:

| Task | Frequency | Description |
|------|-----------|-------------|
| Sync inbox | Hourly | Check Gmail for new emails |
| Update dashboard | Hourly | Refresh metrics |
| Process checkboxes | Minutely | Detect and act on checkbox changes |
| Weekly briefing | Weekly (Friday) | Generate CEO report |
| LinkedIn/WhatsApp sync | Daily | Pull messages and analytics |
| Log cleanup | Monthly | Archive old logs |

### File Naming Conventions

| Type | Format |
|------|--------|
| Emails | `EMAIL_{gmail_id}_{subject}.md` |
| WhatsApp | `WHATSAPP_{sender}_{date}.md` |
| Files | `FILE_{original_name}.md` |
| Payments | `PAYMENT_{recipient}_{date}.md` |
| Plans | `PLAN_{topic}_{date}.md` |
| Briefings | `BRIEFING_{date}.md` |

### Frontmatter Schema

All vault files use YAML frontmatter:

```yaml
---
type: email|task|plan|payment|file
source: gmail|whatsapp|manual
id: {unique_id}
status: pending|needs_action|pending_approval|approved|rejected|done|planned
created: {iso8601}
---
```

---

## Running on Schedule

### Using Cron

```bash
crontab -e

# Run orchestrator every hour
0 * * * * cd ~/Documents/AI_Employee_Vault && python src/orchestrator.py --vault ./vault_data --interval 3600
```

### Using Systemd Services

Create service files for MCP servers:

```bash
# Social MCP server as background service
nohup python src/gold_tier/mcp_server_social.py --vault ./vault_data --port 8081 > social_mcp.log 2>&1 &
```

### Using PM2 (Node.js)

## Security

```bash
pm2 start "python src/orchestrator.py --vault ./vault_data" --name ai-employee
pm2 start "python src/silver_tier/mcp_server_fixed.py --vault ./vault_data --port 8080" --name mcp-core
pm2 start "python src/gold_tier/mcp_server_social.py --vault ./vault_data --port 8081" --name mcp-social
pm2 save
```

---

| Folder | What Goes Here |
|--------|----------------|
| `Inbox` | New emails, messages |
| `Needs_Action` | Items you need to handle |
| `Pending_Approval` | Waiting for your OK |
| `Done` | Completed items |
| `Plans` | AI-generated action plans |
| `Briefings` | Weekly/monthly reports |
| `Accounting` | Financial records (invoices, expenses) |
| `Logs` | Audit logs (daily, error, performance, security) |

## Development

### Install Development Dependencies

## Need Help?

```bash
pip install pytest black ruff
```

### Run Tests

```bash
python -m pytest
```

### Code Formatting

```bash
# Format code
black src/

# Lint code
ruff check src/
```

### Project Metadata

- **Python**: 3.12+
- **Build System**: Hatchling
- **Package Manager**: pip (via requirements.txt) or uv
- **Entry Points**: `ai-employee`, `ai-gmail-watcher`, `ai-file-watcher`

### Key Dependencies

| Package | Purpose |
|---------|---------|
| `google-api-python-client` | Gmail API integration |
| `google-auth` | OAuth2 authentication |
| `google-auth-oauthlib` | OAuth flow handling |
| `playwright` | Browser automation (LinkedIn) |
| `watchdog` | File system monitoring |

---

## Troubleshooting

### Gmail Not Syncing

1. Check `credentials.json` exists in project root
2. Run `python src/setup_gmail_oauth.py` to re-authenticate
3. Verify Gmail API is enabled in Google Cloud Console

### MCP Server Won't Start

1. Ensure port 8080/8081 is not in use: `lsof -i :8080`
2. Check dependencies: `pip install -r requirements.txt`
3. Run with verbose logging: `python src/silver_tier/mcp_server_fixed.py --vault ./vault_data --port 8080 --debug`

### Social Media Posts Failing

1. Verify API tokens in respective `config.json` files
2. Check token expiration (LinkedIn tokens expire after 60 days)
3. Review error logs in `vault_data/Logs/`

### Approval Items Stuck

1. Check `vault_data/Pending_Approval/` for items
2. Review `CLAUDE.md` for approval workflow rules
3. Manually move files to `Approved/` or `Rejected/` to resolve

### Dashboard Not Updating

1. Ensure orchestrator is running
2. Check `vault_data/Dashboard.md` timestamp
3. Trigger manually: `claude --cwd . "Update the dashboard"`

---

## Documentation

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | Claude Code interface and workflow documentation |
| `Company_Handbook.md` | Business rules and communication policies |
| `Business_Goals.md` | Quarterly objectives and key metrics |
| `Dashboard.md` | Real-time system status |
| `SILVER_TIER_STATUS.md` | Silver Tier implementation progress |
| `SILVER_TIER_GAP_ANALYSIS.md` | Gap analysis for Silver Tier |
| `GOLD_TIER_IMPLEMENTATION_SUMMARY.md` | Gold Tier technical details |
| `BRONZE_TIER_ASSESSMENT.md` | Bronze Tier assessment |

---

## License

MIT

---
*Build your Autonomous Employee today!*
