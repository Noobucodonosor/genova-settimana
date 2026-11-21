"""Shared data I/O, inline-JSON escaping, and licensing helpers (ADR-0004 / TASK-ARCH-02)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

OPEN_DATA_ATTRIBUTION_TEXT = (
    "Dati geografici e toponimi: © OpenStreetMap contributors (ODbL 1.0) · Wikidata (CC0)."
)


def get_data_dir() -> Path:
    """Resolve the repository/data root directory portably."""
    return Path(os.environ.get("GENOVA_DATA_DIR") or Path(__file__).resolve().parent.parent)


def load_json_file(filename: str, data_dir: Optional[Path] = None) -> Any:
    """Load a UTF-8 JSON dataset relative to data_dir."""
    base = data_dir or get_data_dir()
    with open(base / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_json_for_script(obj: Any) -> str:
    """Serialize obj as JSON safe for inline <script> embedding (escapes '<')."""
    return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")
