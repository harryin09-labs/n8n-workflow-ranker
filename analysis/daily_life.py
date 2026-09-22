"""
Daily-Life Practicality Analyzer: Evaluates how useful a workflow is in genuine everyday personal/professional life.

Scoring Criteria (7 dimensions, each contributing to a 0-10 score):

1. Frequency of Use (0-10): How often could a normal user realistically benefit?
   - 10 = Daily or multiple times/week
   - 7 = Weekly
   - 5 = Monthly
   - 2 = Rarely needed
   - 0 = Almost no realistic recurring use

2. Real-World Problem Relevance (0-10): Does it solve a common genuine problem?
   High scores for: email management, scheduling, reminders, document handling, 
   communication, customer service, data entry, reporting, file organization, 
   task management, finance, sales, content handling, repetitive office work.

3. Time Saved (0-10): Estimate manual time automation can realistically save per use.
   - 10 = Saves hours per use
   - 7 = Saves 30-60 minutes per use
   - 5 = Saves 10-30 minutes per use
   - 3 = Saves a few minutes per use
   - 1 = Negligible time savings

4. Number of Potential Users (0-10): How broadly applicable is the problem?
   - 10 = Most users / universal problem
   - 7 = Many businesses / professionals
   - 5 = Specific professions
   - 3 = Narrow niche
   - 1 = Very unusual scenarios

5. Ease of Incorporation (0-10): Can user fit it into existing routine?
   - 10 = Zero setup, fits immediately
   - 7 = Simple setup, low maintenance
   - 5 = Moderate setup/credentials needed
   - 3 = Complex setup, ongoing maintenance
   - 1 = Requires deep technical expertise

6. Repetition Reduction (0-10): Does it remove repetitive manual activity?
   - 10 = Eliminates highly repetitive daily tasks
   - 7 = Reduces weekly repetitive work
   - 5 = Reduces monthly repetitive work
   - 3 = One-time or occasional task
   - 1 = Not repetitive

7. Outcome Importance (0-10): Actual benefit significance
   - 10 = Critical: revenue, compliance, customer experience
   - 7 = High: productivity, reduced errors, faster response
   - 5 = Moderate: convenience, better organization
   - 3 = Low: minor convenience
   - 1 = Negligible benefit
"""

from typing import Dict, Any, List, Tuple
import re


class DailyLifePracticalityAnalyzer:
    """Evaluates the daily-life practicality of a workflow across 7 criteria."""
    
    # Problem categories that indicate high practical relevance
    HIGH_RELEVANCE_KEYWORDS = {
        "email", "inbox", "gmail", "outlook", "mail",
        "schedule", "calendar", "appointment", "booking", "meeting",
        "remind", "notification", "alert", "task", "todo",
        "document", "pdf", "invoice", "receipt", "contract", "file",
        "spreadsheet", "sheet", "excel", "data entry", "copy", "paste",
        "report", "dashboard", "analytics", "metric", "kpi",
        "customer", "support", "ticket", "zendesk", "intercom", "helpdesk",
        "sales", "lead", "crm", "hubspot", "deal", "pipeline",
        "marketing", "social", "post", "tweet", "instagram", "linkedin", "content",
        "finance", "expense", "budget", "payment", "invoice", "accounting",
        "backup", "sync", "transfer", "migrate", "archive",
        "organize", "sort", "filter", "categorize", "classify",
        "automation", "workflow", "process", "pipeline"
    }
    
    # Integration patterns indicating high daily use
    DAILY_USE_INTEGRATIONS = {
        "gmail", "outlook", "email", "calendar", "googlecalendar",
        "slack", "teams", "discord", "telegram", "whatsapp",
        "googlesheets", "excel", "spreadsheet", "airtable", "notion",
        "drive", "dropbox", "onedrive", "box",
        "github", "gitlab", "jira", "linear", "trello", "asana",
        "webhook", "http", "api", "database", "postgres", "mysql",
        "salesforce", "hubspot", "pipedrive", "zendesk", "freshdesk"
    }
    
    @staticmethod
    def calculate_frequency_score(workflow_data: Dict[str, Any]) -> Tuple[float, str]:
        """Criterion 1: Frequency of Use (0-10)"""
        title = workflow_data.get("title", "").lower()
        description = workflow_data.get("description", "").lower()
        categories = [c.lower() for c in workflow_data.get("categories", [])]
        integrations = [i.lower() for i in workflow_data.get("integrations", [])]
        node_count = workflow_data.get("node_count", 0)
        
        text = f"{title} {description} {' '.join(categories)} {' '.join(integrations)}"
        
        # High frequency indicators
        daily_indicators = ["email", "inbox", "slack", "telegram", "discord", "message", 
                           "chat", "notification", "alert", "remind", "schedule", 
                           "calendar", "meeting", "task", "todo", "sync", "backup",
                           "monitor", "watch", "daily", "hourly", "real-time"]
        
        weekly_indicators = ["report", "weekly", "summary", "digest", "analytics", 
                            "kpi", "metric", "pipeline", "lead", "customer", "support"]
        
        monthly_indicators = ["invoice", "expense", "budget", "payroll", "monthly", 
                             "quarterly", "tax", "compliance", "audit"]
        
        score = 2.0  # Base score
        freq = "Rarely"
        
        if any(ind in text for ind in daily_indicators):
            score = 9.0
            freq = "Daily"
        elif any(ind in text for ind in weekly_indicators):
            score = 7.0
            freq = "Weekly"
        elif any(ind in text for ind in monthly_indicators):
            score = 5.0
            freq = "Monthly"
        elif node_count >= 4 and len(integrations) >= 2:
            score = 5.0
            freq = "Monthly"
        else:
            score = 2.0
            freq = "Rarely"
            
        reason = f"Frequency indicators found: {freq.lower()} use pattern"
        return score, reason, freq
    
    @staticmethod
    def calculate_problem_relevance_score(workflow_data: Dict[str, Any]) -> Tuple[float, str]:
        """Criterion 2: Real-World Problem Relevance (0-10)"""
        title = workflow_data.get("title", "").lower()
        description = workflow_data.get("description", "").lower()
        categories = [c.lower() for c in workflow_data.get("categories", [])]
        
        text = f"{title} {description} {' '.join(categories)}"
        
        matches = sum(1 for kw in DailyLifePracticalityAnalyzer.HIGH_RELEVANCE_KEYWORDS if kw in text)
        
        if matches >= 5:
            score = 9.5
        elif matches >= 3:
            score = 8.0
        elif matches >= 2:
            score = 6.5
        elif matches >= 1:
            score = 5.0
        else:
            score = 3.0
            
        reason = f"Matched {matches} high-relevance problem keywords"
        return score, reason
    
    @staticmethod
    def calculate_time_saved_score(workflow_data: Dict[str, Any]) -> Tuple[float, str]:
        """Criterion 3: Time Saved (0-10)"""
        node_count = workflow_data.get("node_count", 0)
        integrations = workflow_data.get("integrations", [])
        integration_count = len(integrations)
        description = workflow_data.get("description", "").lower()
        
        # Complex multi-step workflows save more time
        base_score = min(10.0, node_count * 1.2)
        
        # Multi-integration workflows eliminate context switching
        if integration_count >= 3:
            base_score += 1.5
        elif integration_count >= 2:
            base_score += 1.0
            
        # Specific high-time-saving patterns
        time_saving_keywords = ["bulk", "batch", "mass", "auto", "schedule", 
                               "recurring", "repetitive", "manual", "copy", "paste",
                               "download", "upload", "transfer", "migrate", "sync"]
        
        if any(kw in description for kw in time_saving_keywords):
            base_score += 1.0
            
        score = round(min(10.0, max(1.0, base_score)), 1)
        reason = f"Estimated time savings from {node_count} nodes across {integration_count} integrations"
        return score, reason
    
    @staticmethod
    def calculate_potential_users_score(workflow_data: Dict[str, Any]) -> Tuple[float, str]:
        """Criterion 4: Number of Potential Users (0-10)"""
        categories = [c.lower() for c in workflow_data.get("categories", [])]
        integrations = [i.lower() for i in workflow_data.get("integrations", [])]
        
        # Universal integrations
        universal_integrations = {"gmail", "email", "calendar", "slack", "teams", 
                                 "googlesheets", "excel", "drive", "dropbox"}
        
        universal_count = sum(1 for i in integrations if any(u in i for u in universal_integrations))
        
        # Business categories with broad appeal
        broad_categories = {"productivity", "automation", "communication", "marketing", 
                           "sales", "finance", "hr", "operations", "engineering"}
        
        broad_count = sum(1 for c in categories if any(b in c for b in broad_categories))
        
        if universal_count >= 2 or broad_count >= 2:
            score = 9.0
            reason = "Applicable to most knowledge workers and businesses"
        elif universal_count >= 1 or broad_count >= 1:
            score = 7.0
            reason = "Applicable to many professionals in common roles"
        elif len(categories) > 0:
            score = 5.0
            reason = f"Specific to {len(categories)} business domain(s)"
        else:
            score = 3.0
            reason = "Niche or specialized use case"
            
        return score, reason
    
    @staticmethod
    def calculate_ease_of_incorporation_score(workflow_data: Dict[str, Any]) -> Tuple[float, str]:
        """Criterion 5: Ease of Incorporation Into Normal Life (0-10)"""
        node_count = workflow_data.get("node_count", 0)
        credentials_needed = sum(1 for n in workflow_data.get("nodes", []) 
                                 if n.get("credentials_needed"))
        complexity = workflow_data.get("complexity", "INTERMEDIATE")
        has_code = any(n.get("is_code") for n in workflow_data.get("nodes", []))
        has_ai = any(n.get("is_ai") for n in workflow_data.get("nodes", []))
        cost_class = workflow_data.get("cost_class", "FREE")
        
        score = 10.0
        
        # Node count penalty
        if node_count > 15:
            score -= 3.0
        elif node_count > 10:
            score -= 2.0
        elif node_count > 7:
            score -= 1.0
            
        # Credential complexity
        if credentials_needed > 4:
            score -= 2.5
        elif credentials_needed > 2:
            score -= 1.5
        elif credentials_needed > 0:
            score -= 0.5
            
        # Complexity tier
        complexity_penalty = {"BEGINNER": 0, "INTERMEDIATE": 0.5, "ADVANCED": 1.5, "EXPERT": 3.0}
        score -= complexity_penalty.get(complexity, 1.0)
        
        # Technical barriers
        if has_code:
            score -= 1.5
        if has_ai:
            score -= 1.0
        if cost_class in ("PAID", "EXPENSIVE"):
            score -= 1.0
            
        score = round(max(1.0, min(10.0, score)), 1)
        
        if score >= 8.5:
            reason = "Zero/minimal setup, fits immediately into existing workflow"
        elif score >= 6.5:
            reason = "Simple setup with standard credentials"
        elif score >= 4.5:
            reason = "Moderate setup requiring some technical knowledge"
        else:
            reason = "Complex setup requiring significant technical expertise"
            
        return score, reason
    
    @staticmethod
    def calculate_repetition_reduction_score(workflow_data: Dict[str, Any]) -> Tuple[float, str]:
        """Criterion 6: Repetition Reduction (0-10)"""
        description = workflow_data.get("description", "").lower()
        title = workflow_data.get("title", "").lower()
        text = f"{title} {description}"
        node_count = workflow_data.get("node_count", 0)
        
        repetitive_keywords = ["auto", "schedule", "recurring", "batch", "bulk", "loop",
                              "repeat", "periodic", "cron", "daily", "hourly", "interval",
                              "monitor", "watch", "poll", "sync", "backup", "archive"]
        
        manual_keywords = ["manual", "copy", "paste", "download", "upload", "transfer",
                          "export", "import", "enter", "type", "fill", "click", "navigate"]
        
        repetitive_score = sum(1 for kw in repetitive_keywords if kw in text)
        manual_score = sum(1 for kw in manual_keywords if kw in text)
        
        # High repetition if workflow has automation triggers and repetitive keywords
        triggers = workflow_data.get("triggers", [])
        has_auto_trigger = any("webhook" in t.lower() or "schedule" in t.lower() 
                              or "poll" in t.lower() for t in triggers)
        
        score = 3.0
        if has_auto_trigger and (repetitive_score >= 2 or manual_score >= 2):
            score = 9.0
        elif has_auto_trigger and (repetitive_score >= 1 or manual_score >= 1):
            score = 7.5
        elif repetitive_score >= 2 or manual_score >= 2:
            score = 7.0
        elif repetitive_score >= 1 or manual_score >= 1:
            score = 5.5
        elif node_count >= 3:
            score = 5.0
        else:
            score = 2.0
            
        reason = f"Repetition indicators: {repetitive_score} auto, {manual_score} manual reduction keywords"
        return score, reason
    
    @staticmethod
    def calculate_outcome_importance_score(workflow_data: Dict[str, Any]) -> Tuple[float, str]:
        """Criterion 7: Outcome Importance (0-10)"""
        title = workflow_data.get("title", "").lower()
        description = workflow_data.get("description", "").lower()
        categories = [c.lower() for c in workflow_data.get("categories", [])]
        integrations = [i.lower() for i in workflow_data.get("integrations", [])]
        text = f"{title} {description} {' '.join(categories)} {' '.join(integrations)}"
        
        # Critical outcomes
        critical = ["revenue", "sales", "customer", "compliance", "security", "legal",
                   "audit", "payment", "billing", "invoice", "contract", "deal"]
        
        # High value outcomes
        high = ["productivity", "error", "mistake", "missed", "response time", "sla",
               "organization", "efficiency", "automation", "scale", "growth"]
        
        # Moderate outcomes
        moderate = ["convenience", "organize", "sort", "filter", "format", "cleanup",
                   "backup", "archive", "report", "dashboard", "insight"]
        
        if any(kw in text for kw in critical):
            score = 9.5
            tier = "Critical business impact"
        elif any(kw in text for kw in high):
            score = 7.5
            tier = "High productivity/error reduction value"
        elif any(kw in text for kw in moderate):
            score = 5.5
            tier = "Moderate convenience/organization benefit"
        else:
            score = 3.0
            tier = "Low tangible outcome"
            
        reason = f"Outcome tier: {tier}"
        return score, reason
    
    @classmethod
    def analyze(cls, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all 7 criteria and compute weighted daily-life practicality score.
        Each criterion weighted equally (1/7 ≈ 14.3% each).
        """
        results = {}
        
        # Criterion 1: Frequency of Use
        freq_score, freq_reason, use_freq = cls.calculate_frequency_score(workflow_data)
        results["frequency_of_use"] = {
            "score": freq_score,
            "reason": freq_reason,
            "use_frequency": use_freq
        }
        
        # Criterion 2: Real-World Problem Relevance
        prob_score, prob_reason = cls.calculate_problem_relevance_score(workflow_data)
        results["problem_relevance"] = {
            "score": prob_score,
            "reason": prob_reason
        }
        
        # Criterion 3: Time Saved
        time_score, time_reason = cls.calculate_time_saved_score(workflow_data)
        results["time_saved"] = {
            "score": time_score,
            "reason": time_reason
        }
        
        # Criterion 4: Potential Users
        users_score, users_reason = cls.calculate_potential_users_score(workflow_data)
        results["potential_users"] = {
            "score": users_score,
            "reason": users_reason
        }
        
        # Criterion 5: Ease of Incorporation
        ease_score, ease_reason = cls.calculate_ease_of_incorporation_score(workflow_data)
        results["ease_of_incorporation"] = {
            "score": ease_score,
            "reason": ease_reason
        }
        
        # Criterion 6: Repetition Reduction
        rep_score, rep_reason = cls.calculate_repetition_reduction_score(workflow_data)
        results["repetition_reduction"] = {
            "score": rep_score,
            "reason": rep_reason
        }
        
        # Criterion 7: Outcome Importance
        outcome_score, outcome_reason = cls.calculate_outcome_importance_score(workflow_data)
        results["outcome_importance"] = {
            "score": outcome_score,
            "reason": outcome_reason
        }
        
        # Overall weighted average (equal weights = 1/7 each)
        total_score = sum(r["score"] for r in results.values()) / 7.0
        overall_score = round(min(10.0, max(0.0, total_score)), 2)
        
        # Label mapping
        if overall_score >= 9.0:
            label = "Extremely Practical"
        elif overall_score >= 8.0:
            label = "Highly Practical"
        elif overall_score >= 7.0:
            label = "Very Practical"
        elif overall_score >= 6.0:
            label = "Practical"
        elif overall_score >= 5.0:
            label = "Moderately Practical"
        elif overall_score >= 4.0:
            label = "Limited Practicality"
        elif overall_score >= 2.0:
            label = "Low Practicality"
        else:
            label = "Very Low Practicality"
            
        # Overall reason summary
        overall_reason = (
            f"Daily frequency: {results['frequency_of_use']['use_frequency']}; "
            f"Problem relevance: {prob_score:.1f}/10; "
            f"Time saved: {time_score:.1f}/10; "
            f"Ease of adoption: {ease_score:.1f}/10; "
            f"Outcome importance: {outcome_score:.1f}/10"
        )
        
        return {
            "daily_life_practicality_score": overall_score,
            "daily_life_practicality_label": label,
            "daily_life_practicality_reason": overall_reason,
            "daily_life_use_frequency": results["frequency_of_use"]["use_frequency"],
            "detailed_breakdown": results
        }


# Standalone test
if __name__ == "__main__":
    # Test with sample workflow
    test_workflow = {
        "workflow_id": 1,
        "title": "Insert Excel data to Postgres",
        "description": "1. Read XLS from file\n2. Convert it to JSON\n3. Insert it in Postgres",
        "categories": ["Engineering"],
        "integrations": ["spreadsheetFile", "postgres"],
        "node_count": 3,
        "complexity": "BEGINNER",
        "cost_class": "FREE",
        "nodes": [
            {"credentials_needed": None},
            {"credentials_needed": None},
            {"credentials_needed": "postgres"}
        ],
        "triggers": []
    }
    
    result = DailyLifePracticalityAnalyzer.analyze(test_workflow)
    print(f"Daily-Life Practicality Score: {result['daily_life_practicality_score']}/10")
    print(f"Label: {result['daily_life_practicality_label']}")
    print(f"Frequency: {result['daily_life_use_frequency']}")
    print(f"Reason: {result['daily_life_practicality_reason']}")
    print("\nDetailed breakdown:")
    for criterion, details in result["detailed_breakdown"].items():
        print(f"  {criterion}: {details['score']}/10 - {details['reason']}")