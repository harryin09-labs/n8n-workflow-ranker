"""
Tests for analysis modules: complexity, cost, security, and usefulness.
"""

from analysis.complexity import ComplexityClassifier
from analysis.cost import CostClassifier
from analysis.security import SecurityAnalyzer
from analysis.usefulness import UsefulnessAnalyzer
from extraction.workflow_json import WorkflowJsonExtractor


def test_complexity_classification(sample_excel_postgres_workflow, sample_ai_rag_workflow):
    # 1. Simple 3-node workflow
    graph1 = WorkflowJsonExtractor.extract_graph(sample_excel_postgres_workflow)
    wf_data1 = {"nodes": graph1["nodes"], "integrations": graph1["integrations"]}
    comp1, score1, reason1 = ComplexityClassifier.classify(wf_data1)
    assert comp1 in ("BEGINNER", "INTERMEDIATE")
    assert score1 <= 6.0

    # 2. AI RAG Agent workflow
    graph2 = WorkflowJsonExtractor.extract_graph(sample_ai_rag_workflow)
    wf_data2 = {"nodes": graph2["nodes"], "integrations": graph2["integrations"]}
    comp2, score2, reason2 = ComplexityClassifier.classify(wf_data2)
    assert score2 > score1
    assert "AI" in reason2


def test_cost_classification(sample_excel_postgres_workflow, sample_ai_rag_workflow):
    graph1 = WorkflowJsonExtractor.extract_graph(sample_excel_postgres_workflow)
    wf_data1 = {"nodes": graph1["nodes"], "integrations": graph1["integrations"]}
    cost1, paid1, free1, notes1 = CostClassifier.classify(wf_data1)
    assert cost1 == "FREE"
    assert len(paid1) == 0

    graph2 = WorkflowJsonExtractor.extract_graph(sample_ai_rag_workflow)
    wf_data2 = {"nodes": graph2["nodes"], "integrations": graph2["integrations"]}
    cost2, paid2, free2, notes2 = CostClassifier.classify(wf_data2)
    assert cost2 in ("LOW_COST", "MOSTLY_FREE", "PAID")
    assert any("OpenAI" in p for p in paid2)


def test_security_analysis_clean(sample_excel_postgres_workflow):
    graph = WorkflowJsonExtractor.extract_graph(sample_excel_postgres_workflow)
    sec_score, risk, findings = SecurityAnalyzer.analyze({"nodes": graph["nodes"]})
    assert sec_score >= 9.0
    assert risk == "LOW"


def test_security_analysis_hardcoded_key():
    insecure_wf = {
        "nodes": [
            {
                "node_name": "Insecure Request",
                "node_type": "n8n-nodes-base.httpRequest",
                "parameters": {"headerParameters": {"Authorization": "Bearer sk-1234567890abcdef1234567890abcdef"}}
            }
        ]
    }
    sec_score, risk, findings = SecurityAnalyzer.analyze(insecure_wf)
    assert sec_score < 8.0
    assert len(findings) > 0
    assert findings[0]["finding_type"] == "HARDCODED_SECRET"
