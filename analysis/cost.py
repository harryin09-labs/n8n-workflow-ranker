"""
Cost Classifier: Identifies external paid services and classifies workflow recurring cost footprint.
"""

from typing import Dict, Any, List, Tuple
import re

KNOWN_PAID_SERVICES = {
    "openai": "OpenAI API",
    "anthropic": "Anthropic Claude API",
    "elevenlabs": "ElevenLabs Voice API",
    "twilio": "Twilio SMS/Voice",
    "apify": "Apify Scraping",
    "serpapi": "SerpApi Search",
    "replicate": "Replicate AI",
    "cohere": "Cohere API",
    "salesforce": "Salesforce CRM",
    "hubspot": "HubSpot",
    "snowflake": "Snowflake Data Warehouse",
    "pinecone": "Pinecone Vector DB",
    "sendgrid": "SendGrid Email API",
    "mailgun": "Mailgun Email API",
    "rapidapi": "RapidAPI",
    "airtable": "Airtable",
}

KNOWN_FREE_SELF_HOSTED = {
    "postgres": "PostgreSQL (Self-hosted/Free tier)",
    "mysql": "MySQL (Self-hosted/Free tier)",
    "sqlite": "SQLite (Local/Free)",
    "redis": "Redis (Local/Free)",
    "mongodb": "MongoDB (Self-hosted/Free tier)",
    "ollama": "Ollama (Local LLM / 100% Free)",
    "telegram": "Telegram Bot (Free API)",
    "discord": "Discord Webhooks (Free)",
    "slack": "Slack (Free workspace API)",
    "github": "GitHub (Free for public/standard)",
    "googlesheets": "Google Sheets (Free quota)",
    "gmail": "Gmail (Free personal quota)",
    "notion": "Notion (Free API tier)",
    "webhook": "n8n Webhook Trigger (Free)",
    "scheduletrigger": "n8n Schedule Trigger (Free)",
    "code": "n8n Code/JavaScript Node (Free)",
    "httprequest": "HTTP Request (Native)",
}


class CostClassifier:
    @staticmethod
    def classify(workflow_data: Dict[str, Any]) -> Tuple[str, List[str], List[str], str]:
        """
        Classifies cost footprint into FREE, MOSTLY_FREE, LOW_COST, PAID, EXPENSIVE, UNKNOWN.
        Returns (cost_class, paid_dependencies, free_dependencies, cost_notes).
        """
        nodes = workflow_data.get("nodes", [])
        integrations = workflow_data.get("integrations", [])
        
        paid_found = set()
        free_found = set()
        
        # Scan integrations and node types
        for integ in integrations:
            clean = re.sub(r'[^a-zA-Z0-9]', '', integ.lower())
            for key, name in KNOWN_PAID_SERVICES.items():
                if key in clean:
                    paid_found.add(name)
            for key, name in KNOWN_FREE_SELF_HOSTED.items():
                if key in clean:
                    free_found.add(name)

        for node in nodes:
            node_type = node.get("node_type", "").lower()
            node_name = node.get("node_name", "").lower()
            
            for key, name in KNOWN_PAID_SERVICES.items():
                if key in node_type or key in node_name:
                    paid_found.add(name)
            for key, name in KNOWN_FREE_SELF_HOSTED.items():
                if key in node_type or key in node_name:
                    free_found.add(name)

        paid_list = sorted(list(paid_found))
        free_list = sorted(list(free_found))

        if len(paid_list) == 0:
            cost_class = "FREE"
            cost_notes = "100% free or self-hostable with no recurring external paid API costs."
        elif len(paid_list) == 1:
            if any("OpenAI" in p or "Claude" in p for p in paid_list):
                cost_class = "LOW_COST"
                cost_notes = f"Requires 1 paid API ({', '.join(paid_list)}) with pay-as-you-go micro-costs per execution."
            else:
                cost_class = "MOSTLY_FREE"
                cost_notes = f"Primarily free/standard tools with optional or low-usage paid service: {', '.join(paid_list)}."
        elif len(paid_list) <= 3:
            cost_class = "PAID"
            cost_notes = f"Requires multiple external paid subscriptions/APIs: {', '.join(paid_list)}."
        else:
            cost_class = "EXPENSIVE"
            cost_notes = f"High recurring infrastructure footprint with {len(paid_list)} paid enterprise services: {', '.join(paid_list)}."

        return cost_class, paid_list, free_list, cost_notes
