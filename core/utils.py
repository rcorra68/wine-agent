"""
core/utils.py — Logica condivisa tra tutti i mode dell'agente.
"""

import os
import re
import csv
import json
import time
from pathlib import Path
import anthropic


# ── Client Anthropic ───────────────────────────────────────────────────────────

def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Variabile d'ambiente ANTHROPIC_API_KEY non impostata.\n"
            "Esegui: export ANTHROPIC_API_KEY='sk-ant-...'"
        )
    return anthropic.Anthropic(api_key=api_key)


# ── Helpers ────────────────────────────────────────────────────────────────────

def extract_type(name: str):
    match = re.search(r"\b(DOCG|DOC|IGT)\b$", name)
    if match:
        return match.group(1)
    return ""


def slugify(text: str) -> str:
    text = text.lower().strip()
    for src, dst in [("àáâã","a"),("èéêë","e"),("ìíîï","i"),("òóôõ","o"),("ùúûü","u")]:
        for ch in src:
            text = text.replace(ch, dst)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def format_yaml_list(items) -> str:
    if not items:
        return "[]"
    if isinstance(items, str):
        items = [i.strip() for i in items.split(",") if i.strip()]
    return "[" + ", ".join(f'"{i}"' for i in items) + "]"


def call_claude(client, system, user, max_tokens=4096, retries=2):
    for attempt in range(retries + 1):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            raw = message.content[0].text.strip()
            raw = re.sub(r"^```json\s*|^```\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
            return json.loads(raw)
        except json.JSONDecodeError:
            if attempt < retries:
                print(f"(retry {attempt+1}/{retries})", end=" ", flush=True)
                time.sleep(2)
            else:
                raise

# ── CSV reader ─────────────────────────────────────────────────────────────────

def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── Runner generico ────────────────────────────────────────────────────────────

def run_agent(rows: list[dict], process_fn, output_dir: Path,
              dry_run: bool, delay: float, label: str):
    """
    Itera sulle righe e chiama process_fn(row) → (slug, markdown_content).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    total = len(rows)
    print(f"\n🍷 Wine Agent [{label}] — {total} voci da elaborare\n")

    ok, fail = 0, 0
    for i, row in enumerate(rows, 1):
        name = row.get("name") or row.get("nome") or f"voce_{i}"
        print(f"[{i}/{total}] {name} ...", end=" ", flush=True)

        if dry_run:
            print("(dry-run, skipped)")
            ok += 1
            continue

        try:
            slug, content = process_fn(row)
            out_path = output_dir / f"{slug}.md"
            out_path.write_text(content, encoding="utf-8")
            print(f"✓  → {out_path.name}")
            ok += 1
        except json.JSONDecodeError as e:
            print(f"✗  Errore JSON: {e}")
            fail += 1
        except Exception as e:
            print(f"✗  Errore: {e}")
            fail += 1

        if i < total:
            time.sleep(delay)

    print(f"\n✅ Completato: {ok} generati, {fail} errori")
    print(f"📁 Output: {output_dir.resolve()}")
