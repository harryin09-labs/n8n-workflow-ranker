"""
Analyst Agent: Executes multi-dimensional workflow analysis including complexity, cost, security, usefulness, and AI capability.
"""

import json
import logging
from typing import Dict, Any, Optional
from analysis.complexity import ComplexityClassifier
from analysis.cost import CostClassifier
from analysis.security import SecurityAnalyzer
from analysis.usefulness import UsefulnessAnalyzer
from analysis.daily_life import DailyLifePracticalityAnalyzer
from analysis.problem_solver import ProblemSolver
from scoring.confidence import ConfidenceScorer
from scoring.ai_capability import AICapabilityScorer
from scoring.value_gem import ValueAndGemScorer
from database.db import get_db, execute_query, fetch_one

logger = logging.getLogger(__name__)


class AnalystAgent:
    def __init__(self):
        self.complexity_classifier = ComplexityClassifier()
        self.cost_classifier = CostClassifier()
        self.security_analyzer = SecurityAnalyzer()
        self.usefulness_analyzer = UsefulnessAnalyzer()
        self.daily_life_analyzer = DailyLifePracticalityAnalyzer()
        self.problem_solver = ProblemSolver()
        self.confidence_scorer = ConfidenceScorer()
        self.ai_scorer = AICapabilityScorer()
        self.value_gem_scorer = ValueAndGemScorer()

    def analyze_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs all analytical modules on a normalized workflow."""
        workflow_id = workflow_data["workflow_id"]
        logger.info(f"Analyzing workflow {workflow_id}: {workflow_data.get('title')}")

        # 1. Complexity Classification
        complexity, complexity_score, complexity_reason = self.complexity_classifier.classify(workflow_data)
        
        # 2. Cost Classification
        cost_class, paid_deps, free_deps, cost_notes = self.cost_classifier.classify(workflow_data)
        
        # 3. Security Analysis
        security_score, risk_level, security_findings = self.security_analyzer.analyze(workflow_data)
        
        # 4. Usefulness Analysis
        usefulness_data = self.usefulness_analyzer.analyze(workflow_data)
        
        # 5. Daily-Life Practicality Analysis
        daily_life_data = self.daily_life_analyzer.analyze(workflow_data)
        
        # 6. Problem It Solves Generation
        problem_it_solves = self.problem_solver.generate(workflow_data)
        
        # 7. Confidence Scoring
        confidence_score, confidence_reasons = self.confidence_scorer.calculate(workflow_data)
        
        # 8. AI Capability Scoring
        ai_score, ai_reasons = self.ai_scorer.evaluate(workflow_data)
        
        # Merge findings into workflow payload
        workflow_data["complexity"] = complexity
        workflow_data["complexity_score"] = complexity_score
        workflow_data["complexity_reason"] = complexity_reason
        
        workflow_data["cost_class"] = cost_class
        workflow_data["paid_dependencies"] = paid_deps
        workflow_data["free_dependencies"] = free_deps
        workflow_data["cost_notes"] = cost_notes
        
        workflow_data["security_score"] = security_score
        workflow_data["security_risk_level"] = risk_level
        workflow_data["security_findings"] = security_findings
        
        workflow_data["confidence_score"] = confidence_score
        workflow_data["ai_score"] = ai_score
        workflow_data["primary_domain"] = usefulness_data["primary_domain"]
        workflow_data["automation_level"] = usefulness_data["automation_level"]
        workflow_data["estimated_time_saved"] = usefulness_data["estimated_time_saved"]
        
        # Daily-Life Practicality
        workflow_data["daily_life_practicality_score"] = daily_life_data["daily_life_practicality_score"]
        workflow_data["daily_life_practicality_label"] = daily_life_data["daily_life_practicality_label"]
        workflow_data["daily_life_practicality_reason"] = daily_life_data["daily_life_practicality_reason"]
        workflow_data["daily_life_use_frequency"] = daily_life_data["daily_life_use_frequency"]
        
        # Problem It Solves
        workflow_data["problem_it_solves"] = problem_it_solves

        return workflow_data
