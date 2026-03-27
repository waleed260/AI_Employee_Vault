# SKILL.md - LinkedIn Automation

## Purpose
Automate LinkedIn posting, engagement, and lead generation for business growth.

## Trigger
- Manual: "Post to LinkedIn", "Manage LinkedIn"
- Automated: Scheduled posts, new business updates

## Workflow

### 1. Post Content
- Read draft content from `/Plans/` or receive from user
- Apply appropriate template
- Post to LinkedIn (profile or company page)
- Log post ID and details

### 2. Engagement
- Monitor notifications for comments
- Like relevant posts automatically (if enabled)
- Reply to comments on your posts
- Process new connection requests

### 3. Lead Generation
- Track engagement on posts
- Identify interested prospects
- Save leads to `/Accounting/` or CRM

### 4. Analytics
- Get post performance metrics
- Track follower growth
- Generate weekly engagement reports

## Commands

```
# Post a simple update
Post to LinkedIn: {message}

# Schedule a post
Schedule LinkedIn post: {content} at {datetime}

# Get analytics
Show LinkedIn analytics

# Process notifications
Process LinkedIn notifications
```

## Templates

Available post templates:
- `product_launch` - Announce new products
- `milestone` - Celebrate achievements
- `testimonial` - Share customer feedback
- `tip` - Provide value to audience
- `behind_scenes` - Show company culture
- `news` - General business updates

## Configuration

Configure in `vault_data/LinkedIn/config.json`:
- Access token
- Company ID (for company page posts)
- Auto-like settings
- Auto-comment settings

## Approval Requirements

Always request approval for:
- Posts mentioning specific clients/partners
- Promotional content with offers
- Content about sensitive business topics

## Success Criteria
- Posts published successfully
- Engagement tracked
- Leads captured
- Analytics reported
