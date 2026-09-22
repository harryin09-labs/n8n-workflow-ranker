"""
Pydantic Data Models for n8n Workflow Intelligence & Ranking System.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DiscoveryRecordModel(BaseModel):
    workflow_id: int
    canonical_url: str
    slug: Optional[str] = None
    discovery_source: str = "sitemap"
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    crawl_status: str = "pending"


class NodeExtractedModel(BaseModel):
    node_name: str
    node_type: str
    node_type_normalized: str
    node_category: str = "general"  # trigger, action, ai, logic, data_transform, code, custom
    is_trigger: bool = False
    is_ai: bool = False
    is_custom: bool = False
    credentials_needed: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class ScoreEvidenceModel(BaseModel):
    criterion: str
    raw_score: float = Field(..., ge=0.0, le=10.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    weighted_score: float
    evidence: str
    reasoning: str
    confidence: float = Field(100.0, ge=0.0, le=100.0)
    evidence_type: str = "OBSERVED"  # OBSERVED, DERIVED, INFERRED, UNKNOWN


class PenaltyModel(BaseModel):
    penalty_type: str
    penalty_amount: float
    evidence: str


class SecurityFindingModel(BaseModel):
    finding_type: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    evidence: Optional[str] = None
    recommendation: Optional[str] = None


class DuplicateMatchModel(BaseModel):
    workflow_id: int
    duplicate_of_id: int
    duplicate_type: str  # EXACT_DUPLICATE, NEAR_DUPLICATE, VARIANT, UNIQUE
    similarity_score: float
    similarity_reason: Optional[str] = None


class WorkflowNormalizedModel(BaseModel):
    workflow_id: int
    title: str
    slug: Optional[str] = None
    canonical_url: str
    creator_name: Optional[str] = None
    creator_username: Optional[str] = None
    creator_bio: Optional[str] = None
    creator_verified: bool = False
    description: Optional[str] = None
    problem_it_solves: Optional[str] = None
    
    # Topology
    node_count: int = 0
    connection_count: int = 0
    nodes: List[NodeExtractedModel] = Field(default_factory=list)
    integrations: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    # Classification
    complexity: str = "INTERMEDIATE"
    complexity_score: float = 5.0
    complexity_reason: Optional[str] = None
    
    cost_class: str = "FREE"
    paid_dependencies: List[str] = Field(default_factory=list)
    free_dependencies: List[str] = Field(default_factory=list)
    cost_notes: Optional[str] = None
    
    # Scoring
    overall_score: float = 0.0
    base_score: float = 0.0
    rating_label: str = "Average"
    confidence_score: float = 0.0
    ai_score: Optional[float] = None
    security_score: float = 10.0
    security_risk_level: str = "LOW"
    
    value_score: float = 0.0
    value_reason: Optional[str] = None
    hidden_gem_score: float = 0.0
    
    # Daily-Life Practicality
    daily_life_practicality_score: float = 0.0
    daily_life_practicality_label: Optional[str] = None
    daily_life_practicality_reason: Optional[str] = None
    daily_life_use_frequency: Optional[str] = None
    
    # Stats & Hashes
    views: int = 0
    recent_views: int = 0
    price: float = 0.0
    content_hash: Optional[str] = None
    structure_hash: Optional[str] = None
    
    # Detailed breakdown
    evidence_list: List[ScoreEvidenceModel] = Field(default_factory=list)
    penalties_list: List[PenaltyModel] = Field(default_factory=list)
    security_findings: List[SecurityFindingModel] = Field(default_factory=list)
    
    # Timestamps
    created_at_source: Optional[str] = None
    updated_at_source: Optional[str] = None
    raw_storage_path: Optional[str] = None
    normalized_storage_path: Optional[str] = None
