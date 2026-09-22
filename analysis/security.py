"""
Security Review Analyzer: Analyzes workflow parameters, nodes, and code for credential risks and safety.
"""

from typing import Dict, Any, List, Tuple
import re

API_KEY_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
    (r"sk-ant-[a-zA-Z0-9]{20,}", "Anthropic API Key"),
    (r"ghp_[a-zA-Z0-9]{20,}", "GitHub Personal Access Token"),
    (r"AIza[0-9A-Za-z-_]{35}", "Google API Key"),
    (r"bearer\s+[a-zA-Z0-9_\-\.]{25,}", "Bearer Token"),
    (r"password[\"']?\s*[:=]\s*[\"'][^\"']{6,}[\"']", "Embedded Password"),
]


class SecurityAnalyzer:
    @staticmethod
    def analyze(workflow_data: Dict[str, Any]) -> Tuple[float, str, List[Dict[str, Any]]]:
        """
        Analyzes security posture.
        Returns (security_score, risk_level, security_findings_list).
        """
        nodes = workflow_data.get("nodes", [])
        findings = []
        deductions = 0.0

        for node in nodes:
            node_name = node.get("node_name", "Node")
            node_type = node.get("node_type", "")
            params = node.get("parameters") or {}
            
            params_str = str(params)
            
            # 1. Check for embedded secrets
            for pattern, secret_type in API_KEY_PATTERNS:
                if re.search(pattern, params_str, re.IGNORECASE):
                    findings.append({
                        "finding_type": "HARDCODED_SECRET",
                        "risk_level": "CRITICAL",
                        "description": f"Possible hard-coded {secret_type} detected in parameters of node '{node_name}'.",
                        "evidence": f"Node: {node_name} ({node_type})",
                        "recommendation": "Use n8n credential store or environment variables instead of hard-coding keys."
                    })
                    deductions += 4.0

            # 2. Check for unsafe code execution patterns in code nodes
            if node.get("is_code"):
                js_code = str(params.get("jsCode", "") or params.get("pythonCode", "") or "")
                if "eval(" in js_code or "exec(" in js_code:
                    findings.append({
                        "finding_type": "DYNAMIC_CODE_EXECUTION",
                        "risk_level": "HIGH",
                        "description": f"Dynamic code execution (eval/exec) found in code node '{node_name}'.",
                        "evidence": f"Node: {node_name}",
                        "recommendation": "Refactor code to avoid dynamic eval/exec to prevent injection vulnerabilities."
                    })
                    deductions += 2.0

            # 3. Check for unauthenticated webhook triggers
            if "webhook" in node_type.lower() and node.get("is_trigger"):
                auth_mode = params.get("authentication", "none")
                if auth_mode == "none":
                    findings.append({
                        "finding_type": "UNPROTECTED_WEBHOOK",
                        "risk_level": "MEDIUM",
                        "description": f"Webhook trigger '{node_name}' does not configure authentication headers or tokens.",
                        "evidence": f"Authentication mode: {auth_mode}",
                        "recommendation": "Enable Basic Auth or Header Auth on webhook endpoints to prevent unauthorized triggers."
                    })
                    deductions += 1.0

            # 4. Check for community / unverified nodes
            if node.get("is_custom"):
                findings.append({
                    "finding_type": "COMMUNITY_NODE_DEPENDENCY",
                    "risk_level": "LOW",
                    "description": f"Node '{node_name}' uses custom community package '{node_type}'.",
                    "evidence": f"Package: {node_type}",
                    "recommendation": "Review community package source code before deploying in production environments."
                })
                deductions += 0.5

        # Calculate final security score
        security_score = round(max(1.0, min(10.0, 10.0 - deductions)), 2)
        
        if security_score >= 9.0:
            risk_level = "LOW"
        elif security_score >= 7.0:
            risk_level = "MEDIUM"
        elif security_score >= 4.5:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return security_score, risk_level, findings
