"""
Security Review Agent: Evaluates security risks and produces findings list.
"""

import logging
from typing import Dict, Any, List
from analysis.security import SecurityAnalyzer

logger = logging.getLogger(__name__)


class SecurityAgent:
    def __init__(self):
        self.analyzer = SecurityAnalyzer()

    def review(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Performs security review and populates findings in workflow_data."""
        sec_score, risk_level, findings = self.analyzer.analyze(workflow_data)
        workflow_data["security_score"] = sec_score
        workflow_data["security_risk_level"] = risk_level
        workflow_data["security_findings"] = findings
        return workflow_data
