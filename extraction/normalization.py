"""
Normalization: Standardizes extracted data into canonical forms for analysis and comparison.
"""

from typing import Dict, Any, List, Optional, Set
import re
import hashlib
import json

NODE_TYPE_ALIASES = {
    "httprequest": "http_request",
    "httprequestnode": "http_request",
    "readbinaryfile": "read_binary_file",
    "spreadsheetfile": "spreadsheet_file",
    "postgres": "postgres",
    "googlesheets": "google_sheets",
    "gmail": "gmail",
    "slack": "slack",
    "telegram": "telegram",
    "discord": "discord",
    "webhook": "webhook",
    "scheduletrigger": "schedule_trigger",
    "cron": "schedule_trigger",
    "code": "code",
    "function": "code",
    "set": "set",
    "editfields": "set",
    "if": "if",
    "switch": "switch",
    "merge": "merge",
    "splitinbatches": "split_in_batches",
    "sticky": "sticky_note",
    "stickynote": "sticky_note",
    "agent": "agent",
    "lmchatopenai": "openai_chat_model",
    "lmchatanthropic": "anthropic_chat_model",
    "lmchatgemini": "gemini_chat_model",
    "lmchatollama": "ollama_chat_model",
    "vectordbpinecone": "pinecone",
    "vectordbqdrant": "qdrant",
    "vectordbweaviate": "weaviate",
    "embeddingsopenai": "openai_embeddings",
    "documentloader": "document_loader",
    "textsplitter": "text_splitter",
    "retriever": "retriever",
    "memorybuffer": "memory_buffer",
    "tool": "tool",
    "airtable": "airtable",
    "supabase": "supabase",
    "notion": "notion",
    "salesforce": "salesforce",
    "hubspot": "hubspot",
    "jira": "jira",
    "linear": "linear",
    "clickup": "clickup",
    "monday": "monday",
    "asana": "asana",
    "trello": "trello",
    "github": "github",
    "gitlab": "gitlab",
}

INTEGRATION_ALIASES = {
    "googlesheets": "Google Sheets",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "sqlite": "SQLite",
    "supabase": "Supabase",
    "airtable": "Airtable",
    "openai_chat_model": "OpenAI",
    "anthropic_chat_model": "Anthropic",
    "gemini_chat_model": "Gemini",
    "ollama_chat_model": "Ollama",
    "pinecone": "Pinecone",
    "qdrant": "Qdrant",
    "weaviate": "Weaviate",
    "telegram": "Telegram",
    "slack": "Slack",
    "discord": "Discord",
    "gmail": "Gmail",
    "notion": "Notion",
    "salesforce": "Salesforce",
    "hubspot": "HubSpot",
    "jira": "Jira",
    "linear": "Linear",
    "clickup": "ClickUp",
    "monday": "Monday",
    "asana": "Asana",
    "trello": "Trello",
    "github": "GitHub",
    "gitlab": "GitLab",
}


class Normalizer:
    @staticmethod
    def normalize_node_type(node_type: str) -> str:
        """Normalize node type to canonical form."""
        if not node_type:
            return "unknown"
        
        # Extract clean type (last part after .)
        clean = node_type.split(".")[-1].lower()
        clean = re.sub(r'[^a-z0-9]+', '', clean)
        
        return NODE_TYPE_ALIASES.get(clean, clean)

    @staticmethod
    def normalize_integration_name(integration: str) -> str:
        """Normalize integration name to canonical display form."""
        if not integration:
            return "Unknown"
        
        clean = integration.lower()
        clean = re.sub(r'[^a-z0-9]+', '', clean)
        
        return INTEGRATION_ALIASES.get(clean, integration)

    @staticmethod
    def normalize_category(category: str) -> str:
        """Normalize category name."""
        if not category:
            return "Other"
        cat = category.strip()
        cat_lower = cat.lower()
        
        # Common category mappings
        if cat_lower in ["ai", "artificial intelligence"]:
            return "AI"
        if cat_lower in ["marketing", "social media"]:
            return "Marketing"
        if cat_lower in ["sales", "crm"]:
            return "Sales"
        if cat_lower in ["engineering", "devops", "development"]:
            return "Engineering"
        if cat_lower in ["finance", "accounting"]:
            return "Finance"
        if cat_lower in ["hr", "human resources"]:
            return "HR"
        if cat_lower in ["support", "customer support", "helpdesk"]:
            return "Customer Support"
        
        return cat

    @staticmethod
    def normalize_date(date_str: Optional[str]) -> Optional[str]:
        """Normalize date strings to ISO format."""
        if not date_str:
            return None
        # Already ISO?
        try:
            from datetime import datetime
            if 'T' in date_str and date_str.endswith('Z'):
                return date_str
            # Try parsing common formats
            for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.isoformat() + "Z"
                except ValueError:
                    continue
        except Exception:
            pass
        return date_str

    @staticmethod
    def compute_content_hash(data: Dict[str, Any]) -> str:
        """Compute deterministic content hash for change detection."""
        # Serialize with sorted keys for consistency
        serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    @staticmethod
    def compute_structure_hash(nodes: List[Dict], connections: Dict) -> str:
        """Compute structural hash ignoring cosmetic differences."""
        # Extract structural signature
        structure = {
            "node_types": sorted([n.get("node_type_clean", "") for n in nodes]),
            "node_categories": sorted([n.get("node_category", "") for n in nodes]),
            "triggers": sorted([n.get("node_type_clean", "") for n in nodes if n.get("is_trigger")]),
            "ai_nodes": sorted([n.get("node_type_clean", "") for n in nodes if n.get("is_ai")]),
            "code_nodes": sorted([n.get("node_type_clean", "") for n in nodes if n.get("is_code")]),
            "connections_count": 0,
        }
        
        if isinstance(connections, dict):
            conn_count = 0
            for src, outputs in connections.items():
                if isinstance(outputs, dict):
                    for out_type, conns in outputs.items():
                        if isinstance(conns, list):
                            for conn_group in conns:
                                if isinstance(conn_group, list):
                                    conn_count += len(conn_group)
            structure["connections_count"] = conn_count
        
        serialized = json.dumps(structure, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()