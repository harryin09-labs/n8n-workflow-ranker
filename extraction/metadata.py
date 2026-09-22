"""
Metadata Extractor: Extracts public template metadata from raw payload.
"""

from typing import Dict, Any, List, Optional
import re


class MetadataExtractor:
    @staticmethod
    def extract_metadata(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract top-level metadata from n8n API template response."""
        wf_obj = raw_data.get("workflow", raw_data)
        
        workflow_id = wf_obj.get("id")
        title = wf_obj.get("name") or "Untitled Workflow"
        description = wf_obj.get("description") or ""
        
        # Creator details
        user_info = wf_obj.get("user") or {}
        creator_name = user_info.get("name") or "Unknown"
        creator_username = user_info.get("username") or "unknown"
        creator_bio = user_info.get("bio")
        creator_verified = bool(user_info.get("verified", False))
        
        # Categories
        categories_raw = wf_obj.get("categories") or []
        categories = []
        for cat in categories_raw:
            if isinstance(cat, dict) and "name" in cat:
                categories.append(cat["name"])
            elif isinstance(cat, str):
                categories.append(cat)
                
        # Stats & Pricing
        views = wf_obj.get("totalViews", wf_obj.get("views", 0)) or 0
        recent_views = wf_obj.get("recentViews", 0) or 0
        price = float(wf_obj.get("price", 0.0) or 0.0)
        
        # Dates
        created_at = wf_obj.get("createdAt")
        updated_at = wf_obj.get("updatedAt")
        
        # Generate slug and canonical URL
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
        canonical_url = f"https://n8n.io/workflows/{workflow_id}-{slug}/" if slug else f"https://n8n.io/workflows/{workflow_id}/"

        return {
            "workflow_id": workflow_id,
            "title": title.strip(),
            "slug": slug,
            "canonical_url": canonical_url,
            "creator_name": creator_name.strip(),
            "creator_username": creator_username.strip(),
            "creator_bio": creator_bio,
            "creator_verified": creator_verified,
            "description": description.strip(),
            "categories": categories,
            "views": int(views),
            "recent_views": int(recent_views),
            "price": price,
            "created_at_source": created_at,
            "updated_at_source": updated_at,
        }
