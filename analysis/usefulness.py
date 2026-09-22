"""
Usefulness and Business Value Analyzer: Assesses practical utility, automation potential, and business domain.
"""

from typing import Dict, Any, List, Tuple


class UsefulnessAnalyzer:
    @staticmethod
    def analyze(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes business domain, target audience, automation value, and practical usefulness.
        """
        title = workflow_data.get("title", "").lower()
        description = workflow_data.get("description", "").lower()
        categories = [c.lower() for c in workflow_data.get("categories", [])]
        integrations = [i.lower() for i in workflow_data.get("integrations", [])]
        node_count = workflow_data.get("node_count", 0)
        
        # Determine business domain
        domains = []
        if any(w in title or w in description or w in categories for w in ["ai", "gpt", "rag", "agent", "llm"]):
            domains.append("AI & Automation")
        if any(w in title or w in description or w in categories for w in ["lead", "sales", "crm", "hubspot", "deal"]):
            domains.append("Sales & CRM")
        if any(w in title or w in description or w in categories for w in ["marketing", "social", "tweet", "post", "instagram", "youtube", "seo"]):
            domains.append("Marketing & Content")
        if any(w in title or w in description or w in categories for w in ["support", "ticket", "customer", "zendesk", "faq"]):
            domains.append("Customer Support")
        if any(w in title or w in description or w in categories for w in ["devops", "github", "gitlab", "deploy", "server", "postgres", "sql"]):
            domains.append("Engineering & DevOps")
        if any(w in title or w in description or w in categories for w in ["doc", "pdf", "invoice", "excel", "sheets", "spreadsheet", "extract"]):
            domains.append("Document & Data Operations")
        if not domains:
            domains.append("General Productivity")
            
        primary_domain = domains[0]
        
        # Determine automation impact
        if node_count >= 8 or len(integrations) >= 3:
            automation_level = "HIGH"
            time_saved = "5+ hours/week of manual repetitive processing"
        elif node_count >= 4 or len(integrations) >= 2:
            automation_level = "MEDIUM"
            time_saved = "2-4 hours/week of routine task coordination"
        else:
            automation_level = "LOW"
            time_saved = "Quick utility task saving 30-60 minutes/week"

        return {
            "primary_domain": primary_domain,
            "all_domains": domains,
            "automation_level": automation_level,
            "estimated_time_saved": time_saved,
            "target_audience": "Developers, automation engineers, and business operators",
        }
