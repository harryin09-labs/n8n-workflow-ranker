"""
Pytest Fixtures and Mock Data for n8n Workflow Intelligence & Ranking System.
"""

import pytest
import tempfile
import os
from pathlib import Path
from database.db import init_db, get_connection

@pytest.fixture
def test_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    os.environ["DATABASE_PATH"] = db_path
    init_db(db_path=db_path)
    
    yield db_path
    
    try:
        os.remove(db_path)
    except Exception:
        pass


@pytest.fixture
def sample_excel_postgres_workflow():
    return {
        "workflow": {
            "id": 1,
            "name": "Insert Excel data to Postgres",
            "description": "1. Read XLS from file\n2. Convert it to JSON\n3. Insert it in Postgres",
            "totalViews": 13545,
            "recentViews": 10,
            "price": 0.0,
            "createdAt": "2019-08-31T00:05:02.587Z",
            "user": {
                "name": "Jan Oberhauser",
                "username": "jan",
                "bio": "Founder/CEO of n8n",
                "verified": True
            },
            "categories": [{"id": 5, "name": "Engineering"}],
            "workflow": {
                "nodes": [
                    {
                        "name": "Read Binary File",
                        "type": "n8n-nodes-base.readBinaryFile",
                        "typeVersion": 1,
                        "position": [250, 300],
                        "parameters": {"filePath": "/data/test.xlsx"}
                    },
                    {
                        "name": "Spreadsheet File",
                        "type": "n8n-nodes-base.spreadsheetFile",
                        "typeVersion": 1,
                        "position": [450, 300],
                        "parameters": {"operation": "fromFile"}
                    },
                    {
                        "name": "Postgres",
                        "type": "n8n-nodes-base.postgres",
                        "typeVersion": 1,
                        "position": [650, 300],
                        "credentials": {"postgres": {"id": "123"}},
                        "parameters": {"operation": "insert", "table": "users"}
                    }
                ],
                "connections": {
                    "Read Binary File": {"main": [[{"node": "Spreadsheet File", "type": "main", "index": 0}]]},
                    "Spreadsheet File": {"main": [[{"node": "Postgres", "type": "main", "index": 0}]]}
                }
            }
        }
    }


@pytest.fixture
def sample_ai_rag_workflow():
    return {
        "workflow": {
            "id": 11807,
            "name": "Answer multi-channel support queries with OpenAI RAG and Supabase",
            "description": "Comprehensive customer support AI agent answering queries via RAG with OpenAI and Supabase vector database.",
            "totalViews": 2462,
            "recentViews": 55,
            "price": 0.0,
            "createdAt": "2024-03-15T12:00:00.000Z",
            "user": {
                "name": "Dragoș",
                "username": "dragos",
                "bio": "AI Automation Architect",
                "verified": False
            },
            "categories": [{"id": 25, "name": "AI"}, {"id": 48, "name": "AI RAG"}],
            "workflow": {
                "nodes": [
                    {
                        "name": "Webhook Trigger",
                        "type": "n8n-nodes-base.webhook",
                        "typeVersion": 1,
                        "position": [100, 200],
                        "parameters": {"path": "support-query", "httpMethod": "POST", "authentication": "headerAuth"}
                    },
                    {
                        "name": "AI Agent",
                        "type": "@n8n/n8n-nodes-langchain.agent",
                        "typeVersion": 1,
                        "position": [350, 200],
                        "parameters": {"systemMessage": "You are a helpful customer support assistant."}
                    },
                    {
                        "name": "OpenAI Chat Model",
                        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                        "typeVersion": 1,
                        "position": [350, 380],
                        "credentials": {"openAiApi": {"id": "999"}},
                        "parameters": {"model": "gpt-4o"}
                    },
                    {
                        "name": "Supabase Vector Store",
                        "type": "@n8n/n8n-nodes-langchain.vectorStoreSupabase",
                        "typeVersion": 1,
                        "position": [550, 380],
                        "credentials": {"supabaseApi": {"id": "888"}},
                        "parameters": {"tableName": "documents"}
                    },
                    {
                        "name": "Telegram",
                        "type": "n8n-nodes-base.telegram",
                        "typeVersion": 1,
                        "position": [700, 200],
                        "credentials": {"telegramApi": {"id": "777"}},
                        "parameters": {"chatId": "12345", "text": "Answer generated."}
                    }
                ],
                "connections": {
                    "Webhook Trigger": {"main": [[{"node": "AI Agent", "type": "main", "index": 0}]]},
                    "AI Agent": {"main": [[{"node": "Telegram", "type": "main", "index": 0}]]},
                    "OpenAI Chat Model": {"ai_languageModel": [[{"node": "AI Agent", "type": "ai_languageModel", "index": 0}]]},
                    "Supabase Vector Store": {"ai_tool": [[{"node": "AI Agent", "type": "ai_tool", "index": 0}]]}
                }
            }
        }
    }
