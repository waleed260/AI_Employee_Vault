# AI Employee Vault

A personal AI assistant that manages your emails, tasks, and business operations automatically — now with **Gold Tier Autonomous Employee** capabilities.

## What It Does

- **Reads your emails** from Gmail and processes them automatically
- **Monitors WhatsApp** for messages and leads
- **Posts to LinkedIn, Facebook, Instagram, and Twitter/X** for business growth
- **Creates intelligent plans** for tasks using AI reasoning (Ralph Wiggum Loop)
- **Handles approvals** for sensitive actions (payments, new contacts, etc.)
- **Manages finances** via self-hosted Odoo accounting (JSON-RPC integration)
- **Generates reports** - daily and weekly CEO briefings
- **Runs on schedule** - automated workflows via cron
- **Provides bidirectional social media**: reads messages, understands intent, generates responses, and posts—all autonomously
- **Maintains comprehensive audit logs** with error recovery and graceful degradation

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the main system (orchestrator)
python src/orchestrator.py --vault ./vault_data

# 3. Start MCP servers (in separate terminals)
python src/silver_tier/mcp_server_fixed.py --vault ./vault_data --port 8080
python src/gold_tier/mcp_server_social.py --vault ./vault_data --port 8081

# 4. Use with Claude Code
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
│   ├── Rejected/           # Rejected items
│   ├── Briefings/          # Weekly/monthly reports
│   ├── Accounting/         # Financial records
│   ├── Analytics/          # Business metrics
│   ├── Logs/               # Audit logs
│   ├── LinkedIn/           # LinkedIn posts & analytics
│   ├── Facebook_Instagram/ # FB/IG posts & analytics
│   ├── Twitter/            # Twitter/X posts & analytics
│   ├── WhatsApp/           # WhatsApp messages
│   └── Dashboard.md        # Your command center
├── src/
│   ├── orchestrator.py     # Main brain
│   ├── gmail_service.py   # Gmail connection
│   ├── silver_tier/       # Advanced features (Silver Tier)
│   │   ├── linkedin_service.py
│   │   ├── mcp_server.py
│   │   ├── mcp_server_fixed.py
│   │   ├── whatsapp_watcher.py
│   │   ├── analytics_service.py
│   │   └── ...
│   ├── gold_tier/         # Autonomous Employee features (Gold Tier)
│   │   ├── mcp_server_social.py
│   │   ├── enhanced_audit_logger.py
│   │   ├── facebook_instagram_service.py
│   │   └── twitter_service.py
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

### Silver (Intermediate)
Everything in Bronze, plus:
- **WhatsApp integration** - Handle messages automatically
- **LinkedIn automation** - Post updates, track engagement
- **MCP Server** - External API connections
- **Analytics** - Business intelligence dashboards
- **Scheduling** - Cron-based automation
- **Team collaboration** - Multi-user support
- **Claude reasoning** - Smart plan generation

### Gold (Autonomous Employee) - NEW
Everything in Silver, plus:
- **Full cross-domain integration** - Personal + business operations unified
- **Odoo accounting system** - Self-hosted financial management via JSON-RPC
- **Facebook & Instagram integration** - Visual content posting & analytics
- **Twitter/X integration** - Real-time engagement & monitoring
- **Multiple MCP servers** - Separate servers for different action types (core, social)
- **Enhanced audit logging** - Multi-level, categorized, buffered with error recovery
- **Ralph Wiggum Loop** - Autonomous multi-step reasoning engine
- **Weekly CEO Briefing & Business Audit** - Comprehensive Friday reports
- **Human-in-the-Loop approval workflow** - Smart approvals for sensitive actions
- **Error recovery & graceful degradation** - System continues during partial outages

## How It Works (Gold Tier Flow)

```
1. Email/Message arrives → Saved to Inbox (via watchers)
2. You check checkbox → Item moves to correct folder (or AI suggests)
3. AI analyzes → Creates a plan using Ralph Wiggum Loop (multi-step reasoning)
4. If sensitive → Requests your approval (Pending_Approval)
5. After approval → Executes action via appropriate MCP server
6. Logs result → Updates audit logs & Dashboard
7. Generates insights → Weekly CEO Briefing
```

### Example Autonomous Workflow:
1. **9:00 AM** - Customer WhatsApp: "Do you offer payment plans for consulting?"
2. **Claude** reads message, checks Odoo accounting for your policies
3. **Claude** drafts response with options, moves to Pending_Approval for your review
6. **You approve** → Claude sends message via WhatsApp
7. **Claude** logs interaction in audit trail
8. **If customer agrees** → Claude auto-creates invoice in Odoo
9. **Claude** posts case study to LinkedIn/Facebook (using approved template)
10. **Friday 5 PM** - You receive CEO briefing with revenue, social performance, insights

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

# Post to Facebook/Instagram
"Post to Facebook and Instagram: Our new service is live! [image_url]"

# Tweet
"Post to Twitter/X: Excited to announce our partnership with [partner]!"

# View audit logs
"Show me today's audit log"
```

## Setting Up Services

### Gmail API (Required)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project → Enable Gmail API
3. Create OAuth credentials → Download as `credentials.json`
4. Place in `src/` directory (or configure path)

### WhatsApp API (Required for WhatsApp features)
1. Get WhatsApp Business API credentials
2. Edit `vault_data/WhatsApp/config.json`

### LinkedIn (Required for LinkedIn features)
1. Create LinkedIn Developer app
2. Get access token
3. Edit `vault_data/LinkedIn/config.json`

### Facebook & Instagram (Required for FB/IG features)
1. Create Facebook Developer app
2. Get access token from [Meta for Developers](https://developers.facebook.com/)
3. Create Facebook Page and connect Instagram Business Account
4. Edit `vault_data/Facebook_Instagram/config.json`:
   ```json
   {
     "access_token": "YOUR_FB_IG_ACCESS_TOKEN",
     "page_id": "YOUR_FACEBOOK_PAGE_ID",
     "instagram_account_id": "YOUR_INSTAGRAM_BUSINESS_ID",
     "auto_post_enabled": false
   }
   ```

### Twitter/X (Required for Twitter features)
1. Create Twitter Developer app
2. Get Bearer Token (Essential) or API Key/Secret + Access Token/Secret
3. Edit `vault_data/Twitter/config.json`:
   ```json
   {
     "bearer_token": "YOUR_TWITTER_BEARER_TOKEN",
     "api_key": "YOUR_API_KEY (optional if using bearer)",
     "api_secret": "YOUR_API_SECRET (optional)",
     "access_token": "YOUR_ACCESS_TOKEN (optional)",
     "access_token_secret": "YOUR_ACCESS_TOKEN_SECRET (optional)",
     "auto_post_enabled": false
   }
   ```

### Odoo Accounting (Required for full financial management)
1. Install Odoo Community Edition locally (https://www.odoo.com/page/download)
2. Create database and set up chart of accounts
3. Configure JSON-RPC connection (will be prompted during first use)
4. Edit `vault_data/Accounting/odoo_config.json` (auto-generated):
   ```json
   {
     "url": "http://localhost:8069",
     "database": "your_db_name",
     "username": "admin",
     "password": "your_password"
   }
   ```

## Running on Schedule

```bash
# Add to crontab (runs orchestrator hourly)
crontab -e

# Run every hour
0 * * * * cd ~/Documents/AI_Employee_Vault && python src/orchestrator.py --vault ./vault_data --interval 3600

# Run MCP servers as services (use systemd, pm2, or simple nohup)
# Example for social MCP server:
nohup python src/gold_tier/mcp_server_social.py --vault ./vault_data --port 8081 > social_mcp.log 2>&1 &
```

## Security

- **Local data** - Everything stays on your machine
- **Human approval** - You control sensitive actions (contracts >$5K, pricing changes, etc.)
- **Audit logs** - Every action recorded in `/Logs/` with enhanced multi-level logging
- **No secrets in git** - Uses `.gitignore` for config files
- **Graceful degradation** - If one service fails (e.g., LinkedIn API), others continue

## Files Created by AI

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

## Need Help?

- Check `vault_data/Dashboard.md` for current status
- Read `CLAUDE.md` for technical details
- Review `skills/` folder for all AI capabilities
- See `GOLD_TIER_IMPLEMENTATION_SUMMARY.md` for deep technical details

## License

MIT

---
*Build your Autonomous Employee today!*