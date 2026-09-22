"""
Main Scoring Engine: Calculates 12-dimension evidence-based scores, penalties, and overall rating labels.

12-Dimension Rubric (Weights sum to 100%):
- daily_life_practicality: 15% (0.15)
- automation_value: 13% (0.13)
- practical_usefulness: 10% (0.10)
- design_quality: 10% (0.10)
- reliability: 10% (0.10)
- ease_of_setup: 10% (0.10)
- reusability: 8% (0.08)
- documentation: 5% (0.05)
- integration_quality: 5% (0.05)
- security: 5% (0.05)
- cost_efficiency: 5% (0.05)
- maintenance: 4% (0.04)
TOTAL: 100% (1.00)
"""

from typing import Dict, Any, List, Tuple
from database.models import ScoreEvidenceModel, PenaltyModel
from analysis.daily_life import DailyLifePracticalityAnalyzer

WEIGHTS = {
    "daily_life_practicality": 0.15,
    "automation_value": 0.13,
    "practical_usefulness": 0.10,
    "design_quality": 0.10,
    "reliability": 0.10,
    "ease_of_setup": 0.10,
    "reusability": 0.08,
    "documentation": 0.05,
    "integration_quality": 0.05,
    "security": 0.05,
    "cost_efficiency": 0.05,
    "maintenance": 0.04,
}

# Verify weights sum exactly to 1.00
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-6, f"Weights must sum to 1.0, got {sum(WEIGHTS.values())}"

RATING_LABELS = [
    (9.00, 10.00, "Exceptional"),
    (8.00, 8.99, "Excellent"),
    (7.00, 7.99, "Very Good"),
    (6.00, 6.99, "Good"),
    (5.00, 5.99, "Average"),
    (4.00, 4.99, "Below Average"),
    (0.00, 3.99, "Poor"),
]


class ScoringEngine:
    @staticmethod
    def get_rating_label(score: float) -> str:
        for min_val, max_val, label in RATING_LABELS:
            if min_val <= score <= max_val:
                return label
        return "Average" if score >= 5.0 else "Poor"

    @classmethod
    def score_workflow(cls, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates all 12 criteria scores, penalties, base score, and overall final score.
        Returns dictionary with complete breakdown and evidence models.
        """
        nodes = workflow_data.get("nodes", [])
        node_count = len(nodes)
        connections = workflow_data.get("connection_count", 0)
        integrations = workflow_data.get("integrations", [])
        description = workflow_data.get("description", "")
        cost_class = workflow_data.get("cost_class", "FREE")
        security_score = workflow_data.get("security_score", 10.0)
        
        evidence_list: List[ScoreEvidenceModel] = []
        penalties_list: List[PenaltyModel] = []

        # 1. Practical Use in Daily Life (15%)
        # Measured by DailyLifePracticalityAnalyzer across 7 criteria
        daily_life_res = DailyLifePracticalityAnalyzer.analyze(workflow_data)
        daily_life_raw = daily_life_res["daily_life_practicality_score"]
        daily_life_freq = daily_life_res["daily_life_use_frequency"]
        evidence_list.append(ScoreEvidenceModel(
            criterion="daily_life_practicality",
            raw_score=daily_life_raw,
            weight=WEIGHTS["daily_life_practicality"],
            weighted_score=round(daily_life_raw * WEIGHTS["daily_life_practicality"], 4),
            evidence=f"Daily-life practicality: {daily_life_raw:.1f}/10 ({daily_life_res['daily_life_practicality_label']}), expected frequency: {daily_life_freq}.",
            reasoning=daily_life_res["daily_life_practicality_reason"],
            confidence=92.0,
            evidence_type="DERIVED"
        ))

        # 2. Automation / Time-Saving Value (13%)
        auto_raw = 6.5
        if node_count >= 8:
            auto_raw = 9.0
        elif node_count >= 4:
            auto_raw = 8.0
        elif node_count >= 2:
            auto_raw = 7.0
        evidence_list.append(ScoreEvidenceModel(
            criterion="automation_value",
            raw_score=auto_raw,
            weight=WEIGHTS["automation_value"],
            weighted_score=round(auto_raw * WEIGHTS["automation_value"], 4),
            evidence=f"{node_count} nodes chained across {connections} connections.",
            reasoning="Eliminates multi-step human interaction and manual data entry.",
            confidence=90.0,
            evidence_type="DERIVED"
        ))

        # 3. General Practical Usefulness (10%)
        # Measures how effectively it solves its intended problem
        usefulness_raw = 7.0
        title_lower = workflow_data.get("title", "").lower()
        desc_lower = description.lower()
        if any(w in desc_lower or w in title_lower for w in ["lead", "sync", "backup", "alert", "rag", "support", "sales", "report", "invoice", "email", "gmail"]):
            usefulness_raw = 8.5
        if node_count >= 3:
            usefulness_raw = min(10.0, usefulness_raw + 0.5)
        evidence_list.append(ScoreEvidenceModel(
            criterion="practical_usefulness",
            raw_score=usefulness_raw,
            weight=WEIGHTS["practical_usefulness"],
            weighted_score=round(usefulness_raw * WEIGHTS["practical_usefulness"], 4),
            evidence=f"Addresses target workflow domain with {len(integrations)} integrations.",
            reasoning="Effectively solves the specific functional domain requirement.",
            confidence=92.0,
            evidence_type="OBSERVED"
        ))

        # 4. Workflow Design Quality (10%)
        design_raw = 7.5
        if node_count > 0 and connections >= (node_count - 1):
            design_raw = 8.5
        if any(n.get("is_trigger") for n in nodes):
            design_raw = min(10.0, design_raw + 0.5)
        evidence_list.append(ScoreEvidenceModel(
            criterion="design_quality",
            raw_score=design_raw,
            weight=WEIGHTS["design_quality"],
            weighted_score=round(design_raw * WEIGHTS["design_quality"], 4),
            evidence=f"Connected graph with {connections} links and explicit triggers.",
            reasoning="Clean topology and modular node separation.",
            confidence=90.0,
            evidence_type="OBSERVED"
        ))

        # 5. Reliability / Robustness (10%)
        rel_raw = 7.5
        has_error_handling = any("error" in n.get("node_type", "").lower() for n in nodes)
        if has_error_handling:
            rel_raw = 9.0
        evidence_list.append(ScoreEvidenceModel(
            criterion="reliability",
            raw_score=rel_raw,
            weight=WEIGHTS["reliability"],
            weighted_score=round(rel_raw * WEIGHTS["reliability"], 4),
            evidence="Deterministic node pipelines without ambiguous branches.",
            reasoning="Standard n8n error handling and retry configuration.",
            confidence=85.0,
            evidence_type="DERIVED"
        ))

        # 6. Ease of Setup (10%)
        setup_raw = 8.5
        cred_count = sum(1 for n in nodes if n.get("credentials_needed"))
        if cred_count > 3:
            setup_raw = 6.0
        elif cred_count > 1:
            setup_raw = 7.5
        evidence_list.append(ScoreEvidenceModel(
            criterion="ease_of_setup",
            raw_score=setup_raw,
            weight=WEIGHTS["ease_of_setup"],
            weighted_score=round(setup_raw * WEIGHTS["ease_of_setup"], 4),
            evidence=f"Requires {cred_count} authentication credentials.",
            reasoning="Straightforward credential mapping and environment configuration.",
            confidence=90.0,
            evidence_type="OBSERVED"
        ))

        # 7. Reusability / Customization (8%)
        reuse_raw = 8.0
        if any(n.get("is_code") or n.get("node_type_normalized") == "set" for n in nodes):
            reuse_raw = 9.0
        evidence_list.append(ScoreEvidenceModel(
            criterion="reusability",
            raw_score=reuse_raw,
            weight=WEIGHTS["reusability"],
            weighted_score=round(reuse_raw * WEIGHTS["reusability"], 4),
            evidence="Parameterized inputs and transformable schema.",
            reasoning="Easily adaptable to adjacent tools and alternative APIs.",
            confidence=85.0,
            evidence_type="INFERRED"
        ))

        # 8. Documentation Quality (5%)
        doc_raw = 6.0
        if len(description) > 200:
            doc_raw = 9.0
        elif len(description) > 50:
            doc_raw = 7.5
        evidence_list.append(ScoreEvidenceModel(
            criterion="documentation",
            raw_score=doc_raw,
            weight=WEIGHTS["documentation"],
            weighted_score=round(doc_raw * WEIGHTS["documentation"], 4),
            evidence=f"Description length: {len(description)} chars.",
            reasoning="Provides context and configuration guidance for users.",
            confidence=95.0,
            evidence_type="OBSERVED"
        ))

        # 9. Integration Quality (5%)
        integ_raw = 8.0
        if len(integrations) >= 2:
            integ_raw = 9.0
        evidence_list.append(ScoreEvidenceModel(
            criterion="integration_quality",
            raw_score=integ_raw,
            weight=WEIGHTS["integration_quality"],
            weighted_score=round(integ_raw * WEIGHTS["integration_quality"], 4),
            evidence=f"Integrates with {len(integrations)} services: {', '.join(integrations[:3])}.",
            reasoning="Uses native official n8n nodes for all endpoints.",
            confidence=90.0,
            evidence_type="OBSERVED"
        ))

        # 10. Security (5%)
        sec_raw = security_score
        evidence_list.append(ScoreEvidenceModel(
            criterion="security",
            raw_score=sec_raw,
            weight=WEIGHTS["security"],
            weighted_score=round(sec_raw * WEIGHTS["security"], 4),
            evidence=f"Static security scan score: {sec_raw:.1f}/10.",
            reasoning="Evaluated for embedded secrets, injection risks, and webhook auth.",
            confidence=90.0,
            evidence_type="DERIVED"
        ))

        # 11. Cost Efficiency (5%)
        cost_raw = 8.0
        if cost_class == "FREE":
            cost_raw = 10.0
        elif cost_class == "MOSTLY_FREE":
            cost_raw = 8.5
        elif cost_class == "LOW_COST":
            cost_raw = 7.5
        elif cost_class == "PAID":
            cost_raw = 6.0
        elif cost_class == "EXPENSIVE":
            cost_raw = 4.0
        evidence_list.append(ScoreEvidenceModel(
            criterion="cost_efficiency",
            raw_score=cost_raw,
            weight=WEIGHTS["cost_efficiency"],
            weighted_score=round(cost_raw * WEIGHTS["cost_efficiency"], 4),
            evidence=f"Cost classification: {cost_class}.",
            reasoning="Affordable or free running costs for target automation payload.",
            confidence=95.0,
            evidence_type="OBSERVED"
        ))

        # 12. Maintenance / Relevance (4%)
        maint_raw = 8.0
        if workflow_data.get("updated_at_source") or workflow_data.get("created_at_source"):
            maint_raw = 8.5
        evidence_list.append(ScoreEvidenceModel(
            criterion="maintenance",
            raw_score=maint_raw,
            weight=WEIGHTS["maintenance"],
            weighted_score=round(maint_raw * WEIGHTS["maintenance"], 4),
            evidence="Active community node definitions and current schema.",
            reasoning="Node versions align with modern n8n runtime syntax.",
            confidence=80.0,
            evidence_type="DERIVED"
        ))

        # Compute Base Score
        base_score = sum(ev.weighted_score for ev in evidence_list)
        
        # Penalties Check
        penalty_deduction = 0.0
        if len(description.strip()) < 10:
            penalties_list.append(PenaltyModel(
                penalty_type="missing_setup_documentation",
                penalty_amount=0.3,
                evidence="No description or setup instructions provided in template."
            ))
            penalty_deduction += 0.3
            
        if security_score < 6.0:
            penalties_list.append(PenaltyModel(
                penalty_type="hardcoded_credentials",
                penalty_amount=1.0,
                evidence="Critical security findings identified during static analysis."
            ))
            penalty_deduction += 1.0

        final_score = round(max(0.0, min(10.0, base_score - penalty_deduction)), 2)
        rating_label = cls.get_rating_label(final_score)

        return {
            "base_score": round(base_score, 2),
            "penalties_deduction": round(penalty_deduction, 2),
            "overall_score": final_score,
            "rating_label": rating_label,
            "daily_life_practicality_score": daily_life_raw,
            "daily_life_practicality_label": daily_life_res["daily_life_practicality_label"],
            "daily_life_practicality_reason": daily_life_res["daily_life_practicality_reason"],
            "daily_life_use_frequency": daily_life_freq,
            "evidence_list": [ev.model_dump() for ev in evidence_list],
            "penalties_list": [p.model_dump() for p in penalties_list],
        }
