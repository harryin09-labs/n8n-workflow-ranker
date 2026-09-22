"""
AI Capability Scorer: Evaluates AI architecture, agent patterns, memory, RAG, and tools.
Returns None (N/A) for non-AI workflows.
"""

from typing import Dict, Any, Optional, Tuple, List


class AICapabilityScorer:
    @staticmethod
    def evaluate(workflow_data: Dict[str, Any]) -> Tuple[Optional[float], List[str]]:
        """
        Evaluates AI capabilities (0.0 to 10.0) if AI components exist.
        Returns (ai_score, reasons_list).
        """
        nodes = workflow_data.get("nodes", [])
        ai_nodes = [n for n in nodes if n.get("is_ai")]
        
        if not ai_nodes:
            return None, ["Non-AI workflow: AI capability evaluation is not applicable."]

        score = 4.0  # Base score for containing AI nodes
        reasons = [f"Contains {len(ai_nodes)} native AI/LangChain nodes"]
        
        # 1. Agent Architecture & Tools
        agent_nodes = [n for n in ai_nodes if "agent" in n.get("node_type", "").lower() or "agent" in n.get("node_type_normalized", "").lower()]
        tool_nodes = [n for n in nodes if "tool" in n.get("node_type", "").lower() or "tool" in n.get("node_type_normalized", "").lower()]
        
        if agent_nodes:
            score += 2.0
            reasons.append("Autonomous agent node architecture present (+2.0)")
        if tool_nodes:
            score += 1.5
            reasons.append(f"{len(tool_nodes)} agent tools configured (+1.5)")
            
        # 2. RAG & Vector Databases
        rag_nodes = [n for n in nodes if any(k in n.get("node_type", "").lower() for k in ["vectordb", "pinecone", "qdrant", "weaviate", "retriever", "embeddings"])]
        if rag_nodes:
            score += 1.5
            reasons.append("RAG & vector knowledge retrieval pipeline configured (+1.5)")
            
        # 3. Memory & Context
        memory_nodes = [n for n in nodes if "memory" in n.get("node_type", "").lower() or "buffer" in n.get("node_type", "").lower()]
        if memory_nodes:
            score += 1.0
            reasons.append("Chat memory buffer enabled (+1.0)")

        # 4. Multi-model / fallback flexibility
        model_nodes = [n for n in ai_nodes if "chatmodel" in n.get("node_type", "").lower() or "lmchat" in n.get("node_type", "").lower()]
        if len(model_nodes) >= 2:
            score += 0.5
            reasons.append("Multi-model routing or fallback capabilities (+0.5)")

        final_ai_score = round(min(10.0, max(1.0, score)), 2)
        return final_ai_score, reasons
