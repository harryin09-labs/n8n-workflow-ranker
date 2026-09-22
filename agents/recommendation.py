"""
Recommendation Engine: Answers natural language and structured automation queries backed by actual evidence.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from database.db import fetch_all, fetch_one

logger = logging.getLogger(__name__)


class RecommendationEngine:
    @staticmethod
    def parse_query_intent(query: str) -> Dict[str, Any]:
        """Extract search criteria, constraints, and preferences from natural language query."""
        q_lower = query.lower()
        
        intent = {
            "require_free": bool(re.search(r"\b(free|no cost|no paid|zero cost)\b", q_lower)),
            "require_ai": bool(re.search(r"\b(ai|agent|rag|llm|gpt|chat|bot)\b", q_lower)),
            "require_self_hosted": bool(re.search(r"\b(self-hosted|self hosted|local|privacy|ollama)\b", q_lower)),
            "prefer_daily_life": bool(re.search(r"\b(daily|everyday|routine|practical|frequent|normal life)\b", q_lower)),
            "complexity_preference": None,
            "target_integrations": [],
            "excluded_integrations": [],
            "keywords": [],
        }

        # Complexity preference
        if re.search(r"\b(beginner|simple|easy|starter|first|quick win)\b", q_lower):
            intent["complexity_preference"] = "BEGINNER"
        elif re.search(r"\b(advanced|complex|enterprise)\b", q_lower):
            intent["complexity_preference"] = "ADVANCED"

        # Check for integrations mentioned
        common_integrations = [
            "telegram", "slack", "discord", "gmail", "sheets", "googlesheets",
            "postgres", "mysql", "mongodb", "redis", "supabase", "airtable",
            "openai", "anthropic", "gemini", "ollama", "pinecone", "qdrant",
            "hubspot", "salesforce", "notion", "github", "jira", "drive", "dropbox"
        ]

        # Check for exclusions ("without openai", "no openai")
        exclude_match = re.findall(r"\b(?:without|no|excluding)\s+([a-zA-Z0-9]+)\b", q_lower)
        for excl in exclude_match:
            for integ in common_integrations:
                if integ in excl or excl in integ:
                    intent["excluded_integrations"].append(integ)

        for integ in common_integrations:
            if integ in q_lower and integ not in intent["excluded_integrations"]:
                intent["target_integrations"].append(integ)

        # General keywords
        words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', q_lower)
        stop_words = {"what", "the", "best", "for", "with", "and", "workflow", "n8n", "without", "from", "use"}
        intent["keywords"] = [w for w in words if w not in stop_words and w not in intent["target_integrations"]]

        return intent

    def recommend(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Evaluates query, queries database with multi-factor scoring, and formats evidence-based recommendations.
        """
        intent = self.parse_query_intent(query)
        logger.info(f"Parsed intent for query '{query}': {intent}")

        # Fetch candidate workflows
        sql = """
            SELECT w.workflow_id, w.title, w.canonical_url, w.creator_name,
                   w.problem_it_solves, w.node_count, w.connection_count, w.complexity, w.cost_class,
                   w.overall_score, w.rating_label, w.confidence_score, w.ai_score,
                   w.security_score, w.security_risk_level, w.value_score,
                   w.daily_life_practicality_score, w.daily_life_practicality_label,
                   w.daily_life_use_frequency, w.paid_dependencies, w.free_dependencies, w.cost_notes,
                   w.description, w.views
            FROM workflows w
            WHERE w.status = 'active'
        """
        params = []

        if intent["require_free"]:
            sql += " AND w.cost_class IN ('FREE', 'MOSTLY_FREE')"

        if intent["complexity_preference"]:
            sql += " AND w.complexity = ?"
            params.append(intent["complexity_preference"])

        if intent["prefer_daily_life"]:
            sql += " ORDER BY w.daily_life_practicality_score DESC, w.overall_score DESC"
        else:
            sql += " ORDER BY w.overall_score DESC, w.confidence_score DESC"

        candidates = fetch_all(sql, tuple(params))
        
        # Score and filter candidates based on integrations and keywords
        scored_candidates = []
        for c in candidates:
            wf_id = c["workflow_id"]
            # Fetch integrations
            integ_rows = fetch_all("SELECT integration_normalized FROM workflow_integrations WHERE workflow_id = ?", (wf_id,))
            integrations = [r["integration_normalized"].lower() for r in integ_rows]
            
            # Check exclusions
            if any(excl in " ".join(integrations) for excl in intent["excluded_integrations"]):
                continue

            match_points = 0.0
            why_points = []

            # Check target integrations
            if intent["target_integrations"]:
                matched_integs = [t for t in intent["target_integrations"] if any(t in i for i in integrations)]
                if matched_integs:
                    match_points += len(matched_integs) * 35.0
                    why_points.append(f"Includes requested integration(s): {', '.join(matched_integs).title()}")
                else:
                    match_points -= 40.0

            # Check AI requirement
            if intent["require_ai"]:
                if c["ai_score"] is not None:
                    match_points += 25.0
                    why_points.append(f"Autonomous AI agent/LLM architecture (AI Score: {c['ai_score']:.1f}/10)")
                else:
                    match_points -= 20.0

            # Check Daily Life preference
            if intent["prefer_daily_life"]:
                daily_score = c.get("daily_life_practicality_score") or 0.0
                match_points += (daily_score * 8.0)
                if daily_score >= 8.0:
                    why_points.append(f"High everyday practicality ({daily_score:.1f}/10, {c.get('daily_life_use_frequency')} frequency)")

            # Check keywords in title/description/problem_it_solves
            full_text = f"{c['title']} {c.get('problem_it_solves') or ''} {c.get('description') or ''}".lower()
            for kw in intent["keywords"]:
                if kw in full_text:
                    match_points += 12.0
                    why_points.append(f"Direct match for keyword '{kw}'")

            # Overall quality baseline
            match_points += (c["overall_score"] * 10.0)

            # Strengths & Weaknesses
            strengths = []
            weaknesses = []
            
            if (c.get("daily_life_practicality_score") or 0.0) >= 8.0:
                strengths.append(f"High daily usefulness ({c.get('daily_life_practicality_score'):.1f}/10 - {c.get('daily_life_use_frequency')})")
            if c["overall_score"] >= 8.0:
                strengths.append(f"Strong overall quality score ({c['overall_score']:.2f}/10)")
            if c["cost_class"] == "FREE":
                strengths.append("100% free with zero recurring API costs")
            if c["security_score"] >= 9.0:
                strengths.append("Strong static security posture")
            if c["complexity"] == "BEGINNER":
                strengths.append("Quick setup and beginner friendly")
                
            if c["cost_class"] in ("PAID", "EXPENSIVE"):
                weaknesses.append(f"Requires paid subscription/APIs: {c['cost_notes']}")
            if c["confidence_score"] < 50.0:
                weaknesses.append("Lower documentation depth")
            if c["security_risk_level"] in ("HIGH", "CRITICAL"):
                weaknesses.append(f"Security risk: {c['security_risk_level']} detected")

            if not strengths:
                strengths.append("Standard tested n8n template")
            if not weaknesses:
                weaknesses.append("None identified under standard operating parameters")

            # Why recommended reasoning
            if not why_points:
                why_points.append(f"Top-scoring template ({c['overall_score']:.2f}/10) in this category")

            scored_candidates.append({
                "workflow_id": c["workflow_id"],
                "workflow_name": c["title"],
                "problem_it_solves": c.get("problem_it_solves") or f"Automates {c['title']} to eliminate manual effort.",
                "overall_score": round(c["overall_score"], 2),
                "daily_life_practicality_score": round(c.get("daily_life_practicality_score") or 0.0, 1),
                "daily_life_use_frequency": c.get("daily_life_use_frequency") or "Weekly",
                "rating_label": c["rating_label"],
                "confidence": round(c["confidence_score"], 1),
                "cost": c["cost_class"],
                "complexity": c["complexity"],
                "integrations": [i.title() for i in integrations],
                "strengths": strengths,
                "weaknesses": weaknesses,
                "why_recommended": "; ".join(why_points),
                "original_url": c["canonical_url"],
                "_match_score": match_points,
            })

        # Sort by match score
        scored_candidates.sort(key=lambda x: x["_match_score"], reverse=True)
        
        # Clean internal match score
        results = []
        for item in scored_candidates[:limit]:
            del item["_match_score"]
            results.append(item)

        return results


if __name__ == "__main__":
    import argparse
    from database.db import init_db

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Workflow Recommendation Engine")
    parser.add_argument("query", nargs="?", default="Best daily-life automations", help="Natural language query")
    parser.add_argument("--limit", type=int, default=5, help="Number of recommendations (default: 5)")
    args = parser.parse_args()

    init_db()
    engine = RecommendationEngine()
    recs = engine.recommend(args.query, limit=args.limit)
    print(f"\nRecommendations for: \"{args.query}\"\n" + "="*60)
    for i, r in enumerate(recs, 1):
        print(f"#{i} {r['workflow_name']}")
        print(f"   Problem It Solves: {r['problem_it_solves']}")
        print(f"   Overall Score: {r['overall_score']}/10 ({r['rating_label']}) | Daily-Life: {r['daily_life_practicality_score']}/10 ({r['daily_life_use_frequency']})")
        print(f"   Cost: {r['cost']} | Complexity: {r['complexity']} | Confidence: {r['confidence']}%")
        print(f"   Why: {r['why_recommended']}")
        print(f"   URL: {r['original_url']}\n")
