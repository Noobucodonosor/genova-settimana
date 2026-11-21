# Investigation Report: Interaction Mechanics, WhatsApp Plain-Writing & Automated Validation

**Working Directory**: `/workspace/genova/.agents/teamwork/explorer_interaction_plainwriting/`  
**Date**: 2026-11-04  
**Investigator**: Teamwork Explorer (Interaction & Plain-Writing)  
**Target Requirements**: R2 (Interactive Selection), R3 (WhatsApp Output), R4 (Plain-Writing Tone & Constraints)

---

## 1. Executive Summary

This investigation designs the user interaction, selection mechanics, and WhatsApp plain-writing generation pipeline for the Genova informal outings tool. The goal is to provide a seamless workflow where a user can inspect the full verified weekly catalog of activities (cinema d'essai, exhibitions, walks, workshops, libraries, cultural cafes), select one or more options with checkboxes, and immediately generate an informal, natural WhatsApp message ready for 1-click copy-pasting.

Key discoveries and architectural conclusions:
1. **Zero-Dependency Interactive Selection**: The active Python environment is Python 3.14.3 with `pydantic`, `dataclasses`, `http.server`, and `curses` available, but third-party interactive prompt libraries (`prompt_toolkit`, `questionary`, `rich`) are *not installed*. We recommend a dual-interface architecture:
   - A **standard library interactive terminal selector** (numbered toggle REPL with instant commands `1,3`, `+2`, `-1`, `all`, `cat cinema`, `done`, `preview`) that works universally in any shell, SSH session, or IDE terminal without any pip dependencies.
   - An optional **lightweight local web UI** powered by standard library `http.server`, opening automatically in the browser with visual cards, live WhatsApp preview, category filtering, and 1-click clipboard copy (`navigator.clipboard`).
   - A **headless CLI argument mode** (`--select 1,2,5`, `--select-all`, `--category cinema,mostre`, `--json`) for automation and testing.
2. **Strict Plain-Writing Compliance**:
   - Analysis of the raw workspace datasets (`tempo_libero_payload.json`) revealed that existing event titles and pitches frequently contain em-dashes `—`. Raw ingestion without sanitization would immediately violate the strict plain-writing rule ("No em dashes or en dashes anywhere in the prose").
   - A dedicated sanitization pipeline is designed to convert em-dashes and en-dashes (`\u2014`, `\u2013`) into colons, commas, or clean sentence structures.
   - Strict ban on marketing puffery ("imperdibile", "splendido", "magico", "esperienza unica", "mozzafiato", "suggestivo", "fiore all'occhiello", "incantevole", "immersivo").
   - Strict ban on romantic framing ("date", "appuntamento romantico", "uscita a due", "galante", "intimo", "lume di candela"). In Italian, the token "date" is also the plural of "data" (calendar dates); to eliminate any false positives and strictly honor Acceptance Criterion 40, all generated copy uses natural Italian temporal terms ("giorni", "calendario", "in programma dal... al...", "orari") instead of the literal word "date".
3. **WhatsApp Formatting Standards**:
   - Proper bolding syntax: `*Testo*` (no spaces inside asterisks, no double asterisks `**` which break in WhatsApp).
   - Discrete, tasteful category emoji anchors (🎬 for cinema, 🏛️ for exhibitions, 🌿 for scenic walks, 📚 for libraries, 🎭 for workshops, 🎶 for music, ☕ for cultural cafes).
   - URL hygiene: URLs placed on their own line (`Info: https://...`) stripped of trailing periods or punctuation that would break WhatsApp's automatic link detection.
4. **Automated Validation Test Suite**:
   - A complete `PlainWritingValidator` regex engine and test specification verifying zero long dashes, zero romantic terms, zero marketing buzzwords, balanced bolding asterisks, raw URLs, and conciseness.

---

## 2. Requirement Analysis & Problem Boundary

### 2.1 The User Request (`ORIGINAL_REQUEST.md`)
The tool must extract and verify real leisure alternatives for the week in Genova and provincia for an "informale moderna" outing, allowing the user to view the full list, check/toggle desired options, and generate a ready-to-send WhatsApp message.

Crucial constraints:
- **R2 (Selection)**: User can review the complete catalog and check/toggle options via terminal or lightweight interface.
- **R3 (WhatsApp Output)**: WhatsApp formatting (*bold*, clean spacing, subtle emoji), copy-paste ready.
- **R4 (Plain-Writing Tone)**: Natural, direct, informal Italian between modern friends/acquaintances. NO long dashes (`—` or `–`). NO marketing puffery. NO romantic labeling ("date", "appuntamento romantico", "uscita a due").
- **R5 / AC 35-37**: Real venues, active hours, verified official source URLs, no placeholders or hallucinations.

---

## 3. Selection Mechanism Architecture (R2)

### 3.1 Environment Constraints & Tooling Survey
A check of the active Python runtime (`python3 -c "..."`) on macOS revealed:
- **Python version**: 3.14.3
- **Available stdlib & builtins**: `curses`, `http.server`, `urllib`, `dataclasses`, `pydantic`
- **Missing packages**: `prompt_toolkit` (None), `questionary` (None), `rich` (None), `inquirer` (None)

Following the project dependency guidelines (avoiding unnecessary external dependencies and preventing environment conflicts), the selection mechanism should not hard-depend on `prompt_toolkit` or `rich`.

### 3.2 Evaluation of Interaction Models

| Dimension | Option A: Stdlib Interactive CLI (Numbered REPL) | Option B: Stdlib Curses TUI | Option C: Lightweight Local Web UI (`http.server`) | Option D: CLI Argument / Batch Mode |
|---|---|---|---|---|
| **Dependencies** | Zero (Pure Python stdlib) | Zero (Pure Python stdlib) | Zero (Pure Python stdlib) | Zero (Pure Python stdlib) |
| **Portability** | 100% (Any shell, IDE terminal, SSH) | High (Requires ANSI terminal >= 80x24) | High (Requires browser or localhost port) | 100% (Automated/CI friendly) |
| **Visual Fidelity** | Clear text list with numbers & badges | Terminal curses window with checkboxes | Rich HTML cards, clickable links, live WhatsApp preview | Non-interactive text output |
| **Clickable Links** | Terminal dependent (OSC 8) | Truncated text | Native `<a target="_blank">` | Text strings |
| **Copy-to-Clipboard** | Manual copy or `pbcopy` | Manual copy or `pbcopy` | 1-click `navigator.clipboard` button | Pipe to `pbcopy` / stdout |
| **Ease of Use** | Fast keyboard commands (`1,3`, `all`, `done`) | Arrow keys + spacebar | Click checkboxes, toggle filters | Direct CLI flags |

### 3.3 Proposed Multi-Mode Interaction Architecture

We recommend a **Unified Selector Architecture** supporting three complementary modes:

```
                          ┌────────────────────────────┐
                          │  Verified Weekly Catalog   │
                          │   (WeeklyActivityCatalog)  │
                          └─────────────┬──────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
                 [Interactive Mode]           [Non-Interactive Mode]
                         │                             │
          ┌──────────────┴──────────────┐              │
          ▼                             ▼              ▼
   [Local Web UI]               [Terminal CLI]  [CLI Flags: --select]
  (localhost:8765)           (Numbered REPL /   (--all, --category,
 (Visual cards, live          curses fallback)   --tone, --output)
  preview, 1-click copy)               │               │
          │                            │               │
          └──────────────┬─────────────┘               │
                         ▼                             ▼
               ┌───────────────────────────────────────────────┐
               │    Selection State: [Selected Activity IDs]   │
               └───────────────────────┬───────────────────────┘
                                       ▼
               ┌───────────────────────────────────────────────┐
               │         WhatsApp Plain-Writing Formatter       │
               │  - Dash sanitization (no —, no –)             │
               │  - Plain Italian friend-to-friend templates   │
               │  - Category emoji & bolding layout            │
               │  - URL normalization                          │
               └───────────────────────┬───────────────────────┘
                                       ▼
               ┌───────────────────────────────────────────────┐
               │           PlainWritingValidator               │
               │   (Automated compliance & syntax checks)       │
               └───────────────────────┬───────────────────────┘
                                       ▼
               ┌───────────────────────────────────────────────┐
               │             Final WhatsApp Copy               │
               │  (Terminal stdout / File / Clipboard / Web)   │
               └───────────────────────────────────────────────┘
```

#### Mode 1: Terminal Numbered REPL Selector (Default CLI)
Designed for frictionless operation in standard terminals.
- Displays catalog grouped by category or sorted by day/zone:
  ```text
  ========================================================================
  GENOVA USCITE INFORMALI: CATALOGO SETTIMANALE (4-10 Nov 2026)
  ========================================================================
  Filtro attuale: TUTTI (8 alternative disponibili)
  
  [ ]  1. [CINEMA] Cinema Sivori: rassegna d'essai
          Centro (Salita S. Caterina 12) | Mercoledì ore 21:00
          https://circuitocinemagenova.com
  [*]  2. [MOSTRA] Palazzo Ducale: Mostra Impressionisti
          Centro (Piazza Matteotti 9) | Gio-Dom 10:00-19:00
          https://palazzoducale.genova.it
  [ ]  3. [PASSEGGIATA] Passeggiata di Nervi Anita Garibaldi
          Nervi (Porticciolo) | Tutti i giorni, ideale tardo pomeriggio
          https://www.visitgenoa.it
  ------------------------------------------------------------------------
  Comandi:
    [n,n...]    Toggle elementi (es: 1,3 oppure +1 +2 oppure -3)
    all / none  Seleziona tutti / Deseleziona tutti
    cat <nome>  Filtra o seleziona per categoria (cinema, mostre, etc.)
    show        Rivisualizza l'elenco aggiornato
    preview     Mostra anteprima del messaggio WhatsApp
    web         Avvia l'interfaccia grafica locale nel browser
    done        Conferma la selezione e genera il messaggio finale
    quit        Esci
  ------------------------------------------------------------------------
  Scelta > 
  ```
- Command parsing:
  - Handles comma-separated numbers: `1, 3, 5`
  - Handles additions/subtractions: `+2`, `-1`
  - Handles batch actions: `all`, `none`, `cat cinema`
  - Real-time feedback showing current count of selected items.
  - On `done`, validates selection, formats message, passes through `PlainWritingValidator`, prints formatted text to stdout, copies to macOS clipboard via `pbcopy` (if available), and writes `whatsapp_message.txt`.

#### Mode 2: Lightweight Local Web UI (Zero-Dependency `http.server`)
Launched with `--web` or typing `web` in the CLI prompt.
- **Server**: Python built-in `http.server.HTTPServer` running on `localhost:8765` (dynamic port fallback if busy).
- **Client**: Single-file responsive HTML5/CSS3/Vanilla JS embedded in the Python script. No npm, no external CDNs, completely offline-compatible.
- **Features**:
  - **Filter pills**: `Tutti`, `Cinema d'essai`, `Mostre & Arte`, `Passeggiate`, `Biblioteche & Spazi Studio`, `Laboratori & Corsi`.
  - **Live Search bar**: Filters cards by keyword (e.g. "Nervi", "Sivori", "gratis").
  - **Activity Cards**: Big toggle checkbox, category badge with subtle emoji, title, venue/address, schedule badge, factual description, and verified link opening in a new tab (`target="_blank"`).
  - **Split-Screen Live WhatsApp Preview**:
    - As the user clicks any card checkbox, the WhatsApp preview updates instantly (<20ms).
    - Tone selector buttons: `Informale`, `Compatto`, `Weekend`.
    - `📋 Copia Messaggio` button: Uses `navigator.clipboard.writeText()` with immediate visual toast notification ("Messaggio copiato!").
    - `💾 Salva ed Esci` button: Posts selected IDs to `/api/confirm`, writes output file, and cleanly stops the server.

#### Mode 3: CLI Arguments & Headless Automation
For non-interactive execution, scripts, and test pipelines:
- `genova_outings.py --select 1,2,5`
- `genova_outings.py --select-all`
- `genova_outings.py --category cinema,mostre`
- `genova_outings.py --tone weekend --layout compact`
- `genova_outings.py --output output.txt`
- `genova_outings.py --json`

---

## 4. WhatsApp Plain-Writing Generation Engine (R3 & R4)

### 4.1 Plain Writing Principles Applied to Informal Outings
The user request mandates strict plain-writing:
> "Il testo del messaggio deve seguire lo stile plain writing: scrittura naturale, diretta e informale, senza trattini lunghi (— o –), senza termini promozionali o buzzword, e senza riferimenti espliciti a 'date' o appuntamenti romantici."

Translating the core rules of `/plain-writing` into Italian friend-to-friend messaging:

#### Rule 1: Zero Long Dashes (Mechanical Check)
- Neither em-dash `—` (`\u2014`) nor en-dash `–` (`\u2013`) is permitted anywhere in the message prose.
- In AI-generated Italian, em-dashes are ubiquitous (e.g. `Cinema Sivori — Un classico d'autore`). This is a blatant tell.
- **Sanitizer action**: Replace any `\u2014` or `\u2013` with a colon `: `, comma `, `, or parenthesis `(...)`.
- Time intervals use standard ASCII hyphen without spaces or with clean prepositions: `10:00-19:00` or `dalle 10:00 alle 19:00`.

#### Rule 2: Strict Ban on Romantic Framing & The "Date" Token
- The framing must be an easy-going suggestion between modern friends or acquaintances who enjoy cultural and informal activities together ("se ti va di fare un salto", "ho visto queste cose carine a Genova").
- **Forbidden terms**:
  - `date`, `un date`, `date night`, `primo date`
  - `appuntamento romantico`, `appuntamenti romantici`
  - `uscita a due`, `serata a due`, `cena a due`
  - `galante`, `romantico`, `romantica`, `romantici`, `romantiche`
  - `intimo`, `intimità`, `lume di candela`
  - `innamorati`, `fidanzati`, `flirt`, `cuore`
- **Italian "date" linguistic clarification**:
  - In Italian, "date" is also the plural of "data" (e.g. "le date della mostra").
  - To ensure 100% compliance with Acceptance Criterion 40 ("non contiene la parola 'date'"), our generator templates strictly avoid "le date" and instead use:
    - `In programma dal... al...`
    - `Giorni e orari:`
    - `Aperto da martedì a domenica`
    - `Il calendario della rassegna`

#### Rule 3: Zero Marketing Puffery, Hype, or Buzzwords
- No artificial enthusiasm, no sales copy, no promotional adjectives.
- **Forbidden Italian buzzwords**:
  - `imperdibile`, `imperdibili`
  - `splendido`, `splendida`, `splendidi`, `splendide`
  - `magico`, `magica`, `magici`, `magiche`
  - `esperienza unica`, `esperienze uniche`
  - `mozzafiato`
  - `suggestivo`, `suggestiva`, `suggestivi`, `suggestive`
  - `fiore all'occhiello`
  - `incantevole`, `incantevoli`
  - `immersivo`, `immersiva`, `immersivi`
  - `da non perdere`
  - `straordinario`, `meraviglioso`, `favoloso`, `eccezionale`
  - `frizzante`, `top`, `chicca`, `gioiello`
- **Plain Writing alternative**: State the objective facts.
  - *Bad*: "Uno splendido film d'essai nella magica cornice del Sivori, un'esperienza davvero imperdibile!"
  - *Good*: "Cinema Sivori: rassegna d'autore. Mercoledì alle 21:00 in lingua originale con sottotitoli. Salita Santa Caterina (Centro)."

#### Rule 4: Clean WhatsApp Formatting
- WhatsApp bolding syntax requires asterisks touching the characters: `*Titolo dell'Attività*`. No spaces inside (`* Titolo *` fails).
- No standard Markdown headers (`#`, `##`, `###`), as WhatsApp prints hashes verbatim.
- No Markdown embedded links `[testo](url)`. WhatsApp renders `[testo](url)` as plain ugly text. Links must be raw URLs (`https://...`), ideally preceded by `Info:` or `Dettagli:`.
- URL cleanup: trailing punctuation (periods, commas, closing parentheses) must be stripped from URLs to prevent WhatsApp link-parser corruption.

---

## 5. Message Layouts & Templates

### 5.1 Template 1: Standard Card Layout (Default)
Best for 1 to 3 selected activities. Clean, spaced, highly legible on mobile.

```text
Ciao! Ti lascio un paio di idee carine per questa settimana a Genova se ti va di fare un salto:

🎬 *Cinema Sivori: rassegna d'essai*
📍 Salita Santa Caterina 12 (Centro)
🗓️ Mercoledì alle 21:00
Proiezione del film d'autore in versione originale sottotitolata.
Info: https://circuitocinemagenova.com

🏛️ *Palazzo Ducale: mostra temporanea*
📍 Piazza Matteotti 9 (Centro)
🗓️ Gio-Dom 10:00-19:00
Esposizione fotografica allestita negli spazi del Munizioniere.
Info: https://palazzoducale.genova.it

🌿 *Passeggiata di Nervi Anita Garibaldi*
📍 Porticciolo di Nervi (Nervi)
🗓️ Tutti i giorni, ideale tardo pomeriggio
Percorso pedonale panoramico a picco sulla scogliera tra il porticciolo e Capolungo.
Info: https://www.visitgenoa.it

Dimmi se ti ispira qualcosa!
```

### 5.2 Template 2: Compact / Bullet Layout
Best when 4 or more activities are selected, keeping the WhatsApp bubble concise without requiring excessive scrolling.

```text
Ecco qualche opzione in programma questa settimana a Genova se ti va di fare un salto:

• 🎬 *Cinema Sivori* (Centro): rassegna d'essai mercoledì alle 21:00. Info: https://circuitocinemagenova.com
• 🏛️ *Palazzo Ducale* (Centro): mostra aperta gio-dom 10:00-19:00. Info: https://palazzoducale.genova.it
• 📚 *Biblioteca Berio* (Centro): spazio lettura e chiostro aperti fino alle 19:00. Info: https://www.bibliotechedigenova.it
• 🌿 *Passeggiata di Nervi* (Nervi): percorso sul lungomare aperto tutto il giorno. Info: https://www.visitgenoa.it

Dimmi se ti ispira qualcuna!
```

### 5.3 Template 3: Single Activity Focus
Automatically selected when the user selects exactly 1 option:

```text
Ciao! Ho visto questa cosa a Genova questa settimana che sembra interessante se ti va di fare un salto:

🏛️ *Palazzo Ducale: mostra temporanea*
📍 Piazza Matteotti 9 (Centro)
🗓️ Gio-Dom 10:00-19:00
Esposizione fotografica allestita negli spazi del Munizioniere.
Info: https://palazzoducale.genova.it

Dimmi se ti ispira!
```

---

## 6. Interface Contracts & Data Specifications

### 6.1 Data Model: `OutingOption` & `WeeklyCatalog`
The contract between the extraction/verification engine and the selector/formatter:

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
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
    id: str                           # Unique slug, e.g. "sivori_film_mer"
    title: str                        # Plain title, sanitized (no em/en dashes)
    category: OutingCategory          # Category enum
    venue: str                        # Venue name, e.g. "Cinema Sivori"
    zone: str                         # Zone/quarter, e.g. "Centro", "Nervi"
    address: str                      # Street address, e.g. "Salita Santa Caterina 12"
    days_display: str                 # Human readable schedule, e.g. "Mercoledì ore 21:00"
    time_slot: str                    # "mattina", "pomeriggio", "sera", "flessibile"
    description: str                  # 1-2 factual plain-writing sentences
    source_url: str                   # Official verified URL
    verified: bool = True             # Verification flag
    verification_source: str = ""     # e.g. "official_website", "circuito_cinema"
    is_free: bool = False             # Admission is free
    cost_info: Optional[str] = None   # e.g. "Biglietto 7€", "Ingresso libero"
    tags: List[str] = field(default_factory=list) # e.g. ["indoor", "lingua_originale"]
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WeeklyCatalog:
    week_label: str                   # e.g. "Settimana 4-10 Novembre 2026"
    generated_at: str                 # ISO timestamp
    activities: List[OutingOption] = field(default_factory=list)
```

### 6.2 Category Emoji Mapping
| Category | Emoji | Context |
|---|---|---|
| `cinema` | 🎬 | Cinema d'essai, rassegne d'autore |
| `mostra` | 🏛️ | Mostre d'arte, musei civici, esposizioni temporanee |
| `passeggiata` | 🌿 | Passeggiate panoramiche, sentieri urbani, parchi storici |
| `biblioteca` | 📚 | Biblioteche civiche, sale studio, chiostri di lettura |
| `laboratorio` | 🎭 | Workshop culturali, lezioni aperte, circoli teatrali |
| `musica` | 🎶 | Concerti jazz, live club acustici, serate musicali |
| `ritrovo` | ☕ | Caffè letterari, spazi sociali aperti (es. Giardini Luzzati) |
| `altro` | 📍 | Altre attività informali verificate |

---

## 7. Automated Plain-Writing Validation & Test Specification

### 7.1 Validation Class Architecture: `PlainWritingValidator`
The validator checks any generated text against 6 automated rules:

```python
import re
from typing import List, Tuple

class PlainWritingValidator:
    DASH_PATTERN = re.compile(r'[\u2014\u2013\u2015]')
    
    ROMANCE_PATTERN = re.compile(
        r'\b(date|appuntament[oi]\s+romantic[oi]|serat[ae]\s+a\s+due|uscit[ae]\s+a\s+due|'
        r'galante|romantic[oai]|lume\s+di\s+candela|innamorat[oaie]|fidanzat[oaie]|'
        r'flirt|intimit[aà]|cenett[ae]\s+a\s+due)\b',
        re.IGNORECASE
    )
    
    PUFFERY_PATTERN = re.compile(
        r'\b(imperdibile|imperdibili|splendid[oai]|magic[oai]|esperienza\s+unica|'
        r'esperienze\s+uniche|mozzafiato|suggestiv[oai]|fiore\s+all\'?occhiello|'
        r'incantevole|incantevoli|immersiv[oai]|da\s+non\s+perdere|straordinari[oai]|'
        r'meraviglios[oai]|favolos[oai]|eccezionale|frizzante|incredibile|top)\b',
        re.IGNORECASE
    )

    @classmethod
    def validate(cls, text: str) -> List[Tuple[str, str]]:
        errors = []
        if cls.DASH_PATTERN.search(text):
            matches = cls.DASH_PATTERN.findall(text)
            errors.append(('FORBIDDEN_DASH', f'Found prohibited long dashes: {matches}'))
            
        if cls.ROMANCE_PATTERN.search(text):
            matches = cls.ROMANCE_PATTERN.findall(text)
            errors.append(('ROMANTIC_FRAMING', f'Found prohibited romance terms: {matches}'))
            
        if cls.PUFFERY_PATTERN.search(text):
            matches = cls.PUFFERY_PATTERN.findall(text)
            errors.append(('MARKETING_PUFFERY', f'Found prohibited puffery terms: {matches}'))
            
        # WhatsApp bolding syntax: even number of asterisks
        if text.count('*') % 2 != 0:
            errors.append(('UNBALANCED_ASTERISKS', f'Unbalanced * for WhatsApp bolding ({text.count("*")} total)'))
            
        # Disallow markdown headers (#) and markdown links [text](url)
        if re.search(r'^#{1,6}\s', text, re.MULTILINE):
            errors.append(('MARKDOWN_HEADERS', 'Found markdown headers (#) not supported in WhatsApp'))
        if re.search(r'\[.+?\]\(.+?\)', text):
            errors.append(('MARKDOWN_LINKS', 'Found [text](url) markdown link. WhatsApp requires raw URLs'))
            
        return errors
```

### 7.2 Automated Test Cases
1. `test_no_long_dashes`: Checks that text containing `\u2014` or `\u2013` fails immediately.
2. `test_no_romantic_terms`: Checks rejection of "date", "appuntamento romantico", "uscita a due", "galante".
3. `test_no_puffery`: Checks rejection of "imperdibile", "splendido", "magico", "esperienza unica", "mozzafiato".
4. `test_whatsapp_bolding`: Checks that asterisks are balanced and properly formatted.
5. `test_no_markdown_links`: Ensures `[click here](url)` is detected as invalid, enforcing raw URLs.
6. `test_dash_sanitizer`: Verifies that raw inputs with `—` (like `#DomenicalMuseo — Palazzi Reale`) are automatically cleaned to `#DomenicalMuseo: Palazzi Reale`.
7. `test_empty_selection`: Ensures appropriate graceful message when 0 items are selected.
8. `test_single_item_selection`: Verifies single item tone adjustments.
9. `test_multiple_item_selection`: Verifies card layout and compact layout.

---

## 8. Next Steps & Handoff Preparation
This analysis provides the architectural foundation. The handoff report will document the concrete file designs, code snippets, and verification methods for downstream implementation.
