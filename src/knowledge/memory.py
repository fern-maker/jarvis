"""
Jarvis Memory Manager
- Load training examples into SQLite
- Query past conversations for memory recall
- Manage user preferences
"""

import glob
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional

MODULE_DIR = Path(__file__).parent
REPO_ROOT = MODULE_DIR.parents[1]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "memory.db"
SCHEMA_PATH = MODULE_DIR / "memory_schema.sql"
RAW_TRAINING_DATA_DIR = REPO_ROOT / "training" / "data" / "raw"


class MemoryManager:
    def __init__(self, db_path: str = str(DEFAULT_DB_PATH)):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        """Initialize database with schema"""
        with open(SCHEMA_PATH) as f:
            self.conn.executescript(f.read())
        self.conn.commit()

    def load_training_examples(self, jsonl_path: str):
        """Load training examples from JSONL file into database"""
        cursor = self.conn.cursor()
        count = 0

        with open(jsonl_path) as f:
            for line in f:
                if not line.strip():
                    continue

                example = json.loads(line)
                conversation = example.get("conversation", [])

                # Extract user message and assistant response
                if len(conversation) >= 2:
                    user_msg = conversation[0].get("content", "")
                    asst_msg = conversation[1].get("content", "")
                else:
                    continue

                web_context = example.get("web_search_context", {})
                web_query = web_context.get("query", None)
                web_sources = json.dumps(web_context.get("sources", []))

                past_convos = example.get("memory_context", {}).get("past_conversations", [])
                referenced_ids = json.dumps([c.get("id") for c in past_convos if "id" in c])

                cursor.execute(
                    """
                    INSERT INTO conversations
                    (user_message, assistant_response, web_search_query, web_search_sources,
                     referenced_past_convos, category, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_msg,
                        asst_msg,
                        web_query,
                        web_sources,
                        referenced_ids,
                        example.get("primary_category", "general"),
                        json.dumps(example.get("tags", []))
                    )
                )
                count += 1

        self.conn.commit()
        print(f"Loaded {count} training examples from {jsonl_path}")
        return count

    def load_all_training_data(self, raw_dir: str = str(RAW_TRAINING_DATA_DIR)):
        """Load every *.jsonl file under the training data raw directory"""
        total = 0
        for path in sorted(glob.glob(str(Path(raw_dir) / "*.jsonl"))):
            total += self.load_training_examples(path)
        print(f"Loaded {total} training examples total from {raw_dir}")
        return total

    def recall_relevant_conversations(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for past conversations relevant to current query
        Uses simple keyword matching; can be upgraded to semantic search later
        """
        cursor = self.conn.cursor()

        # Simple keyword search
        search_term = f"%{query}%"
        cursor.execute(
            """
            SELECT id, user_message, assistant_response, timestamp, category
            FROM conversations
            WHERE user_message LIKE ? OR assistant_response LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (search_term, search_term, limit)
        )

        results = [dict(row) for row in cursor.fetchall()]
        return results

    def save_conversation(self, user_msg: str, assistant_msg: str,
                         web_query: Optional[str] = None,
                         web_sources: Optional[List] = None,
                         category: str = "general",
                         tags: Optional[List[str]] = None):
        """Save a real conversation to memory"""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO conversations
            (user_message, assistant_response, web_search_query, web_search_sources, category, tags)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_msg,
                assistant_msg,
                web_query,
                json.dumps(web_sources or []),
                category,
                json.dumps(tags or [])
            )
        )

        self.conn.commit()

    def set_user_preference(self, key: str, value: str):
        """Store user preference"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO user_preferences (preference_key, preference_value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()

    def get_user_preference(self, key: str) -> Optional[str]:
        """Retrieve user preference"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT preference_value FROM user_preferences WHERE preference_key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_all_user_preferences(self) -> Dict[str, str]:
        """Get all user preferences"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT preference_key, preference_value FROM user_preferences")
        return {row[0]: row[1] for row in cursor.fetchall()}

    def cache_web_search(self, query: str, sources: List[Dict]):
        """Cache web search results"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO web_search_cache (query, sources) VALUES (?, ?)",
            (query, json.dumps(sources))
        )
        self.conn.commit()

    def get_cached_search(self, query: str) -> Optional[List[Dict]]:
        """Retrieve cached web search"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT sources FROM web_search_cache WHERE query = ?", (query,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def close(self):
        """Close database connection"""
        self.conn.close()


if __name__ == "__main__":
    # Example usage
    manager = MemoryManager()

    # Load all training examples
    manager.load_all_training_data()

    # Save a test conversation
    manager.save_conversation(
        user_msg="Jarvis, how do I use PyTorch?",
        assistant_msg="PyTorch is a machine learning framework, sir...",
        category="coding",
        tags=["ml", "python"]
    )

    # Recall relevant conversations
    results = manager.recall_relevant_conversations("PyTorch")
    for r in results:
        print(f"ID: {r['id']}, Date: {r['timestamp']}, Category: {r['category']}")
        print(f"User: {r['user_message'][:50]}...\n")

    manager.close()
