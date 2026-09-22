"""Export the workflows table to CSV and JSON."""
import csv
import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'n8n_workflows.db')
EXPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'exports')
CSV_PATH = os.path.join(EXPORT_DIR, 'n8n_workflows_full.csv')
JSON_PATH = os.path.join(EXPORT_DIR, 'n8n_workflows_full.json')

COLUMNS = [
    'workflow_id', 'title', 'problem_it_solves', 'overall_score',
    'daily_life_practicality_score', 'daily_life_use_frequency',
    'confidence_score', 'cost_class', 'complexity', 'value_score',
    'security_score', 'views', 'canonical_url', 'creator_name',
    'rating_label', 'node_count', 'description',
]

os.makedirs(EXPORT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute(f"SELECT {', '.join(COLUMNS)} FROM workflows")
rows = [dict(row) for row in cursor.fetchall()]
conn.close()

print(f"Read {len(rows)} rows from workflows table")

# --- CSV export ---
with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
csv_size = os.path.getsize(CSV_PATH)
print(f"Wrote CSV: {CSV_PATH} ({csv_size:,} bytes)")

# --- JSON export ---
with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)
json_size = os.path.getsize(JSON_PATH)
print(f"Wrote JSON: {JSON_PATH} ({json_size:,} bytes)")

print(f"\nDone. Row count: {len(rows)}")