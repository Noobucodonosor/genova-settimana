# Project: Genova Weekly Informal Outings Tool

## Architecture

The tool is a modular Python 3 package (`genova_outings`) that extracts and live-verifies real weekly leisure and cultural alternatives for Genova and provincia, offers interactive selection, and formats a plain-writing WhatsApp message ready to send.

```
                  ┌──────────────────────────────────────────────┐
                  │           Data Sources (Tier 0)              │
                  ├──────────────────────┬───────────────────────┤
                  │ Local Datasets       │ Authoritative Live    │
                  │ (tempo_libero,       │ Endpoints (Circuito,  │
                  │  guida_aperti, etc.) │ Ducale, Berio, etc.)  │
                  └──────────┬───────────┴───────────┬───────────┘
                             │                       │
                             ▼                       ▼
                  ┌──────────────────────────────────────────────┐
                  │    Core Extraction & Verification Engine     │
                  │   (`catalog.py`, `verifier.py`, `models.py`) │
                  │  - Filters informal categories               │
                  │  - Probes live URLs & active schedules       │
                  │  - Enforces negative filters (e.g. closure)  │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │       Weekly Verified Outings Catalog        │
                  │              (List[OutingOption])            │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │             Selection Component              │
                  │           (`selector.py`, `web_ui.py`)       │
                  │  - Interactive Terminal REPL (checkboxes)   │
                  │  - Optional Local Web UI (localhost:8765)    │
                  │  - Headless CLI flags (--select, --all)      │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │    WhatsApp Plain-Writing Formatter Engine   │
                  │         (`formatter.py`, `validator.py`)     │
                  │  - Friend-to-friend informal tone            │
                  │  - Zero em-dashes (\u2014) or en-dashes      │
                  │  - Zero romantic date words or buzzwords     │
                  │  - WhatsApp bolding (*text*) & raw links     │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │       CLI Runner & Final WhatsApp Text       │
                  │   (Terminal stdout, pbcopy, clipboard, file) │
                  └──────────────────────────────────────────────┘
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Local Dataset Aggregator | Reads and parses `tempo_libero_payload.json`, `guida_aperti`, and `dashboard_items.json` for verified Genova venues. | M1 | Survey |
| F2 | Live Verification Prober | Validates reachability (HTTP 200) and extracts active current-week events for cinema, exhibitions, and clubs; enforces closure filters (Villa Croce). | M1 | Survey |
| F3 | Catalog Harmonizer & Schema | Normalizes events into `OutingOption` models with category, date/time slot, verified URL, and zone; ensures zero placeholders. | M1 | Survey |
| F4 | Interactive Selection Interface | Provides interactive numbered terminal checkbox toggling, optional local web UI, and CLI flags. | M2 | Survey |
| F5 | Plain-Writing WhatsApp Formatter | Generates formatted WhatsApp messages without em/en-dashes, promotional buzzwords, or romantic date framing. | M2 | Survey |
| F6 | Automated Plain-Writing Validator | Validates text for dash violations, banned romantic/hype keywords, and WhatsApp formatting rules. | M2 | Survey |
| F7 | Main CLI Integration & Runner | Unified entrypoint script (`genova_outings.py` / `python3 -m genova_outings`) coordinating extraction, selection, and output. | M3 | Survey |
| F8 | Comprehensive E2E Test Suite | 4-tier requirement-driven opaque-box test suite (Tiers 1-4) plus Tier 5 adversarial hardening. | M_E2E | Survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Catalog & Live Verification Engine | `genova_outings/models.py`, `catalog.py`, `verifier.py` | none | DONE |
| M2 | Selector & Plain-Writing WhatsApp Formatter | `genova_outings/selector.py`, `formatter.py`, `validator.py`, `web_ui.py` | M1 interface | IN_PROGRESS |
| M3 | CLI Entrypoint & Integrated Application | `genova_outings/cli.py`, `genova_outings/__main__.py`, root runner | M1, M2 | PLANNED |
| M_E2E | E2E Test Suite Track | `tests/test_e2e_tier1.py`, `tier2.py`, `tier3.py`, `tier4.py`, test runner | none | DONE |
| M4 | Final Milestone: 100% E2E Pass & Hardening | Pass 100% of Tiers 1-4 tests, followed by Tier 5 adversarial testing | M1, M2, M3, M_E2E | PLANNED |

## Interface Contracts

### `models.py`
```python
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class OutingCategory(str, Enum):
    CINEMA = "cinema"
    MOSTRA = "mostra"
    PASSEGGIATA = "passeggiata"
    BIBLIOTECA = "biblioteca"
    LABORATORIO = "laboratorio"
    MUSICA = "musica"
    RITROVO = "ritrovo"
    ALTRO = "altro"

@dataclass
class OutingOption:
    id: str
    title: str
    category: OutingCategory
    venue: str
    zone: str
    day_time: str
    verified_url: str
    description: str
    source_type: str = "verified_local" # or "live_web"
    is_weather_dependent: bool = False
```

### `catalog.py` ↔ `selector.py`
- `get_weekly_catalog(live_verify: bool = True, category: Optional[str] = None) -> List[OutingOption]`
  Returns a curated, verified list of active options for the current week in Genova and provincia.

### `selector.py` ↔ `formatter.py`
- `format_whatsapp_message(selected_options: List[OutingOption], tone: str = "amichevole") -> str`
  Produces the WhatsApp-ready text with zero long dashes, discrete emojis, bold titles, and no romantic date keywords.

### `validator.py`
- `validate_plain_writing(text: str) -> Tuple[bool, List[str]]`
  Returns `(True, [])` if compliant, or `(False, reasons)` if any em-dash, banned keyword, or broken format is found.

## Code Layout
```
/Users/dany/genova/
├── genova_outings/
│   ├── __init__.py
│   ├── __main__.py
│   ├── models.py
│   ├── catalog.py
│   ├── verifier.py
│   ├── selector.py
│   ├── formatter.py
│   ├── validator.py
│   └── web_ui.py
├── genova_outings.py          # Convenient top-level launcher
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_verifier.py
│   ├── test_catalog.py
│   ├── test_formatter.py
│   ├── test_validator.py
│   ├── test_selector.py
│   ├── test_e2e_tier1_features.py
│   ├── test_e2e_tier2_boundaries.py
│   ├── test_e2e_tier3_pairwise.py
│   └── test_e2e_tier4_scenarios.py
├── run_tests.py               # Zero-dependency test runner
└── .agents/teamwork/          # Agent metadata only
```
