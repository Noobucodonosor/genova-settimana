"""Shared data I/O, inline-JSON escaping, and licensing helpers (ADR-0004 / TASK-ARCH-02)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

OPEN_DATA_ATTRIBUTION_TEXT = (
    "Dati geografici e toponimi: © OpenStreetMap contributors (ODbL 1.0) · Wikidata (CC0)."
)

NAV_ITEMS = (
    ("index", "index.html", "Agenda Settimana"),
    ("esercenti", "esercenti.html", "Esercenti"),
    ("bussola", "bussola.html", "Bussola"),
    ("dashboard", "dashboard.html", "Dashboard"),
    ("storie", "storie.html", "Storie dalle Strade"),
)

PWA_HEAD_HTML = (
    '<link rel="manifest" href="./manifest.webmanifest">\n'
    '  <meta name="theme-color" content="#0f4c81">'
)

PWA_SW_SCRIPT = (
    '<script>if("serviceWorker"in navigator&&location.protocol.startsWith("http"))'
    '{window.addEventListener("load",()=>navigator.serviceWorker.register("./sw.js").catch(()=>{}));}</script>'
)

SHARED_NAV_CSS = """
.gc-nav {
  background: #ffffff;
  border-bottom: 1px solid #e2ddd5;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.gc-nav-inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 10px 20px;
  display: flex;
  flex-wrap: wrap;
  flex-wrap: balance;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.gc-brand {
  font-weight: 700;
  font-size: 0.95rem;
  letter-spacing: -0.01em;
  color: #14191f;
  text-decoration: none;
}
.gc-links {
  display: flex;
  flex-wrap: wrap;
  flex-wrap: balance;
  gap: 6px;
}
.gc-link {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  color: #475569;
  text-decoration: none;
  border: 1px solid transparent;
  transition: background-color 140ms ease, color 140ms ease;
}
.gc-link:hover {
  background: #f3efe8;
  color: #14191f;
}
.gc-link.active {
  background: #0f4c81;
  color: #ffffff;
}
"""


def render_shared_nav(active_slug: str) -> str:
    """Render shared editorial top navigation bar across Genova Civica pages."""
    links = "\n".join(
        f'<a class="gc-link{" active" if slug == active_slug else ""}" href="{href}"'
        f'{" aria-current=\"page\"" if slug == active_slug else ""}>{label}</a>'
        for slug, href, label in NAV_ITEMS
    )
    return (
        '<nav class="gc-nav" aria-label="Sezioni Genova Civica">'
        '<div class="gc-nav-inner">'
        '<a class="gc-brand" href="index.html">Genova Civica</a>'
        f'<div class="gc-links">{links}</div>'
        '</div></nav>'
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
