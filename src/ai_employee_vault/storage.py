import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_tables()

    def _ensure_db_dir(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                importance INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                due_date TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def close(self):
        pass


class MemoryStore:
    def __init__(self, db: Database):
        self.db = db

    def set(self, key: str, value: str, category: str = "general", importance: int = 1):
        self.db.execute(
            """INSERT INTO memories (key, value, category, importance)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET value=?, updated_at=CURRENT_TIMESTAMP""",
            (key, value, category, importance, value),
        )

    def get(self, key: str) -> Optional[str]:
        row = self.db.fetch_one("SELECT value FROM memories WHERE key = ?", (key,))
        return row["value"] if row else None

    def get_all(self, category: Optional[str] = None) -> Dict[str, str]:
        query = "SELECT key, value FROM memories"
        params = ()
        if category:
            query += " WHERE category = ?"
            params = (category,)
        rows = self.db.fetch_all(query, params)
        return {row["key"]: row["value"] for row in rows}

    def search(self, query: str) -> List[Dict]:
        rows = self.db.fetch_all(
            "SELECT * FROM memories WHERE key LIKE ? OR value LIKE ? ORDER BY importance DESC",
            (f"%{query}%", f"%{query}%"),
        )
        return rows

    def delete(self, key: str):
        self.db.execute("DELETE FROM memories WHERE key = ?", (key,))

    def get_important(self, limit: int = 10) -> List[Dict]:
        return self.db.fetch_all(
            "SELECT * FROM memories ORDER BY importance DESC, updated_at DESC LIMIT ?",
            (limit,),
        )


class TaskStore:
    def __init__(self, db: Database):
        self.db = db

    def create(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> int:
        tags_json = json.dumps(tags) if tags else None
        cursor = self.db.execute(
            """INSERT INTO tasks (title, description, priority, due_date, tags)
               VALUES (?, ?, ?, ?, ?)""",
            (title, description, priority, due_date, tags_json),
        )
        return cursor.lastrowid

    def get(self, task_id: int) -> Optional[Dict]:
        row = self.db.fetch_one("SELECT * FROM tasks WHERE id = ?", (task_id,))
        if row and row.get("tags"):
            row["tags"] = json.loads(row["tags"])
        return row

    def update(self, task_id: int, **kwargs):
        allowed = ["title", "description", "status", "priority", "due_date", "tags"]
        updates = {k: v for k, v in kwargs.items() if k in allowed}

        if "tags" in updates:
            updates["tags"] = json.dumps(updates["tags"])

        if updates:
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = tuple(updates.values()) + (task_id,)
            self.db.execute(
                f"UPDATE tasks SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE id = ?",
                values,
            )

    def complete(self, task_id: int):
        self.db.execute(
            """UPDATE tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP,
               updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
            (task_id,),
        )

    def delete(self, task_id: int):
        self.db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def get_all(self, status: Optional[str] = None) -> List[Dict]:
        query = "SELECT * FROM tasks"
        params = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END, created_at DESC"

        rows = self.db.fetch_all(query, params)
        for row in rows:
            if row.get("tags"):
                row["tags"] = json.loads(row["tags"])
        return rows

    def get_pending(self) -> List[Dict]:
        return self.get_all(status="pending")

    def get_overdue(self) -> List[Dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        rows = self.db.fetch_all(
            """SELECT * FROM tasks WHERE status = 'pending' AND due_date < ? 
               ORDER BY due_date ASC""",
            (today,),
        )
        for row in rows:
            if row.get("tags"):
                row["tags"] = json.loads(row["tags"])
        return rows


class ChatStore:
    def __init__(self, db: Database):
        self.db = db

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        metadata_json = json.dumps(metadata) if metadata else None
        self.db.execute(
            "INSERT INTO chat_messages (role, content, metadata) VALUES (?, ?, ?)",
            (role, content, metadata_json),
        )

    def get_history(self, limit: int = 100) -> List[Dict]:
        rows = self.db.fetch_all(
            "SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        for row in rows:
            if row.get("metadata"):
                row["metadata"] = json.loads(row["metadata"])
        return list(reversed(rows))

    def clear_history(self):
        self.db.execute("DELETE FROM chat_messages")

    def search(self, query: str) -> List[Dict]:
        rows = self.db.fetch_all(
            "SELECT * FROM chat_messages WHERE content LIKE ? ORDER BY created_at DESC",
            (f"%{query}%",),
        )
        for row in rows:
            if row.get("metadata"):
                row["metadata"] = json.loads(row["metadata"])
        return rows


class PreferenceStore:
    def __init__(self, db: Database):
        self.db = db

    def set(self, key: str, value: str):
        self.db.execute(
            """INSERT INTO user_preferences (key, value)
               VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value = ?, updated_at=CURRENT_TIMESTAMP""",
            (key, value, value),
        )

    def get(self, key: str) -> Optional[str]:
        row = self.db.fetch_one(
            "SELECT value FROM user_preferences WHERE key = ?", (key,)
        )
        return row["value"] if row else None

    def get_all(self) -> Dict[str, str]:
        rows = self.db.fetch_all("SELECT key, value FROM user_preferences")
        return {row["key"]: row["value"] for row in rows}

    def delete(self, key: str):
        self.db.execute("DELETE FROM user_preferences WHERE key = ?", (key,))


def get_storage(vault_path: str = ".") -> Dict[str, Any]:
    db_path = os.path.join(vault_path, ".ai_employee.db")
    db = Database(db_path)
    return {
        "db": db,
        "memory": MemoryStore(db),
        "tasks": TaskStore(db),
        "chat": ChatStore(db),
        "preferences": PreferenceStore(db),
    }
