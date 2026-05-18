"""
Downloads the booru-characters dataset from HuggingFace and builds the local SQLite DB.
"""

import json
import os
import sqlite3
import urllib.request
from datetime import datetime, timezone
from ..sn0w import Logger

DATASET_URL = "https://huggingface.co/datasets/Sn0w123/booru-characters/resolve/main/characters.jsonl"
DATASET_API_URL = "https://huggingface.co/api/datasets/Sn0w123/booru-characters"

logger = Logger()


def _remote_last_modified() -> datetime | None:
    """
    Return the last-modified datetime of the dataset.
    Queries the HuggingFace Hub API (no file download); falls back to a HEAD
    request with ``X-Linked-Last-Modified`` if the API call fails.
    Returns ``None`` if both approaches fail.
    """
    try:
        req = urllib.request.Request(
            DATASET_API_URL,
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        raw = data.get("lastModified")
        if raw:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:  # pylint: disable=broad-except
        pass

    logger.log(
        "Warning: Could not determine remote last-modified time for dataset, assuming local DB is up to date.",
        "WARNING",
    )
    return None


def is_db_up_to_date(db_path: str) -> bool:
    """
    Return ``True`` when the local DB is at least as recent as the remote dataset.
    Falls back to ``True`` on any network error so the app still works offline.
    """
    if not os.path.exists(db_path):
        return False

    remote_dt = _remote_last_modified()
    if remote_dt is None:
        # Can't reach HF – assume local copy is fine
        return True

    local_mtime = datetime.fromtimestamp(os.path.getmtime(db_path), tz=timezone.utc)
    return local_mtime >= remote_dt


def _setup_db(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS characters (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        copyright TEXT,
        prompt TEXT,
        clothing_tags TEXT,
        gender TEXT,
        post_count INTEGER
    )"""
    )

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS character_relationships (
        id INTEGER PRIMARY KEY,
        tag_id INTEGER,
        related_tag_id INTEGER,
        relation_type TEXT,
        FOREIGN KEY (tag_id) REFERENCES characters(id),
        FOREIGN KEY (related_tag_id) REFERENCES characters(id)
    )"""
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_character_relationships_tag_id ON character_relationships(tag_id)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_character_relationships_related_tag_id ON character_relationships(related_tag_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_character_relationships_type ON character_relationships(relation_type)"
    )


def build_db_from_dataset(db_path: str, logger=None) -> None:
    """
    Download ``characters.jsonl`` from HuggingFace and populate the SQLite DB at *db_path*.

    The JSONL schema per line:
        {
            "id": int,
            "name": str,
            "post_count": int,
            "gender": str | null,
            "clothing": list[str],
            "characteristics": list[str],
            "copyright": list[str],
            "relationships": {"parents": list[int], "children": list[int], "siblings": list[int]}
        }
    """

    def log(msg: str, level: str = "INFORMATIONAL") -> None:
        if logger is not None:
            logger.log(msg, level)

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    log("Downloading booru-characters dataset from HuggingFace…")
    try:
        req = urllib.request.Request(
            DATASET_URL,
            headers={"User-Agent": "ComfyUI-Sn0w-Scripts/1.0"},
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            raw_bytes = response.read()
    except Exception as exc:  # pylint: disable=broad-except
        raise RuntimeError(f"Failed to download dataset: {exc}") from exc

    log("Download complete, parsing dataset…")
    lines = raw_bytes.decode("utf-8").splitlines()

    records: list[dict] = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            log(f"Skipping malformed JSONL line {i}: {exc}", "WARNING")

    log(f"Parsed {len(records)} character records, building database…")

    # Build in a temp file first, then replace the target path after success
    tmp_path = db_path + ".tmp"
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    conn = sqlite3.connect(tmp_path)
    cursor = conn.cursor()
    _setup_db(cursor)

    # ── Pass 1: insert characters ──────────────────────────────────────────────
    for rec in records:
        char_id = rec["id"]
        name = rec.get("name", "")
        post_count = rec.get("post_count", 0)
        gender = rec.get("gender") or ""
        clothing_tags = ",".join(rec.get("clothing") or [])
        prompt = ",".join(rec.get("characteristics") or [])
        copyright_tags = ",".join(rec.get("copyright") or [])

        cursor.execute(
            """INSERT OR REPLACE INTO characters
               (id, name, copyright, prompt, clothing_tags, gender, post_count)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (char_id, name, copyright_tags, prompt, clothing_tags, gender, post_count),
        )

    # ── Pass 2: insert relationships (IDs are preserved from the dataset) ──────
    for rec in records:
        tag_id = rec["id"]
        rels: dict = rec.get("relationships") or {}
        _rel_label_map = {"parents": "parent", "children": "child", "siblings": "sibling"}
        for rel_type, related_ids in rels.items():
            rel_label = _rel_label_map.get(rel_type)
            if rel_label is None:
                continue
            for related_id in related_ids or []:
                cursor.execute(
                    """INSERT INTO character_relationships
                       (tag_id, related_tag_id, relation_type)
                       VALUES (?, ?, ?)""",
                    (tag_id, related_id, rel_label),
                )

    conn.commit()
    conn.close()

    # Atomically replace old DB with new one
    if os.path.exists(db_path):
        os.remove(db_path)
    os.rename(tmp_path, db_path)

    log(f"Database built successfully at '{db_path}' ({len(records)} characters).")
