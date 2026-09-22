"""
Problem Solver: Generates the mandatory 'Problem It Solves' one-liner for each workflow.

The problem statement must:
- Be exactly one concise sentence
- Describe the user's problem, not just repeat the workflow title
- Explain what recurring problem exists, who experiences it, and what manual work is reduced
- Be 10-30 words recommended
"""

from typing import Dict, Any, List
import re


class ProblemSolver:
    """Generates concise 'Problem It Solves' statements from workflow evidence."""
    
    INTEGRATION_ALIASES = {
        "gmail": "Gmail",
        "outlook": "Outlook",
        "email": "email",
        "googlesheets": "Google Sheets",
        "googledrive": "Google Drive",
        "excel": "Excel",
        "spreadsheetfile": "Excel/CSV spreadsheets",
        "spreadsheet": "spreadsheets",
        "postgres": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "supabase": "Supabase",
        "airtable": "Airtable",
        "notion": "Notion",
        "slack": "Slack",
        "teams": "Microsoft Teams",
        "discord": "Discord",
        "telegram": "Telegram",
        "whatsapp": "WhatsApp",
        "dropbox": "Dropbox",
        "onedrive": "OneDrive",
        "github": "GitHub",
        "gitlab": "GitLab",
        "jira": "Jira",
        "trello": "Trello",
        "asana": "Asana",
        "linear": "Linear",
        "hubspot": "HubSpot",
        "salesforce": "Salesforce",
        "pipedrive": "Pipedrive",
        "zendesk": "Zendesk",
        "freshdesk": "Freshdesk",
        "intercom": "Intercom",
        "stripe": "Stripe",
        "paypal": "PayPal",
        "twilio": "Twilio",
        "sendgrid": "SendGrid",
        "mailgun": "Mailgun",
        "typeform": "Typeform",
        "nextcloud": "Nextcloud",
        "mautic": "Mautic",
        "mattermost": "Mattermost",
        "rocketchat": "Rocket.Chat",
        "pagerduty": "PagerDuty",
        "clickup": "ClickUp",
        "todoist": "Todoist",
        "coda": "Coda",
        "chargebee": "Chargebee",
        "clearbit": "Clearbit",
        "mailchimp": "Mailchimp",
        "activecampaign": "ActiveCampaign",
        "wit": "Wit.ai",
        "bitly": "Bitly",
        "zoom": "Zoom",
        "circleci": "CircleCI",
        "digitalocean": "DigitalOcean",
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "ollama": "Ollama",
        "pinecone": "Pinecone",
        "qdrant": "Qdrant",
        "webhook": "Webhooks",
        "http": "HTTP APIs",
    }

    @classmethod
    def get_friendly_integrations(cls, integrations: List[str]) -> List[str]:
        friendly = []
        for i in integrations:
            clean = re.sub(r'[^a-zA-Z0-9]', '', i.lower())
            for key, name in cls.INTEGRATION_ALIASES.items():
                if key in clean:
                    if name not in friendly:
                        friendly.append(name)
                    break
            else:
                formatted = i.replace("_", " ").replace("-", " ").title()
                if formatted not in friendly:
                    friendly.append(formatted)
        return friendly

    @classmethod
    def generate(cls, workflow_data: Dict[str, Any]) -> str:
        """
        Generate the 'Problem It Solves' one-liner based on semantic intent and integrations.
        """
        title = workflow_data.get("title", "").strip()
        title_lower = title.lower()
        description = (workflow_data.get("description") or "").strip()
        desc_lower = description.lower()
        categories = [c.lower() for c in workflow_data.get("categories", [])]
        raw_integs = workflow_data.get("integrations", [])
        integrations = cls.get_friendly_integrations(raw_integs)
        nodes = workflow_data.get("nodes", [])
        
        has_ai = any(n.get("is_ai") for n in nodes)
        
        source = integrations[0] if len(integrations) >= 1 else "external sources"
        target = integrations[1] if len(integrations) >= 2 else (integrations[0] if len(integrations) >= 1 else "target systems")
        all_integs_str = ", ".join(integrations[:3]) if integrations else "connected apps"

        # 1. Invoices & Billing
        if any(w in title_lower or w in desc_lower for w in ["invoice", "receipt", "billing", "payout", "chargebee", "stripe"]):
            if "typeform" in title_lower or "typeform" in [i.lower() for i in raw_integs]:
                return f"Automatically generates invoices in {target} from form submissions, eliminating manual invoice creation."
            return f"Automatically processes invoices and payment records in {all_integs_str} to reduce manual financial data entry."

        # 2. Scheduling & Calendar
        if any(w in title_lower or w in desc_lower for w in ["calendar", "schedule", "appointment", "booking", "meeting", "zoom"]):
            if "zoom" in title_lower or "zoom" in [i.lower() for i in raw_integs]:
                return "Automatically creates and schedules Zoom meetings without manual calendar coordination."
            return "Automatically schedules appointments and blocks occupied calendar slots to avoid double bookings and manual coordination."

        # 3. Form Submissions (Typeform, etc.)
        if any(w in title_lower or w in desc_lower for w in ["typeform", "form submission", "survey results", "jotform"]):
            if len(integrations) >= 2:
                targets = " and ".join(integrations[1:3]) if len(integrations) >= 2 else target
                return f"Automatically captures form responses from {source} and routes data to {targets}, eliminating manual data entry."
            return f"Automatically captures form submissions and records responses in {all_integs_str} to streamline lead and survey collection."

        # 4. Error Handling & Monitoring
        if any(w in title_lower or w in desc_lower for w in ["handle error", "error workflow", "catch error", "alert on error"]):
            return "Automatically intercepts and manages failures from background workflows so operations teams can respond before services break."

        # 5. Phishing & Security Alerts
        if any(w in title_lower or w in desc_lower for w in ["phishing", "incident", "pagerduty", "signl4", "security alert"]):
            return "Automatically reports and dispatches critical security or incident alerts to response teams to minimize downtime."

        # 6. AI Agents & RAG Support
        if has_ai or any(w in title_lower or w in desc_lower for w in ["rag", "ai agent", "gpt", "llm", "chatbot"]):
            if any(w in title_lower for w in ["support", "query", "queries"]):
                return f"Automatically triages and answers customer queries using AI and knowledge retrieval to reduce manual support workload."
            return f"Automates complex conversational and reasoning tasks using AI models in {all_integs_str} to reduce repetitive human effort."

        # 7. Customer Support & Tickets
        if any(w in title_lower or w in desc_lower for w in ["ticket", "zendesk", "freshdesk", "intercom", "support message"]):
            return f"Automatically creates and routes customer support tickets from incoming messages to eliminate manual dispatching."

        # 8. Sales & CRM Lead Management
        if any(w in title_lower or w in desc_lower for w in ["lead", "crm", "hubspot", "pipedrive", "salesforce", "mautic", "activecampaign"]):
            return f"Automatically captures and synchronizes sales leads into {all_integs_str} to prevent lost inquiries and manual CRM updates."

        # 9. Email Notifications & Mailbox Listening
        if any(w in title_lower for w in ["listen on new email", "imap", "mailbox", "inbox", "gmail"]):
            if "listen" in title_lower or "imap" in title_lower:
                return "Continuously monitors mailbox for new incoming messages to trigger immediate automated processing without manual inbox checking."
            return "Automatically organizes and processes incoming email messages so users spend less time manually managing their inbox."

        # 10. Developer / Code / Git / DevOps Workflows
        if any(w in title_lower or w in desc_lower for w in ["github", "gitlab", "circleci", "digitalocean", "docker", "release", "deploy"]):
            if any(w in title_lower for w in ["slack", "discord", "notify", "notification"]):
                return f"Automatically posts repository and deployment updates from {source} to {target} so dev teams stay informed without checking dashboards."
            return f"Automates developer and infrastructure operations across {all_integs_str} to reduce repetitive command-line maintenance."

        # 11. Social Media & Content Feeds (RSS, Telegram, Discord, Mastodon, Twitter)
        if any(w in title_lower or w in desc_lower for w in ["rss", "telegram bot", "discord bot", "mastodon", "tweet", "twitter", "sticker bot"]):
            if "rss" in title_lower:
                return f"Automatically monitors RSS feeds and broadcasts new articles to {target} to keep audiences updated without manual sharing."
            if "telegram" in title_lower or "discord" in title_lower:
                return f"Automatically delivers automated responses and alerts via {source} to streamline chat community communication."
            return f"Automatically publishes content updates to {all_integs_str} on schedule to maintain active presence without manual posting."

        # 12. Weather, SMS, and Alerts
        if any(w in title_lower or w in desc_lower for w in ["weather", "sms", "twilio", "messagebird", "affirmation"]):
            if "weather" in title_lower:
                return "Automatically delivers daily weather forecasts and alerts to users without requiring manual weather lookups."
            if "sms" in title_lower or "whatsapp" in title_lower:
                return f"Automatically dispatches SMS and instant notifications via {all_integs_str} for timely communication."

        # 13. Data Sync / Transfer / Database Operations
        if any(w in title_lower for w in ["sync", "transfer", "insert", "convert", "merge", "export", "backup", "save"]):
            if "backup" in title_lower:
                return f"Automatically backs up data from {source} to {target} to prevent accidental loss without manual routine downloads."
            if "sync" in title_lower:
                return f"Automatically synchronizes data between {source} and {target} to eliminate manual copy-paste and keep records consistent."
            if "convert" in title_lower or "transform" in title_lower:
                return f"Automatically converts and formats data payloads between systems to eliminate tedious manual file conversions."
            return f"Automatically transfers and syncs records between {source} and {target} to eliminate repetitive manual data entry."

        # 14. Fallback from title
        clean_title = title.lower()
        for prefix in ["how to ", "sample ", "example ", "n8n nodemation basic - ", "using the "]:
            if clean_title.startswith(prefix):
                clean_title = clean_title[len(prefix):]
                
        return f"Automates {clean_title} to eliminate repetitive manual effort and streamline daily operations."
