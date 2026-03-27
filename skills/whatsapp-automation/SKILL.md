# SKILL.md - WhatsApp Automation

## Purpose
Handle WhatsApp messages, automate responses, and manage conversations.

## Trigger
- Manual: "Check WhatsApp", "Reply to WhatsApp"
- Automated: Webhook notifications, polling

## Workflow

### 1. Receive Messages
- Process incoming webhooks
- Poll for new messages
- Save to vault Inbox

### 2. Categorize Messages
- Lead inquiries → `/Needs_Action`
- Support requests → `/Plans/`
- Urgent → Mark with priority

### 3. Automated Responses
- Quick replies for common questions
- Template messages for formal responses
- Escalate to human for complex issues

### 4. Send Messages
- Reply to specific contacts
- Send broadcast messages
- Use templates for automation

## Commands

```
# Send a message
Send WhatsApp to {number}: {message}

# Check conversations
Show WhatsApp conversations

# Get messages from {contact}
Show WhatsApp messages from {contact}

# Set auto-reply
Enable WhatsApp auto-reply
```

## Message Types

- **Text** - Regular text messages
- **Image** - Photos with captions
- **Audio** - Voice messages
- **Video** - Video messages
- **Document** - File attachments

## Templates

Quick reply templates:
- `greeting` - "Hello! Thanks for messaging. How can I help?"
- `away` - "I'm currently away. Will respond soon."
- `meeting` - "In a meeting now. Can we chat later?"
- `thanks` - "Thank you for your interest!"

## Configuration

Configure in `vault_data/WhatsApp/config.json`:
- API URL
- API Token
- Phone Number ID
- Auto-reply settings

## Approval Requirements

Always request approval for:
- Sending to new contacts
- Bulk messages
- Sensitive information
- Promotional content

## Success Criteria
- Messages received and processed
- Auto-replies sent appropriately
- Leads captured
- No spam violations
