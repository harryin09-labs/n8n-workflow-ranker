"""
Tests for extraction and normalization modules.
"""

from extraction.metadata import MetadataExtractor
from extraction.workflow_json import WorkflowJsonExtractor
from extraction.normalization import Normalizer


def test_metadata_extraction(sample_excel_postgres_workflow):
    meta = MetadataExtractor.extract_metadata(sample_excel_postgres_workflow)
    assert meta["workflow_id"] == 1
    assert meta["title"] == "Insert Excel data to Postgres"
    assert meta["creator_name"] == "Jan Oberhauser"
    assert meta["creator_verified"] is True
    assert "Engineering" in meta["categories"]
    assert meta["views"] == 13545
    assert meta["canonical_url"] == "https://n8n.io/workflows/1-insert-excel-data-to-postgres/"


def test_workflow_graph_extraction(sample_ai_rag_workflow):
    graph = WorkflowJsonExtractor.extract_graph(sample_ai_rag_workflow)
    assert graph["node_count"] == 5
    assert graph["connection_count"] >= 4
    assert graph["ai_nodes_count"] >= 2
    assert "telegram" in [i.lower() for i in graph["integrations"]]
    assert len(graph["credentials_required"]) >= 2


def test_normalization(sample_excel_postgres_workflow, sample_ai_rag_workflow):
    norm = Normalizer()
    
    assert norm.normalize_node_type("n8n-nodes-base.httpRequest") == "http_request"
    assert norm.normalize_node_type("@n8n/n8n-nodes-langchain.agent") == "agent"
    assert norm.normalize_integration_name("googlesheets") == "Google Sheets"
    assert norm.normalize_category("Artificial Intelligence") == "AI"

    h1 = norm.compute_content_hash(sample_excel_postgres_workflow)
    h2 = norm.compute_content_hash(sample_excel_postgres_workflow)
    assert h1 == h2
    assert len(h1) == 64
