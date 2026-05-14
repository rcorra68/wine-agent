"""
Wine Agent — Entry point unificato
===================================
Uso:
    python agent.py --mode denomination --input data/denominazioni.csv
    python agent.py --mode grape        --input data/vitigni.csv

Opzioni:
    --output DIR     Directory di output (default: data/output/<mode>/)
    --delay FLOAT    Secondi tra chiamate API (default: 1.0)
    --dry-run        Simula senza chiamare l'API
"""

import argparse
from pathlib import Path

from core.utils import get_client, read_csv, run_agent
from modes import denomination, grape


MODES = {
    "denomination": denomination,
    "grape": grape,
}


def main():
    parser = argparse.ArgumentParser(
        description="Wine Agent — genera schede Markdown per denominazioni e vitigni"
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=list(MODES.keys()),
        help="Tipo di scheda da generare: denomination | grape",
    )
    parser.add_argument("--input",  required=True, help="Percorso al file CSV")
    parser.add_argument("--output", default=None,  help="Directory di output")
    parser.add_argument("--delay",  type=float, default=1.0,
                        help="Secondi tra chiamate API (default: 1.0)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simula senza chiamare l'API")
    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else Path("data/output") / args.mode
    rows = read_csv(Path(args.input))
    mode_module = MODES[args.mode]

    client = None if args.dry_run else get_client()
    process_fn = mode_module.make_processor(client)

    run_agent(
        rows=rows,
        process_fn=process_fn,
        output_dir=output_dir,
        dry_run=args.dry_run,
        delay=args.delay,
        label=args.mode,
    )


if __name__ == "__main__":
    main()
