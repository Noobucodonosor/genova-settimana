"""Unified CLI for genova_outings (supports both Italian and English flags)."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from genova_outings.catalog import get_weekly_catalog
from genova_outings.formatter import format_whatsapp_message
from genova_outings.selector import parse_selection_indices, run_terminal_selector
from genova_outings.validator import validate_plain_writing


def _print_list(options) -> None:
    current = None
    for i, o in enumerate(options, 1):
        cat = o.category.value
        if cat != current:
            current = cat
            print(f"\n[{cat.upper()}]")
        print(f"{i:3d}. {o.title}")
        print(f"     {o.venue}, {o.zone} | {o.day_time}")
        print(f"     fonte: {o.verified_url}")


def _emit(message: str, out: Optional[str]) -> int:
    ok, issues = validate_plain_writing(message)
    print(message)
    if not ok:
        print("Avvisi di stile:", "; ".join(issues), file=sys.stderr)
    if out:
        try:
            Path(out).write_text(message, encoding="utf-8")
            print(f"Salvato in {out}", file=sys.stderr)
        except OSError as exc:
            print(f"Errore scrittura file {out}: {exc}", file=sys.stderr)
            return 1
    try:
        import subprocess
        subprocess.run(["pbcopy"], input=message.encode("utf-8"), check=True)
        print("Copiato anche negli appunti.", file=sys.stderr)
    except Exception:
        pass
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="genova_outings",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    g = p.add_mutually_exclusive_group()
    g.add_argument("--terminale", "--terminal", dest="terminale", action="store_true", help="spunta da terminale")
    g.add_argument("--lista", "--list", dest="lista", action="store_true", help="stampa l'elenco e termina")
    g.add_argument("--scegli", "--select", dest="scegli", metavar="NUMERI", help="es. 1,3,5-7")
    p.add_argument("--categoria", "--category", dest="categoria", help="filtra per categoria")
    p.add_argument("--tono", "--tone", dest="tono", default="amichevole", help="tono messaggio (amichevole, weekend, minimal)")
    p.add_argument("--no-verifica", "--no-live", dest="no_verifica", action="store_true", help="non controllare i siti in rete")
    p.add_argument("--out", "--output", dest="out", help="salva il messaggio in un file")
    p.add_argument("--porta", "--port", dest="porta", type=int, default=8765)
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = build_parser()
    a = p.parse_args(argv)

    tone = a.tono if a.tono in ("amichevole", "weekend", "minimal") else "amichevole"

    print("Raccolgo e verifico le alternative della settimana...", file=sys.stderr)
    options = get_weekly_catalog(live_verify=not a.no_verifica, category=a.categoria)
    options.sort(key=lambda o: (o.category.value, o.title))
    print(f"{len(options)} alternative verificate.", file=sys.stderr)
    if not options:
        return 1
    if not a.no_verifica:
        from genova_outings.programme import attach_programmes
        print("Leggo la programmazione dai siti dei locali...", file=sys.stderr)
        n = attach_programmes(options)
        print(f"Programma attuale trovato per {n} schede.", file=sys.stderr)

    if a.lista:
        _print_list(options)
        return 0
    if a.scegli is not None:
        idx = parse_selection_indices(a.scegli, len(options))
        chosen = [options[i] for i in idx]
        if not chosen:
            print("Nessuna voce valida selezionata.", file=sys.stderr)
            return 1
        return _emit(format_whatsapp_message(chosen, tone=tone), a.out)
    if a.terminale:
        chosen = run_terminal_selector(options)
        if not chosen:
            print("Nessuna voce selezionata.", file=sys.stderr)
            return 0
        return _emit(format_whatsapp_message(chosen, tone=tone), a.out)

    from genova_outings.web_ui import start_web_ui
    start_web_ui(catalog=options, port=a.porta, open_browser=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
