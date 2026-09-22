"""
Complexity Classifier: Evaluates workflow architecture and classifies into BEGINNER, INTERMEDIATE, ADVANCED, EXPERT.
"""

from typing import Dict, Any, List, Tuple


class ComplexityClassifier:
    @staticmethod
    def classify(workflow_data: Dict[str, Any]) -> Tuple[str, float, str]:
        """
        Classifies workflow complexity based on objective architectural evidence.
        Returns (complexity_label, complexity_score, complexity_reason).
        """
        nodes = workflow_data.get("nodes", [])
        node_count = len(nodes)
        integrations = workflow_data.get("integrations", [])
        integration_count = len(integrations)
        
        # Analyze specific component indicators
        code_nodes = [n for n in nodes if n.get("is_code") or "code" in n.get("node_type_normalized", "")]
        ai_nodes = [n for n in nodes if n.get("is_ai") or "agent" in n.get("node_type_normalized", "")]
        subworkflows = [n for n in nodes if "executeworkflow" in n.get("node_type", "").lower()]
        webhooks = [n for n in nodes if n.get("is_trigger") and "webhook" in n.get("node_type", "").lower()]
        databases = [n for n in nodes if n.get("is_database")]
        custom_nodes = [n for n in nodes if n.get("is_custom")]
        credentials_needed = [n for n in nodes if n.get("credentials_needed")]
        
        # Calculate raw complexity points (0 - 100)
        points = 0.0
        reasons = []
        
        # Node scale
        if node_count <= 3:
            points += 10
            reasons.append(f"Minimal footprint ({node_count} nodes)")
        elif node_count <= 7:
            points += 25
            reasons.append(f"Moderate node count ({node_count} nodes)")
        elif node_count <= 15:
            points += 45
            reasons.append(f"Multi-step pipeline ({node_count} nodes)")
        else:
            points += 65
            reasons.append(f"Large complex graph ({node_count} nodes)")
            
        # Integration breadth
        if integration_count <= 1:
            points += 5
        elif integration_count <= 3:
            points += 15
            reasons.append(f"{integration_count} connected services")
        else:
            points += 30
            reasons.append(f"High integration breadth ({integration_count} distinct services)")
            
        # Advanced patterns
        if code_nodes:
            points += min(20, len(code_nodes) * 10)
            reasons.append(f"{len(code_nodes)} custom code/script nodes")
            
        if ai_nodes:
            points += min(25, len(ai_nodes) * 8)
            reasons.append(f"{len(ai_nodes)} AI/LangChain/LLM nodes")
            
        if subworkflows:
            points += 20
            reasons.append(f"Sub-workflow execution architecture")
            
        if custom_nodes:
            points += 15
            reasons.append(f"Community/custom node dependencies")
            
        if databases:
            points += 10
            reasons.append(f"External database/storage integration")
            
        if len(credentials_needed) >= 3:
            points += 15
            reasons.append(f"Multi-service authentication ({len(credentials_needed)} credentials)")

        # Normalize score to 0.0 - 10.0
        complexity_score = round(min(10.0, max(1.0, points / 10.0)), 2)
        
        # Classify
        if complexity_score < 3.0:
            classification = "BEGINNER"
        elif complexity_score < 6.0:
            classification = "INTERMEDIATE"
        elif complexity_score < 8.5:
            classification = "ADVANCED"
        else:
            classification = "EXPERT"
            
        reason_text = "; ".join(reasons)
        return classification, complexity_score, reason_text
