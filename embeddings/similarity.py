"""
Duplicate Detection Engine: Multi-layer detection of exact duplicates, near duplicates, variants, and unique workflows.
"""

from typing import Dict, Any, List, Tuple, Optional
import re


def tokenize(text: str) -> set:
    """Tokenize text into lowercase alphanumeric words."""
    if not text:
        return set()
    return set(re.findall(r'[a-z0-9]+', text.lower()))


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


class DuplicateDetector:
    @staticmethod
    def compare_workflows(wf1: Dict[str, Any], wf2: Dict[str, Any]) -> Tuple[str, float, str]:
        """
        Compare two workflows and return (duplicate_type, similarity_score, reason).
        Duplicate types: EXACT_DUPLICATE, NEAR_DUPLICATE, VARIANT, UNIQUE.
        """
        id1 = wf1.get("workflow_id")
        id2 = wf2.get("workflow_id")
        
        # 1. Exact Content Hash
        if wf1.get("content_hash") and wf1.get("content_hash") == wf2.get("content_hash"):
            return "EXACT_DUPLICATE", 1.0, "Identical content hash and node parameters."

        # 2. Structure Hash
        same_structure = bool(wf1.get("structure_hash") and wf1.get("structure_hash") == wf2.get("structure_hash"))
        
        # 3. Metadata Token Similarity
        title_sim = jaccard_similarity(
            tokenize(wf1.get("title", "")),
            tokenize(wf2.get("title", ""))
        )
        desc_sim = jaccard_similarity(
            tokenize(wf1.get("description", "")),
            tokenize(wf2.get("description", ""))
        )
        integ_sim = jaccard_similarity(
            set(wf1.get("integrations", [])),
            set(wf2.get("integrations", []))
        )
        
        # Weighted similarity score
        metadata_sim = (title_sim * 0.4) + (desc_sim * 0.3) + (integ_sim * 0.3)
        
        if same_structure:
            if metadata_sim >= 0.7:
                return "NEAR_DUPLICATE", round(0.9 + (metadata_sim * 0.1), 3), f"Identical node graph topology and high title/description similarity ({metadata_sim:.0%})."
            else:
                return "VARIANT", round(0.75 + (metadata_sim * 0.15), 3), f"Identical structural node graph applied with different title or context ({metadata_sim:.0%})."

        # Node overlap
        nodes1 = set(n.get("node_type_clean", "") for n in wf1.get("nodes", []))
        nodes2 = set(n.get("node_type_clean", "") for n in wf2.get("nodes", []))
        node_sim = jaccard_similarity(nodes1, nodes2)
        
        overall_sim = (node_sim * 0.5) + (metadata_sim * 0.5)
        
        if overall_sim >= 0.8:
            return "VARIANT", round(overall_sim, 3), f"High node and metadata overlap ({overall_sim:.0%})."
        elif overall_sim >= 0.55:
            return "VARIANT", round(overall_sim, 3), f"Moderate architectural overlap ({overall_sim:.0%})."
        else:
            return "UNIQUE", round(overall_sim, 3), "Unique topology and distinct integration workflow."
