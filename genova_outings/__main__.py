"""Comando unico: estrai le alternative della settimana, spunta, genera il messaggio WhatsApp.

Uso:
    python3 -m genova_outings              # interfaccia web con checkbox (consigliata)
    python3 -m genova_outings --terminale  # spunta da terminale
    python3 -m genova_outings --lista      # stampa solo l'elenco numerato
    python3 -m genova_outings --scegli 1,4,7-9   # genera subito il messaggio
Opzioni: --categoria cinema|mostra|..., --no-verifica (salta i controlli di rete), --out file.txt
"""

import argparse
import sys
from pathlib import Path

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


def _emit(message: str, out: str | None) -> None:
    ok, issues = validate_plain_writing(message)
    print("\n" + "=" * 60 + "\nMESSAGGIO WHATSAPP (copia da qui)\n" + "=" * 60)
    print(message)
    print("=" * 60)
    if not ok:
        print("Avvisi di stile:", "; ".join(issues), file=sys.stderr)
    if out:
        Path(out).write_text(message, encoding="utf-8")
        print(f"Salvato in {out}")
    try:
        import subprocess
        subprocess.run(["pbcopy"], input=message.encode("utf-8"), check=True)
        print("Copiato anche negli appunti.")
    except Exception:
        pass


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="genova_outings", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--terminale", action="store_true", help="spunta da terminale")
    g.add_argument("--lista", action="store_true", help="stampa l'elenco e termina")
    g.add_argument("--scegli", metavar="NUMERI", help="es. 1,3,5-7")
    p.add_argument("--categoria", help="filtra per categoria")
    p.add_argument("--no-verifica", action="store_true", help="non controllare i siti in rete")
    p.add_argument("--out", help="salva il messaggio in un file")
    p.add_argument("--porta", type=int, default=8765)
    a = p.parse_args(argv)

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
    if a.scegli:
        idx = parse_selection_indices(a.scegli, len(options))
        chosen = [options[i] for i in idx]
        if not chosen:
            print("Nessuna voce valida selezionata.", file=sys.stderr)
            return 2
        _emit(format_whatsapp_message(chosen), a.out)
        return 0
    if a.terminale:
        chosen = run_terminal_selector(options)
        if not chosen:
            print("Nessuna voce selezionata.")
            return 0
        _emit(format_whatsapp_message(chosen), a.out)
        return 0

    from genova_outings.web_ui import start_web_ui
    start_web_ui(catalog=options, port=a.porta, open_browser=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
