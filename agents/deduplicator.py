"""
Deduplicator Agent: Compares workflows across multiple layers to detect exact duplicates, near duplicates, and variants.
"""

import logging
from typing import List, Dict, Any, Tuple
from embeddings.similarity import DuplicateDetector
from database.db import get_db, fetch_all

logger = logging.getLogger(__name__)


class DeduplicatorAgent:
    def __init__(self):
        self.detector = DuplicateDetector()

    def scan_for_duplicates(self) -> List[Dict[str, Any]]:
        """
        Scans all active workflows in database and detects duplicate relationships.
        Persists findings in duplicates table.
        """
        logger.info("Running multi-layer duplicate detection across database workflows...")
        workflows = fetch_all(
            """
            SELECT workflow_id, title, description, content_hash, structure_hash,
                   node_count, overall_score
            FROM workflows
            ORDER BY workflow_id ASC
            """
        )

        # Hydrate nodes and integrations in 2 fast batch queries
        all_nodes = fetch_all("SELECT workflow_id, node_name, node_type, node_type_normalized FROM workflow_nodes")
        all_integrations = fetch_all("SELECT workflow_id, integration_name FROM workflow_integrations")

        nodes_by_wf = {}
        for n in all_nodes:
            nodes_by_wf.setdefault(n["workflow_id"], []).append(n)

        integs_by_wf = {}
        for i in all_integrations:
            integs_by_wf.setdefault(i["workflow_id"], []).append(i["integration_name"])

        hydrated = []
        for wf in workflows:
            wf_id = wf["workflow_id"]
            wf_copy = dict(wf)
            wf_copy["nodes"] = nodes_by_wf.get(wf_id, [])
            wf_copy["integrations"] = integs_by_wf.get(wf_id, [])
            hydrated.append(wf_copy)

        detected_duplicates = []
        
        with get_db() as conn:
            conn.execute("DELETE FROM duplicates")
            
            for i in range(len(hydrated)):
                for j in range(i + 1, len(hydrated)):
                    wf1 = hydrated[i]
                    wf2 = hydrated[j]
                    
                    dup_type, sim_score, reason = self.detector.compare_workflows(wf1, wf2)
                    
                    if dup_type in ("EXACT_DUPLICATE", "NEAR_DUPLICATE", "VARIANT") and sim_score >= 0.7:
                        # Determine canonical original vs duplicate (older id or higher views)
                        orig_id = min(wf1["workflow_id"], wf2["workflow_id"])
                        dup_id = max(wf1["workflow_id"], wf2["workflow_id"])
                        
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO duplicates (workflow_id, duplicate_of_id, duplicate_type, similarity_score, similarity_reason)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (dup_id, orig_id, dup_type, sim_score, reason)
                        )
                        detected_duplicates.append({
                            "workflow_id": dup_id,
                            "duplicate_of_id": orig_id,
                            "duplicate_type": dup_type,
                            "similarity_score": sim_score,
                            "reason": reason
                        })

        logger.info(f"Duplicate scan complete: detected {len(detected_duplicates)} duplicates/variants.")
        return detected_duplicates
