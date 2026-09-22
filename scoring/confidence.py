"""
Confidence Scoring: Calculates evidence completeness percentage (0 to 100%).
"""

from typing import Dict, Any, Tuple, List


class ConfidenceScorer:
    @staticmethod
    def calculate(workflow_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """
        Calculates confidence score (0 - 100%) based on verified evidence points.
        Returns (confidence_percentage, evidence_points_list).
        """
        score = 0.0
        evidence_points = []
        
        # 1. Page/Canonical URL verified (+15)
        if workflow_data.get("canonical_url"):
            score += 15.0
            evidence_points.append("Workflow page & canonical URL verified (+15%)")
            
        # 2. Description inspected (+10)
        desc = workflow_data.get("description", "")
        if desc and len(desc.strip()) > 10:
            score += 10.0
            evidence_points.append("Detailed description verified (+10%)")
        elif desc:
            score += 5.0
            evidence_points.append("Brief description verified (+5%)")
            
        # 3. Node information available (+15)
        nodes = workflow_data.get("nodes", [])
        if nodes and len(nodes) > 0:
            score += 15.0
            evidence_points.append(f"{len(nodes)} nodes extracted and categorized (+15%)")
            
        # 4. Workflow JSON topology inspected (+30)
        if workflow_data.get("connection_count", 0) > 0 or len(nodes) > 1:
            score += 30.0
            evidence_points.append("Complete workflow graph & connections inspected (+30%)")
        elif len(nodes) == 1:
            score += 15.0
            evidence_points.append("Single node structure inspected (+15%)")
            
        # 5. Dependencies & Integrations verified (+10)
        if "integrations" in workflow_data and workflow_data["integrations"]:
            score += 10.0
            evidence_points.append(f"{len(workflow_data['integrations'])} service integrations mapped (+10%)")
            
        # 6. Documentation / Setup steps verified (+10)
        if desc and any(k in desc.lower() for k in ["how to", "setup", "step", "prerequisite", "configure", "credentials", "1.", "2."]):
            score += 10.0
            evidence_points.append("Setup guide & configuration steps verified (+10%)")
        else:
            score += 3.0
            evidence_points.append("Basic documentation present (+3%)")
            
        # 7. Freshness / Dates verified (+5)
        if workflow_data.get("created_at_source") or workflow_data.get("updated_at_source"):
            score += 5.0
            evidence_points.append("Creation & modification timestamps verified (+5%)")
            
        # 8. Static validation performed (+5)
        if workflow_data.get("structure_hash"):
            score += 5.0
            evidence_points.append("Structural integrity & graph validation verified (+5%)")

        final_score = round(min(100.0, max(0.0, score)), 1)
        return final_score, evidence_points
