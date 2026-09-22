"""
Extractor Agent: Extracts metadata and graph data from raw crawled payloads, normalizes, and stores in database.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from extraction import MetadataExtractor, WorkflowJsonExtractor, Normalizer
from database.db import get_db, execute_query, fetch_one
from database.models import WorkflowNormalizedModel, NodeExtractedModel

logger = logging.getLogger(__name__)


class ExtractorAgent:
    def __init__(self, raw_dir: str = "data/raw", normalized_dir: str = "data/normalized"):
        self.raw_dir = Path(raw_dir)
        self.normalized_dir = Path(normalized_dir)
        self.normalized_dir.mkdir(parents=True, exist_ok=True)
        self.normalizer = Normalizer()

    def extract_from_raw_file(self, workflow_id: int, raw_path: Optional[str] = None) -> Dict[str, Any]:
        """Extract and normalize data from a raw workflow file."""
        if raw_path is None:
            raw_path = self.raw_dir / f"{workflow_id}_raw.json"
        else:
            raw_path = Path(raw_path)

        if not raw_path.exists():
            raise FileNotFoundError(f"Raw file not found: {raw_path}")

        with open(raw_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        return self.extract_and_normalize(workflow_id, raw_data)

    def extract_and_normalize(self, workflow_id: int, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Full extraction and normalization pipeline."""
        logger.info(f"Extracting and normalizing workflow {workflow_id}")

        # 1. Extract metadata
        metadata = MetadataExtractor.extract_metadata(raw_data)
        
        # 2. Extract graph (nodes, connections, integrations)
        graph = WorkflowJsonExtractor.extract_graph(raw_data)
        
        # 3. Normalize nodes
        normalized_nodes = []
        for node in graph["nodes"]:
            norm_type = self.normalizer.normalize_node_type(node["node_type"])
            normalized_nodes.append(NodeExtractedModel(
                node_name=node["node_name"],
                node_type=node["node_type"],
                node_type_normalized=norm_type,
                node_category=node["node_category"],
                is_trigger=node["is_trigger"],
                is_ai=node["is_ai"],
                is_custom=node["is_custom"],
                credentials_needed=node["credentials_needed"],
                parameters=node["parameters"],
            ).model_dump())

        # 4. Normalize integrations
        normalized_integrations = sorted(list(set(
            self.normalizer.normalize_integration_name(i) for i in graph["integrations"]
        )))

        # 5. Normalize categories
        normalized_categories = sorted(list(set(
            self.normalizer.normalize_category(c) for c in metadata.get("categories", [])
        )))

        # 6. Compute hashes
        content_hash = self.normalizer.compute_content_hash(raw_data)
        structure_hash = self.normalizer.compute_structure_hash(graph["nodes"], graph["raw_connections"])

        # 7. Build normalized model
        normalized = WorkflowNormalizedModel(
            workflow_id=workflow_id,
            title=metadata["title"],
            slug=metadata["slug"],
            canonical_url=metadata["canonical_url"],
            creator_name=metadata["creator_name"],
            creator_username=metadata["creator_username"],
            creator_bio=metadata["creator_bio"],
            creator_verified=metadata["creator_verified"],
            description=metadata["description"],
            node_count=graph["node_count"],
            connection_count=graph["connection_count"],
            nodes=normalized_nodes,
            integrations=normalized_integrations,
            categories=normalized_categories,
            tags=[],  # Could extract from description
            complexity="INTERMEDIATE",  # Will be set by complexity classifier
            cost_class="FREE",  # Will be set by cost classifier
            views=metadata["views"],
            recent_views=metadata["recent_views"],
            price=metadata["price"],
            content_hash=content_hash,
            structure_hash=structure_hash,
            created_at_source=self.normalizer.normalize_date(metadata.get("created_at_source")),
            updated_at_source=self.normalizer.normalize_date(metadata.get("updated_at_source")),
            raw_storage_path=str(raw_path) if 'raw_path' in locals() else None,
            normalized_storage_path=None,  # Will be set after saving
        )

        return normalized.model_dump()

    def save_normalized(self, normalized_data: Dict[str, Any]) -> str:
        """Save normalized data to JSON file and store path in database."""
        workflow_id = normalized_data["workflow_id"]
        norm_file = self.normalized_dir / f"{workflow_id}_normalized.json"
        
        with open(norm_file, "w", encoding="utf-8") as f:
            json.dump(normalized_data, f, indent=2, default=str)
        
        # Update database with normalized path
        execute_query(
            """
            UPDATE workflows SET
                normalized_storage_path = ?,
                content_hash = ?,
                structure_hash = ?,
                last_checked = DATETIME('now')
            WHERE workflow_id = ?
            """,
            (str(norm_file), normalized_data["content_hash"], normalized_data["structure_hash"], workflow_id)
        )
        
        return str(norm_file)

    def process_workflow(self, workflow_id: int, raw_path: Optional[str] = None) -> Dict[str, Any]:
        """Full pipeline: extract, normalize, save."""
        normalized = self.extract_and_normalize(workflow_id, raw_path)
        normalized["normalized_storage_path"] = self.save_normalized(normalized)
        return normalized

    def process_batch(self, workflow_ids: List[int]) -> List[Dict[str, Any]]:
        """Process multiple workflows."""
        results = []
        for wf_id in workflow_ids:
            try:
                result = self.process_workflow(wf_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process workflow {wf_id}: {e}")
                results.append({"workflow_id": wf_id, "error": str(e)})
        return results