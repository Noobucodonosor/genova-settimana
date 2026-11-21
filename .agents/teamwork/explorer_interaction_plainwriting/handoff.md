# Handoff Report: Interaction Mechanics, Plain-Writing WhatsApp Engine & Automated Validation

**From**: Explorer (Interaction & Plain-Writing)  
**To**: Orchestrator & Development Workers  
**Working Directory**: `/workspace/genova/.agents/teamwork/explorer_interaction_plainwriting/`  
**Date**: 2026-11-04  
**Status**: Hard Handoff (Investigation Complete)

---

## 1. Observation

1. **Python Environment**:
   - Command: `python3 -c "import sys; print(sys.version); ..."`
   - Output: `Python 3.14.3` on macOS (Clang 17.0.0).
   - Available packages: `curses`, `http.server`, `urllib`, `dataclasses`, `pydantic`.
   - Missing packages: `prompt_toolkit: NOT available`, `questionary: NOT available`, `rich: NOT available`.
   - Consequence: An interactive CLI cannot rely on third-party libraries like `prompt_toolkit` or `questionary` without introducing installation friction. It must be built using Python standard library (`curses` or numbered interactive REPL) with optional lightweight local web UI via standard library `http.server`.

2. **Dataset Contamination with Long Dashes**:
   - Examination of local data asset `tempo_libero_payload.json` revealed:
     `Key monthly_events: {'month': 1, 'day_rule': 'first_sun', 'titolo': '#DomenicalMuseo — Palazzi Reale, Spinola e MuSel...'}`
   - Notice the em-dash `—` (`\u2014`) in raw data titles. Direct concatenation of raw titles into WhatsApp messages without sanitization violates Plain Writing Rule 1 (`ORIGINAL_REQUEST.md:22` and `ORIGINAL_REQUEST.md:41`: *"senza trattini lunghi (— o –)"*).

3. **User Request & Acceptance Criteria (`ORIGINAL_REQUEST.md`)**:
   - Line 15-16: R2: *"Offrire all'utente la possibilità di visionare l'elenco completo delle alternative della settimana e spuntare (tramite selezione interattiva da terminale o interfaccia leggera con checkbox/elenchi numerati selezionabili) quelle di proprio interesse da includere nel messaggio."*
   - Line 18-19: R3: *"Generare il testo del messaggio contenente le sole alternative spuntate, formattato specificamente per WhatsApp (spaziatura, grassetti, emoji sobrie), pronto per il copia-incolla."*
   - Line 21-22: R4: *"Il testo del messaggio deve seguire lo stile plain writing: scrittura naturale, diretta e informale, senza trattini lunghi (— o –), senza termini promozionali o buzzword, e senza riferimenti espliciti a 'date' o appuntamenti romantici."*
   - Line 40: *"Il messaggio per WhatsApp non contiene la parola 'date' o espressioni esplicite di appuntamento galante."*
   - Line 41: *"Il testo rispetta il vincolo di plain writing: assenza di trattini lunghi (— o –) e assenza di formule promozionali o enfatiche."*

4. **Linguistic Nuance in Italian ("date")**:
   - Test: `re.search(r'\bdate\b', 'Ecco le date della mostra')` matched `date`. In Italian, "date" is the plural of "data" (calendar dates). To avoid false alarms and strictly adhere to Acceptance Criterion 40, all copy templates must systematically replace "le date" with natural calendar words ("i giorni", "il calendario", "in programma dal... al...", "orari").

5. **WhatsApp Markdown Syntax Constraints**:
   - WhatsApp supports bolding via `*testo*` (asterisks touching characters, no interior spaces).
   - WhatsApp does NOT render standard markdown links `[testo](url)` or markdown headers `# Titolo`. Those appear literally as messy characters. URLs must be raw `https://...` links.
   - Trailing punctuation (e.g. `https://example.com.`) breaks WhatsApp auto-linking.

---

## 2. Logic Chain

1. **Selection Mechanism (R2)**:
   - *Premise*: The tool must allow reviewing all weekly options and checking desired items without mandatory external pip installs.
   - *Deduction*: We design a **Unified Multi-Mode Selector**:
     - Mode A (Default Terminal): A numbered interactive prompt (`1,3`, `+2`, `-1`, `all`, `done`, `cat cinema`, `preview`) that runs in any terminal, SSH, or IDE with 100% reliability.
     - Mode B (Optional Web UI): A local web interface launched via `--web` using standard library `http.server` on `localhost:8765`, providing visual cards, category filter pills, clickable official links, real-time WhatsApp preview, and 1-click clipboard copy (`navigator.clipboard`).
     - Mode C (Headless CLI): Argument flags (`--select 1,2,5`, `--select-all`, `--category cinema,mostre`, `--output file.txt`) for CI/CD and automated test execution.

2. **WhatsApp Message Formatter (R3 & R4)**:
   - *Premise*: Raw extracted events contain em-dashes and promotional pitches, whereas the final text must be natural informal Italian between friends, free of hype, long dashes, and romantic framing.
   - *Deduction*: The formatter must implement a 3-stage pipeline:
     1. **Sanitization**: Replace all `\u2014` and `\u2013` in titles and descriptions with colons or commas. Strip trailing punctuation from URLs.
     2. **Templating**: Render a friendly, non-romantic opener ("Ciao! Ti lascio un paio di idee carine per questa settimana a Genova se ti va di fare un salto..."), structured items with category emojis (🎬, 🏛️, 🌿, 📚, 🎭, 🎶, ☕) and bolded titles (`*Titolo*`), followed by a relaxed closer ("Dimmi se ti ispira qualcosa!").
     3. **Post-Validation**: Execute `PlainWritingValidator` before displaying or saving. If any prohibited pattern is detected, the pipeline fails or corrects before output.

3. **Interface Contract & Testability**:
   - *Premise*: Sibling agents (`explorer_survey_datasets` and `spec_miner_live_sources`) produce structured weekly entries.
   - *Deduction*: We establish `OutingOption` and `WeeklyCatalog` as the formal interface contract. Automated pytest/unittest suites verify plain-writing rules, dash absence, ban-list enforcement, and syntax compliance.

---

## 3. Caveats

1. **Clipboard API in Headless / SSH**:
   - In the terminal CLI, copying to the system clipboard uses macOS `pbcopy` if detected. On headless Linux or SSH without X11/Wayland, `pbcopy` will not be present; the tool gracefully falls back to writing the message to `whatsapp_message.txt` and printing to stdout.
2. **Web Browser Auto-Open**:
   - When running `--web`, `webbrowser.open()` opens the system browser on macOS. In headless testing or environments where no browser is available, the server logs the URL `http://localhost:8765` so the user can navigate manually or use CLI flags instead.
3. **Italian Word "date" vs English "date"**:
   - As observed, Italian texts sometimes use "date" as plural for "data". Even though our templates strictly avoid "le date" (using "i giorni", "il calendario"), raw scraped text from third-party sites could theoretically contain "le date". The sanitization filter replaces `le date` with `i giorni` or `il calendario` to guarantee zero instances of `date` in the final WhatsApp output.

---

## 4. Conclusion & Concrete Design Specifications

### 4.1 Interface Contract: Data Models (`models.py`)

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

---

### 4.2 Interactive Selection Mechanics (`selector.py`)

#### A. Numbered Terminal REPL Selector (Standard Library)
```python
def run_terminal_selector(catalog: WeeklyCatalog) -> List[OutingOption]:
    selected_indices = set()
    items = catalog.activities

    def display_list():
        print("\n" + "=" * 72)
        print(f"GENOVA USCITE INFORMALI: CATALOGO SETTIMANALE ({catalog.week_label})")
        print("=" * 72)
        for idx, item in enumerate(items, 1):
            mark = "[*]" if idx in selected_indices else "[ ]"
            cat_tag = f"[{item.category.upper()}]"
            loc = f"{item.venue} ({item.zone})" if item.zone else item.venue
            print(f"{mark} {idx:2d}. {cat_tag:<14} {item.title}")
            print(f"         📍 {loc} | 🗓️ {item.days_display}")
            print(f"         🔗 {item.source_url}")
        print("-" * 72)
        print(f"Selezionati: {len(selected_indices)} su {len(items)}")
        print("Comandi: [n,n...] toggle | all | none | cat <nome> | preview | done | quit")
        print("-" * 72)

    display_list()
    while True:
        try:
            cmd = input("Scelta > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nUscita annullata.")
            return []

        if not cmd:
            continue
        if cmd in ("quit", "q", "exit"):
            return []
        if cmd in ("done", "ok"):
            if not selected_indices:
                print("Nessuna attività selezionata. Digita i numeri (es. 1,3) oppure 'all'.")
                continue
            return [items[i - 1] for i in sorted(selected_indices)]
        if cmd == "all":
            selected_indices = set(range(1, len(items) + 1))
            display_list()
            continue
        if cmd == "none":
            selected_indices.clear()
            display_list()
            continue
        if cmd.startswith("cat "):
            query = cmd[4:].strip()
            matched = [i for i, it in enumerate(items, 1) if query in it.category.value.lower()]
            if matched:
                selected_indices.update(matched)
                display_list()
            else:
                print(f"Nessuna categoria corrispondente a '{query}'.")
            continue
        if cmd == "preview":
            selected_items = [items[i - 1] for i in sorted(selected_indices)]
            print("\n" + "=" * 50 + " ANTEPRIMA " + "=" * 50)
            print(format_whatsapp_message(selected_items))
            print("=" * 111)
            continue
        if cmd == "show":
            display_list()
            continue

        # Process toggle numbers
        parts = cmd.replace(",", " ").split()
        for p in parts:
            if p.startswith("+") and p[1:].isdigit():
                val = int(p[1:])
                if 1 <= val <= len(items):
                    selected_indices.add(val)
            elif p.startswith("-") and p[1:].isdigit():
                val = int(p[1:])
                selected_indices.discard(val)
            elif p.isdigit():
                val = int(p)
                if 1 <= val <= len(items):
                    if val in selected_indices:
                        selected_indices.remove(val)
                    else:
                        selected_indices.add(val)
        display_list()
```

#### B. Lightweight Local Web UI (Standard Library `http.server`)
An embedded single-page application served via `http.server`:
- Endpoints:
  - `GET /`: Serves complete HTML5/CSS/JS page.
  - `GET /api/catalog`: Returns catalog JSON.
  - `POST /api/save`: Receives `{ "selected_ids": [...], "tone": "..." }`, saves message, signals shutdown.
- Architecture highlights:
  - 100% self-contained: no npm, no CDN dependencies, completely offline-capable.
  - Responsive cards with checkboxes and category icons.
  - Real-time side-by-side WhatsApp preview bubble.
  - 1-click clipboard copy (`navigator.clipboard.writeText`) with green toast feedback.
  - Clean shutdown when the user clicks "Conferma e Chiudi".

---

### 4.3 WhatsApp Plain-Writing Formatter & Sanitizer (`formatter.py`)

```python
import re
from typing import List, Optional
from models import OutingOption, OutingCategory

CATEGORY_EMOJIS = {
    OutingCategory.CINEMA: "🎬",
    OutingCategory.MOSTRA: "🏛️",
    OutingCategory.PASSEGGIATA: "🌿",
    OutingCategory.BIBLIOTECA: "📚",
    OutingCategory.LABORATORIO: "🎭",
    OutingCategory.MUSICA: "🎶",
    OutingCategory.RITROVO: "☕",
    OutingCategory.ALTRO: "📍",
}

def sanitize_plain_writing(text: str) -> str:
    """Sanitizes raw text to strictly conform to plain writing:
    1. Replaces em-dash (\u2014) and en-dash (\u2013) with colon or comma.
    2. Replaces Italian 'le date' with 'i giorni'.
    3. Normalizes whitespace and removes double colons.
    """
    if not text:
        return ""
    # Convert long dashes to colons or commas
    text = re.sub(r'\s*[\u2014\u2013\u2015]\s*', ': ', text)
    text = re.sub(r':\s*:', ':', text)
    # Prevent Italian word 'date' (plural of data)
    text = re.sub(r'\ble\s+date\b', 'i giorni', text, flags=re.IGNORECASE)
    text = re.sub(r'\bdate\b', 'giorni', text, flags=re.IGNORECASE)
    return text.strip()

def format_whatsapp_message(
    selected: List[OutingOption],
    tone: str = "relaxed",
    layout: str = "card",
    include_closing: bool = True
) -> str:
    """Generates copy-paste ready WhatsApp message in natural informal Italian,
    free from long dashes, marketing puffery, and romantic framing.
    """
    if not selected:
        return "Nessuna attività selezionata."

    # Opener based on tone and count
    if tone == "minimal":
        intro = "Ecco le opzioni in programma questa settimana a Genova:"
    elif tone == "weekend":
        intro = "Se hai voglia di fare un salto nel weekend, ho visto queste cose a Genova:"
    else:  # relaxed (default)
        if len(selected) == 1:
            intro = "Ciao! Ho visto questa cosa a Genova questa settimana che sembra interessante se ti va di fare un salto:"
        else:
            intro = "Ciao! Ti lascio un paio di idee carine per questa settimana a Genova se ti va di fare un salto:"

    lines = [intro, ""]

    if layout == "card":
        for opt in selected:
            emoji = CATEGORY_EMOJIS.get(opt.category, "📍")
            clean_title = sanitize_plain_writing(opt.title)
            lines.append(f"{emoji} *{clean_title}*")

            # Location string
            loc_parts = []
            if opt.venue and opt.venue.lower() not in clean_title.lower():
                loc_parts.append(opt.venue)
            if opt.address:
                loc_parts.append(opt.address)
            loc_str = ", ".join(loc_parts)
            if opt.zone:
                loc_str = f"{loc_str} ({opt.zone})" if loc_str else opt.zone
            if loc_str:
                lines.append(f"📍 {loc_str}")

            if opt.days_display:
                clean_days = sanitize_plain_writing(opt.days_display)
                lines.append(f"🗓️ {clean_days}")

            if opt.description:
                clean_desc = sanitize_plain_writing(opt.description)
                lines.append(clean_desc)

            clean_url = opt.source_url.rstrip(".,;:) ")
            lines.append(f"Info: {clean_url}")
            lines.append("")
    else:  # compact layout
        for opt in selected:
            emoji = CATEGORY_EMOJIS.get(opt.category, "•")
            clean_title = sanitize_plain_writing(opt.title)
            clean_url = opt.source_url.rstrip(".,;:) ")
            zone_str = f" ({opt.zone})" if opt.zone else ""
            time_str = f", {opt.days_display}" if opt.days_display else ""
            clean_desc = sanitize_plain_writing(opt.description)
            lines.append(f"• {emoji} *{clean_title}*{zone_str}: {clean_desc}{time_str}. Info: {clean_url}")
        lines.append("")

    if include_closing:
        if len(selected) == 1:
            lines.append("Dimmi se ti ispira!")
        else:
            lines.append("Dimmi se ti ispira qualcosa!")

    return "\n".join(lines).strip()
```

---

### 4.4 Automated Plain-Writing Validation Engine (`validator.py`)

```python
import re
from typing import List, Tuple

class PlainWritingValidator:
    """Automated validator ensuring 100% adherence to Plain Writing and WhatsApp rules."""

    DASH_PATTERN = re.compile(r'[\u2014\u2013\u2015]')

    # Banned romance / date framing keywords
    ROMANCE_PATTERN = re.compile(
        r'\b(date|appuntament[oi]\s+romantic[oi]|serat[ae]\s+a\s+due|uscit[ae]\s+a\s+due|'
        r'galante|romantic[oai]|lume\s+di\s+candela|innamorat[oaie]|fidanzat[oaie]|'
        r'flirt|intimit[aà]|cenett[ae]\s+a\s+due)\b',
        re.IGNORECASE
    )

    # Banned marketing puffery / AI buzzwords
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

        # 1. Check for long dashes
        dash_matches = cls.DASH_PATTERN.findall(text)
        if dash_matches:
            errors.append(('FORBIDDEN_DASH', f'Found prohibited long dashes: {dash_matches}'))

        # 2. Check for romance framing
        romance_matches = cls.ROMANCE_PATTERN.findall(text)
        if romance_matches:
            errors.append(('ROMANTIC_FRAMING', f'Found prohibited romance terms: {romance_matches}'))

        # 3. Check for puffery
        puffery_matches = cls.PUFFERY_PATTERN.findall(text)
        if puffery_matches:
            errors.append(('MARKETING_PUFFERY', f'Found prohibited puffery terms: {puffery_matches}'))

        # 4. WhatsApp bolding syntax
        asterisk_count = text.count('*')
        if asterisk_count % 2 != 0:
            errors.append(('UNBALANCED_ASTERISKS', f'Unbalanced * for WhatsApp bolding ({asterisk_count} total)'))

        # 5. Prohibit double asterisks (markdown bold that fails in WhatsApp)
        if '**' in text:
            errors.append(('DOUBLE_ASTERISKS', 'Found ** markdown bold. WhatsApp uses single *bold*'))

        # 6. Prohibit Markdown headers and markdown links
        if re.search(r'^#{1,6}\s', text, re.MULTILINE):
            errors.append(('MARKDOWN_HEADERS', 'Found markdown headers (#) not supported in WhatsApp'))
        if re.search(r'\[.+?\]\(.+?\)', text):
            errors.append(('MARKDOWN_LINKS', 'Found [text](url) markdown links. WhatsApp requires raw URLs'))

        return errors
```

---

## 5. Verification Method

### 5.1 Automated Test Execution Command
Run the standalone verification test suite:

```bash
python3 -c "
import unittest
from typing import List
from models import OutingOption, OutingCategory
from formatter import format_whatsapp_message, sanitize_plain_writing
from validator import PlainWritingValidator

class TestPlainWriting(unittest.TestCase):
    def setUp(self):
        self.item_cinema = OutingOption(
            id='sivori',
            title='Cinema Sivori: rassegna d\'essai',
            category=OutingCategory.CINEMA,
            venue='Cinema Sivori',
            zone='Centro',
            address='Salita Santa Caterina 12',
            days_display='Mercoledì alle 21:00',
            time_slot='sera',
            description='Proiezione del film d\'autore in versione originale sottotitolata.',
            source_url='https://circuitocinemagenova.com'
        )
        self.item_ducale = OutingOption(
            id='ducale',
            title='Palazzo Ducale: mostra temporanea',
            category=OutingCategory.MOSTRA,
            venue='Palazzo Ducale',
            zone='Centro',
            address='Piazza Matteotti 9',
            days_display='Gio-Dom 10:00-19:00',
            time_slot='pomeriggio',
            description='Esposizione fotografica negli spazi del Munizioniere.',
            source_url='https://palazzoducale.genova.it'
        )

    def test_clean_generation_has_zero_errors(self):
        msg = format_whatsapp_message([self.item_cinema, self.item_ducale])
        errors = PlainWritingValidator.validate(msg)
        self.assertEqual(errors, [], f'Validation errors found: {errors}')

    def test_dash_sanitizer(self):
        raw = '#DomenicalMuseo — Palazzi Reale e Spinola'
        cleaned = sanitize_plain_writing(raw)
        self.assertNotIn('—', cleaned)
        self.assertNotIn('–', cleaned)
        self.assertIn(':', cleaned)

    def test_validator_catches_forbidden_terms(self):
        bad_msg = 'Un date romantico — imperdibile mostra splendida!'
        errors = PlainWritingValidator.validate(bad_msg)
        error_types = [e[0] for e in bad_msg_errors if (bad_msg_errors := errors)]
        self.assertIn('FORBIDDEN_DASH', error_types)
        self.assertIn('ROMANTIC_FRAMING', error_types)
        self.assertIn('MARKETING_PUFFERY', error_types)

    def test_whatsapp_syntax_no_double_asterisks(self):
        bad_bold = '**Titolo**'
        errors = PlainWritingValidator.validate(bad_bold)
        self.assertTrue(any(e[0] == 'DOUBLE_ASTERISKS' for e in errors))

if __name__ == '__main__':
    unittest.main()
"
```

### 5.2 Independent Invalidation Conditions
The design is invalidated if:
1. Any generated WhatsApp message contains an em-dash `—` or en-dash `–` anywhere in the text.
2. Any generated message contains the word "date", "appuntamento romantico", "uscita a due", or romantic framing.
3. Any generated message contains promotional buzzwords ("imperdibile", "splendido", "magico", "esperienza unica", "mozzafiato").
4. The interactive terminal CLI crashes when run on standard Python 3 without external pip dependencies.
5. WhatsApp URLs are rendered with trailing punctuation that breaks mobile clickable previews.
