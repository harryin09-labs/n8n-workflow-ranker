"""
Value Score and Hidden Gem Scorer: Evaluates ROI and surfaces high-value overlooked templates.
"""

from typing import Dict, Any, Tuple


class ValueAndGemScorer:
    @staticmethod
    def calculate_value_score(
        overall_score: float,
        complexity_score: float,
        cost_class: str,
        node_count: int,
        views: int
    ) -> Tuple[float, str]:
        """
        Calculates Value Score (0.0 - 10.0) reflecting ROI and practical efficiency.
        """
        base_value = overall_score * 0.65
        
        # Cost efficiency bonus
        cost_bonus = 0.0
        if cost_class == "FREE":
            cost_bonus = 1.5
        elif cost_class == "MOSTLY_FREE":
            cost_bonus = 1.0
        elif cost_class == "LOW_COST":
            cost_bonus = 0.5
        elif cost_class == "EXPENSIVE":
            cost_bonus = -1.0
            
        # Complexity vs utility balance
        balance_bonus = 0.0
        if complexity_score <= 4.0 and overall_score >= 7.0:
            balance_bonus = 1.2  # High reward for low complexity / high score (quick win)
        elif complexity_score >= 8.0 and overall_score >= 8.5:
            balance_bonus = 1.0  # High reward for heavy enterprise powerhouses
            
        raw_val = base_value + cost_bonus + balance_bonus
        value_score = round(min(10.0, max(1.0, raw_val)), 2)
        
        reason = f"Derived from quality baseline ({overall_score:.1f}), {cost_class.lower().replace('_', ' ')} cost footprint (+{cost_bonus:.1f}), and architectural ROI balance (+{balance_bonus:.1f})."
        return value_score, reason

    @staticmethod
    def calculate_hidden_gem_score(
        overall_score: float,
        value_score: float,
        views: int,
        confidence_score: float
    ) -> float:
        """
        Calculates Hidden Gem Score (0.0 - 10.0).
        Rewards high quality, high value, verified confidence, and low discovery view count.
        """
        if overall_score < 7.0 or confidence_score < 40.0:
            return 0.0

        # View count penalty (fewer views = higher gem potential)
        if views < 200:
            view_factor = 2.5
        elif views < 800:
            view_factor = 2.0
        elif views < 2500:
            view_factor = 1.0
        elif views < 10000:
            view_factor = 0.3
        else:
            view_factor = 0.0  # Already viral/widely known

        gem_score = (overall_score * 0.5) + (value_score * 0.25) + view_factor
        return round(min(10.0, max(0.0, gem_score)), 2)
