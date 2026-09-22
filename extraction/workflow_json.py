"""
Workflow JSON Extractor: Deeply parses node graph, credentials, parameters, triggers, AI components, and databases.
"""

from typing import Dict, Any, List, Optional, Set
import re

AI_NODE_PATTERNS = [
    r"langchain", r"openai", r"anthropic", r"gemini", r"cohere", r"mistral",
    r"groq", r"ollama", r"agent", r"chain", r"chatmodel", r"lmchat",
    r"vectordb", r"pinecone", r"qdrant", r"weaviate", r"memory", r"tool",
    r"retriever", r"embeddings", r"documentloader", r"textsplitter"
]

DATABASE_NODE_PATTERNS = [
    r"postgres", r"mysql", r"mongodb", r"redis", r"sqlite", r"supabase",
    r"couchdb", r"mariadb", r"clickhouse", r"snowflake", r"elasticsearch",
    r"pinecone", r"qdrant", r"weaviate", r"milvus", r"airtable"
]

TRIGGER_NODE_PATTERNS = [
    r"trigger", r"webhook", r"poll", r"schedule", r"cron", r"watch", r"listener"
]


class WorkflowJsonExtractor:
    @staticmethod
    def extract_graph(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure nodes, edges, credentials, and topology."""
        wf_obj = raw_data.get("workflow", raw_data)
        inner_wf = wf_obj.get("workflow") or {}
        
        # In some payloads nodes are at root or inside inner workflow object
        nodes_raw = inner_wf.get("nodes") or wf_obj.get("nodes") or []
        connections_raw = inner_wf.get("connections") or wf_obj.get("connections") or {}
        
        extracted_nodes = []
        integrations_set: Set[str] = set()
        credentials_set: Set[str] = set()
        triggers_list: List[str] = []
        code_nodes_count = 0
        ai_nodes_count = 0
        custom_nodes_count = 0
        webhook_nodes_count = 0
        database_nodes_count = 0
        subworkflow_nodes_count = 0
        
        for node in nodes_raw:
            if not isinstance(node, dict):
                continue
                
            node_name = node.get("name", "Unnamed Node")
            node_type = node.get("type", "unknown")
            type_version = node.get("typeVersion", 1)
            parameters = node.get("parameters", {})
            credentials = node.get("credentials", {})
            
            # Identify categorization
            node_type_lower = node_type.lower()
            
            is_trigger = any(re.search(pat, node_type_lower) for pat in TRIGGER_NODE_PATTERNS)
            if is_trigger:
                triggers_list.append(node_type)
                
            is_ai = any(re.search(pat, node_type_lower) for pat in AI_NODE_PATTERNS)
            if is_ai:
                ai_nodes_count += 1
                
            is_code = "code" in node_type_lower or "function" in node_type_lower
            if is_code:
                code_nodes_count += 1
                
            is_webhook = "webhook" in node_type_lower
            if is_webhook:
                webhook_nodes_count += 1
                
            is_db = any(re.search(pat, node_type_lower) for pat in DATABASE_NODE_PATTERNS)
            if is_db:
                database_nodes_count += 1
                
            is_subworkflow = "executeworkflow" in node_type_lower or "toolworkflow" in node_type_lower
            if is_subworkflow:
                subworkflow_nodes_count += 1
                
            is_custom = node_type.startswith("@") and not node_type.startswith("@n8n/")
            if is_custom:
                custom_nodes_count += 1

            # Extract integration name from node_type
            # e.g., 'n8n-nodes-base.googleSheets' -> 'googleSheets'
            # '@n8n/n8n-nodes-langchain.lmChatOpenAi' -> 'OpenAI'
            clean_type = node_type.split(".")[-1]
            integrations_set.add(clean_type)
            
            # Extract credentials needed
            cred_names = []
            if isinstance(credentials, dict):
                for cred_key, cred_val in credentials.items():
                    if isinstance(cred_val, dict) and "id" in cred_val:
                        cred_names.append(cred_key)
                        credentials_set.add(cred_key)
                    elif isinstance(cred_val, str):
                        cred_names.append(cred_val)
                        credentials_set.add(cred_val)
                        
            # Determine high level node category
            if is_trigger:
                category = "trigger"
            elif is_ai:
                category = "ai"
            elif is_code:
                category = "code"
            elif is_db:
                category = "database"
            elif is_subworkflow:
                category = "subworkflow"
            elif is_custom:
                category = "custom"
            else:
                category = "action"

            extracted_nodes.append({
                "node_name": node_name,
                "node_type": node_type,
                "node_type_clean": clean_type,
                "node_category": category,
                "is_trigger": is_trigger,
                "is_ai": is_ai,
                "is_custom": is_custom,
                "is_code": is_code,
                "is_database": is_db,
                "credentials_needed": ", ".join(cred_names) if cred_names else None,
                "parameters": parameters,
            })

        # Count total connections (edges)
        connection_count = 0
        if isinstance(connections_raw, dict):
            for src_node, outputs in connections_raw.items():
                if isinstance(outputs, dict):
                    for out_type, conns in outputs.items():
                        if isinstance(conns, list):
                            for conn_group in conns:
                                if isinstance(conn_group, list):
                                    connection_count += len(conn_group)

        return {
            "node_count": len(extracted_nodes),
            "connection_count": connection_count,
            "nodes": extracted_nodes,
            "integrations": sorted(list(integrations_set)),
            "credentials_required": sorted(list(credentials_set)),
            "triggers": triggers_list,
            "ai_nodes_count": ai_nodes_count,
            "code_nodes_count": code_nodes_count,
            "custom_nodes_count": custom_nodes_count,
            "webhook_nodes_count": webhook_nodes_count,
            "database_nodes_count": database_nodes_count,
            "subworkflow_nodes_count": subworkflow_nodes_count,
            "raw_connections": connections_raw,
        }
