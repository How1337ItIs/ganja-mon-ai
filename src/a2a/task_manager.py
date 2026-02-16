"""
Persistent Task Manager (SQLite-backed)
========================================

State machine for A2A tasks:
    pending → queued → in_progress → completed
                                   → failed
    (any state) → cancelled

Features:
- SQLite persistence (survives restarts)
- State transition validation
- Task expiration (configurable TTL)
- Audit log for all transitions
- Query by status, skill, age
"""

import json
import logging
import sqlite3
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Valid state transitions
VALID_TRANSITIONS = {
    TaskStatus.PENDING: {TaskStatus.QUEUED, TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.QUEUED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
    TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: set(),  # Terminal
    TaskStatus.FAILED: {TaskStatus.PENDING},  # Allow retry
    TaskStatus.CANCELLED: set(),  # Terminal
}

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS a2a_tasks (
    id TEXT PRIMARY KEY,
    skill TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    direction TEXT NOT NULL DEFAULT 'inbound',
    agent_name TEXT DEFAULT '',
    agent_url TEXT DEFAULT '',
    message TEXT DEFAULT '',
    params TEXT DEFAULT '{}',
    result TEXT DEFAULT NULL,
    error TEXT DEFAULT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    expires_at REAL DEFAULT NULL,
    completed_at REAL DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS a2a_task_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    details TEXT DEFAULT '',
    timestamp REAL NOT NULL,
    FOREIGN KEY (task_id) REFERENCES a2a_tasks(id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON a2a_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_skill ON a2a_tasks(skill);
CREATE INDEX IF NOT EXISTS idx_tasks_direction ON a2a_tasks(direction);
CREATE INDEX IF NOT EXISTS idx_task_log_task_id ON a2a_task_log(task_id);
"""


class TaskManager:
    """
    Persistent SQLite-backed task state machine.

    Usage:
        tm = TaskManager()
        task_id = tm.create_task(skill="alpha-scan", message="Find signals", direction="inbound")
        tm.transition(task_id, TaskStatus.IN_PROGRESS)
        tm.complete(task_id, result={"signals": [...]})
    """

    def __init__(self, db_path: Optional[Path] = None, default_ttl: float = 3600.0):
        self._db_path = db_path or Path("data/a2a_tasks.db")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._default_ttl = default_ttl
        self._init_db()

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript(DB_SCHEMA)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def create_task(
        self,
        skill: str,
        message: str = "",
        params: Optional[Dict[str, Any]] = None,
        direction: str = "inbound",
        agent_name: str = "",
        agent_url: str = "",
        ttl: Optional[float] = None,
    ) -> str:
        """
        Create a new task.

        Args:
            skill: Skill ID being invoked
            message: Natural language message
            params: Additional parameters
            direction: "inbound" (received) or "outbound" (sent to other agent)
            agent_name: Name of the remote agent
            agent_url: A2A URL of the remote agent
            ttl: Time-to-live in seconds (None = default)

        Returns:
            Task ID (UUID)
        """
        task_id = str(uuid.uuid4())
        now = time.time()
        expires = now + (ttl or self._default_ttl)

        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO a2a_tasks
                   (id, skill, status, direction, agent_name, agent_url, message, params, created_at, updated_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task_id,
                    skill,
                    TaskStatus.PENDING.value,
                    direction,
                    agent_name,
                    agent_url,
                    message,
                    json.dumps(params or {}),
                    now,
                    now,
                    expires,
                ),
            )
            conn.execute(
                "INSERT INTO a2a_task_log (task_id, from_status, to_status, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                (task_id, None, TaskStatus.PENDING.value, "Task created", now),
            )

        logger.info(f"Created {direction} task {task_id[:8]} for skill={skill}")
        return task_id

    def transition(self, task_id: str, new_status: TaskStatus, details: str = "") -> bool:
        """
        Transition a task to a new status.

        Validates the transition is allowed. Returns True if successful.
        """
        with self._get_conn() as conn:
            row = conn.execute("SELECT status FROM a2a_tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                logger.warning(f"Task {task_id[:8]} not found")
                return False

            current = TaskStatus(row["status"])
            allowed = VALID_TRANSITIONS.get(current, set())

            if new_status not in allowed:
                logger.warning(f"Invalid transition {current.value} -> {new_status.value} for task {task_id[:8]}")
                return False

            now = time.time()
            updates = {"status": new_status.value, "updated_at": now}
            if new_status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                updates["completed_at"] = now

            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [task_id]
            conn.execute(f"UPDATE a2a_tasks SET {set_clause} WHERE id = ?", values)

            conn.execute(
                "INSERT INTO a2a_task_log (task_id, from_status, to_status, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                (task_id, current.value, new_status.value, details, now),
            )

        return True

    def complete(self, task_id: str, result: Any) -> bool:
        """Mark a task as completed with result data."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT status FROM a2a_tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                return False

            current = TaskStatus(row["status"])
            if TaskStatus.COMPLETED not in VALID_TRANSITIONS.get(current, set()):
                # Allow completing from PENDING too (for immediate results)
                if current != TaskStatus.PENDING:
                    logger.warning(f"Cannot complete task {task_id[:8]} from {current.value}")
                    return False

            now = time.time()
            conn.execute(
                "UPDATE a2a_tasks SET status = ?, result = ?, updated_at = ?, completed_at = ? WHERE id = ?",
                (TaskStatus.COMPLETED.value, json.dumps(result), now, now, task_id),
            )
            conn.execute(
                "INSERT INTO a2a_task_log (task_id, from_status, to_status, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                (task_id, current.value, TaskStatus.COMPLETED.value, "Task completed", now),
            )

        return True

    def fail(self, task_id: str, error: str) -> bool:
        """Mark a task as failed with error details."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT status FROM a2a_tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                return False

            current = TaskStatus(row["status"])
            now = time.time()
            conn.execute(
                "UPDATE a2a_tasks SET status = ?, error = ?, updated_at = ?, completed_at = ? WHERE id = ?",
                (TaskStatus.FAILED.value, error, now, now, task_id),
            )
            conn.execute(
                "INSERT INTO a2a_task_log (task_id, from_status, to_status, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                (task_id, current.value, TaskStatus.FAILED.value, error, now),
            )

        return True

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get full task details."""
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM a2a_tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def get_task_log(self, task_id: str) -> List[Dict[str, Any]]:
        """Get audit log for a task."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM a2a_task_log WHERE task_id = ? ORDER BY timestamp ASC",
                (task_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        skill: Optional[str] = None,
        direction: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filters."""
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status.value)
        if skill:
            conditions.append("skill = ?")
            params.append(skill)
        if direction:
            conditions.append("direction = ?")
            params.append(direction)

        where = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        with self._get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM a2a_tasks WHERE {where} ORDER BY created_at DESC LIMIT ?",
                params,
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def expire_stale(self) -> int:
        """Cancel expired tasks. Returns count of expired tasks."""
        now = time.time()
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, status FROM a2a_tasks WHERE expires_at < ? AND status NOT IN (?, ?, ?)",
                (now, TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value),
            ).fetchall()

            count = 0
            for row in rows:
                conn.execute(
                    "UPDATE a2a_tasks SET status = ?, error = ?, updated_at = ?, completed_at = ? WHERE id = ?",
                    (TaskStatus.CANCELLED.value, "Expired", now, now, row["id"]),
                )
                conn.execute(
                    "INSERT INTO a2a_task_log (task_id, from_status, to_status, details, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (row["id"], row["status"], TaskStatus.CANCELLED.value, "Auto-expired", now),
                )
                count += 1

        if count:
            logger.info(f"Expired {count} stale tasks")
        return count

    def stats(self) -> Dict[str, Any]:
        """Get task statistics."""
        with self._get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM a2a_tasks").fetchone()[0]
            by_status = {}
            for row in conn.execute("SELECT status, COUNT(*) as cnt FROM a2a_tasks GROUP BY status"):
                by_status[row["status"]] = row["cnt"]
            by_direction = {}
            for row in conn.execute("SELECT direction, COUNT(*) as cnt FROM a2a_tasks GROUP BY direction"):
                by_direction[row["direction"]] = row["cnt"]
            by_skill = {}
            for row in conn.execute("SELECT skill, COUNT(*) as cnt FROM a2a_tasks GROUP BY skill ORDER BY cnt DESC LIMIT 10"):
                by_skill[row["skill"]] = row["cnt"]

        return {
            "total": total,
            "by_status": by_status,
            "by_direction": by_direction,
            "by_skill": by_skill,
        }

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        # Parse JSON fields
        for field in ("params", "result"):
            if d.get(field) and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except json.JSONDecodeError:
                    pass
        return d


# Singleton
_instance: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    global _instance
    if _instance is None:
        _instance = TaskManager()
    return _instance
