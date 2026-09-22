"""
Tests for 12-dimension scoring, daily-life practicality, problem solver, penalties, confidence, and duplicate detection.
"""

from scoring.score import ScoringEngine, WEIGHTS
from scoring.confidence import ConfidenceScorer
from scoring.ai_capability import AICapabilityScorer
from scoring.value_gem import ValueAndGemScorer
from analysis.daily_life import DailyLifePracticalityAnalyzer
from analysis.problem_solver import ProblemSolver
from embeddings.similarity import DuplicateDetector


def test_weights_sum_to_exact_100_percent():
    """Phase 32 requirement: Verify all overall scoring weights equal exactly 100%."""
    total_weight = sum(WEIGHTS.values())
    assert abs(total_weight - 1.0) < 1e-9, f"Weights must sum to exactly 1.0 (100%), got {total_weight}"
    assert len(WEIGHTS) == 12, f"Must have exactly 12 scoring criteria, got {len(WEIGHTS)}"
    assert WEIGHTS["daily_life_practicality"] == 0.15
    assert WEIGHTS["automation_value"] == 0.13
    assert WEIGHTS["practical_usefulness"] == 0.10
    assert WEIGHTS["design_quality"] == 0.10
    assert WEIGHTS["reliability"] == 0.10
    assert WEIGHTS["ease_of_setup"] == 0.10
    assert WEIGHTS["reusability"] == 0.08
    assert WEIGHTS["documentation"] == 0.05
    assert WEIGHTS["integration_quality"] == 0.05
    assert WEIGHTS["security"] == 0.05
    assert WEIGHTS["cost_efficiency"] == 0.05
    assert WEIGHTS["maintenance"] == 0.04


def test_daily_life_practicality_analyzer():
    """Test 7-dimension daily life practicality scoring."""
    wf = {
        "workflow_id": 1,
        "title": "AI Gmail Inbox Organizer",
        "description": "Automatically sorts and categorizes incoming Gmail emails into labels and generates daily digest.",
        "categories": ["Productivity", "Email"],
        "integrations": ["gmail", "slack", "openai"],
        "node_count": 6,
        "complexity": "INTERMEDIATE",
        "cost_class": "MOSTLY_FREE",
        "nodes": [
            {"is_trigger": True, "credentials_needed": "gmailOAuth2"},
            {"is_ai": True, "credentials_needed": "openAiApi"},
            {"is_ai": False, "credentials_needed": "slackApi"}
        ],
        "triggers": ["pollEmail"]
    }
    
    res = DailyLifePracticalityAnalyzer.analyze(wf)
    assert 0.0 <= res["daily_life_practicality_score"] <= 10.0
    assert res["daily_life_use_frequency"] in ["Daily", "Weekly", "Monthly", "Rarely", "Almost Never"]
    assert res["daily_life_practicality_label"] in [
        "Extremely Practical", "Highly Practical", "Very Practical", 
        "Practical", "Moderately Practical", "Limited Practicality", 
        "Low Practicality", "Very Low Practicality"
    ]
    assert len(res["detailed_breakdown"]) == 7
    for criterion in ["frequency_of_use", "problem_relevance", "time_saved", "potential_users", "ease_of_incorporation", "repetition_reduction", "outcome_importance"]:
        assert criterion in res["detailed_breakdown"]
        assert 0.0 <= res["detailed_breakdown"][criterion]["score"] <= 10.0


def test_problem_solver_generator():
    """Test mandatory 1-line Problem It Solves generator."""
    wf = {
        "workflow_id": 10,
        "title": "Automatically Save Gmail Invoices to Google Drive",
        "description": "Watches inbox for PDF invoice attachments and saves them to designated Drive folders.",
        "categories": ["Finance", "Productivity"],
        "integrations": ["gmail", "googledrive"],
        "node_count": 4,
        "nodes": [],
        "triggers": ["emailTrigger"]
    }
    
    problem = ProblemSolver.generate(wf)
    assert isinstance(problem, str)
    assert len(problem) > 10
    # Should be a single concise sentence
    assert "\n" not in problem
    assert problem.endswith(".")
    words = problem.split()
    assert 5 <= len(words) <= 40


def test_scoring_engine_12_dimensions():
    """Test 12-dimension deterministic scoring engine."""
    wf = {
        "workflow_id": 1,
        "title": "Insert Excel data to Postgres",
        "description": "Read XLS from file, convert to JSON, and insert into Postgres table.",
        "node_count": 3,
        "connection_count": 2,
        "integrations": ["postgres", "readBinaryFile", "spreadsheetFile"],
        "nodes": [
            {"node_type": "readBinaryFile", "is_trigger": False},
            {"node_type": "spreadsheetFile", "is_trigger": False},
            {"node_type": "postgres", "is_trigger": False, "credentials_needed": "postgres"},
        ],
        "cost_class": "FREE",
        "security_score": 10.0,
    }
    
    res = ScoringEngine.score_workflow(wf)
    assert 0.0 <= res["overall_score"] <= 10.0
    assert res["rating_label"] in ["Exceptional", "Excellent", "Very Good", "Good", "Average", "Below Average", "Poor"]
    assert len(res["evidence_list"]) == 12
    assert "daily_life_practicality_score" in res
    assert "daily_life_use_frequency" in res
    
    # Check all weights sum to 1.0
    total_weight = sum(e["weight"] for e in res["evidence_list"])
    assert round(total_weight, 4) == 1.0


def test_confidence_scorer():
    wf = {
        "canonical_url": "https://n8n.io/workflows/1/",
        "description": "Detailed setup steps: 1. Configure DB 2. Run workflow.",
        "nodes": [{"node_name": "N1"}, {"node_name": "N2"}],
        "connection_count": 2,
        "integrations": ["postgres"],
        "structure_hash": "abcdef123456",
    }
    conf, evidence = ConfidenceScorer.calculate(wf)
    assert conf >= 70.0
    assert len(evidence) >= 5


def test_ai_capability_scorer():
    # Non-AI workflow returns None
    non_ai_wf = {"nodes": [{"is_ai": False}]}
    score, reasons = AICapabilityScorer.evaluate(non_ai_wf)
    assert score is None

    # AI workflow returns score
    ai_wf = {"nodes": [{"is_ai": True, "node_type": "@n8n/n8n-nodes-langchain.agent"}]}
    score2, reasons2 = AICapabilityScorer.evaluate(ai_wf)
    assert score2 is not None
    assert score2 >= 4.0


def test_duplicate_detector():
    wf1 = {
        "workflow_id": 10,
        "title": "Send Slack alert on error",
        "description": "Sends message to Slack when error occurs",
        "content_hash": "hash_abc",
        "structure_hash": "struct_123",
        "integrations": ["slack"],
        "nodes": [{"node_type_clean": "slack"}]
    }
    # Exact duplicate
    dup_type, sim, reason = DuplicateDetector.compare_workflows(wf1, wf1)
    assert dup_type == "EXACT_DUPLICATE"
    assert sim == 1.0

    # Distinct workflow
    wf2 = {
        "workflow_id": 20,
        "title": "Postgres daily backup",
        "description": "Dumps database and saves to S3 bucket",
        "content_hash": "hash_xyz",
        "structure_hash": "struct_999",
        "integrations": ["postgres", "s3"],
        "nodes": [{"node_type_clean": "postgres"}, {"node_type_clean": "s3"}]
    }
    dup_type2, sim2, reason2 = DuplicateDetector.compare_workflows(wf1, wf2)
    assert dup_type2 == "UNIQUE"
    assert sim2 < 0.5
