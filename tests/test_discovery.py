"""
Tests for URL parsing and discovery mechanisms.
"""

from crawler.discovery_sources import parse_workflow_url, DiscoverySource


def test_parse_workflow_url():
    url1 = "https://n8n.io/workflows/1-insert-excel-data-to-postgres/"
    res1 = parse_workflow_url(url1)
    assert res1 is not None
    assert res1[0] == 1
    assert res1[1] == "insert-excel-data-to-postgres"
    assert res1[2] == "https://n8n.io/workflows/1-insert-excel-data-to-postgres/"

    url2 = "https://n8n.io/workflows/11807/"
    res2 = parse_workflow_url(url2)
    assert res2 is not None
    assert res2[0] == 11807
    assert res2[2] == "https://n8n.io/workflows/11807/"

    invalid = "https://n8n.io/integrations/slack/"
    assert parse_workflow_url(invalid) is None


def test_discovery_storage(test_db):
    ds = DiscoverySource()
    sample = [
        {"workflow_id": 101, "slug": "test-wf-101", "canonical_url": "https://n8n.io/workflows/101-test/", "discovery_source": "sitemap"},
        {"workflow_id": 102, "slug": "test-wf-102", "canonical_url": "https://n8n.io/workflows/102-test/", "discovery_source": "search_api"},
    ]
    inserted = ds.store_discovered(sample)
    assert inserted >= 2

    # Re-inserting should update without error
    inserted_again = ds.store_discovered(sample)
    assert inserted_again >= 2
