"""
modes/denomination.py — Gestione delle denominazioni DOC/DOCG/IGT.
"""

import json
from core.utils import call_claude, slugify, format_yaml_list

SYSTEM_PROMPT = """\
Sei un esperto enologo specializzato in denominazioni vitivinicole italiane (DOC, DOCG, IGT).
Rispondi SEMPRE e SOLO con un oggetto JSON valido, senza testo aggiuntivo, senza backtick.
Ogni campo deve essere una stringa o lista di stringhe dove indicato.
Usa linguaggio tecnico ma accessibile. Se un dato non è disponibile, usa "" o [].
"""

def build_prompt(row: dict) -> str:
    return f"""\
Compila la scheda per questa denominazione italiana usando i dati forniti e le tue conoscenze.

DATI DISPONIBILI:
{json.dumps(row, ensure_ascii=False, indent=2)}

Rispondi con un oggetto JSON con ESATTAMENTE questi campi:
{{
  "type": "DOCG oppure DOC oppure IGT",
  "name": "nome ufficiale denominazione",
  "id": "slug-kebab-case",
  "aliases": ["alias1"],
  "year": "anno riconoscimento",
  "region": "regione italiana",
  "subregions": ["sottozona1"],
  "provinces": ["Prov1"],
  "grape_primary": "vitigno principale",
  "grape_primary_min": "percentuale minima es. 85",
  "grape_secondary": ["Vitigno2", "Vitigno3"],
  "aging_min": "mesi invecchiamento base",
  "aging_min_riserva": "mesi invecchiamento riserva o stringa vuota",
  "tipologies": ["Denominazione base", "Denominazione Riserva"],
  "production_area": "1-2 frasi sull'area produttiva",
  "climate": "breve descrizione clima",
  "soils": "breve descrizione suoli",
  "geo_description": "descrizione geografica",
  "altitude": "es. 200-400 m s.l.m.",
  "distinctive_factors": "vento, esposizione, microclima, ecc.",
  "grape_secondary_text": "elenco vitigni secondari come testo",
  "grape_secondary_role": "funzione enologica dei secondari",
  "yield_per_hectare": "es. 70 q/ha",
  "min_alcohol": "es. 12%",
  "winemaking_techniques": "tecniche particolari o 'Nessuna tecnica particolare'",
  "color": "descrizione colore",
  "aroma": "descrizione profumi",
  "taste": "descrizione gusto",
  "structure": "corpo, tannini, acidità",
  "persistence": "finale e persistenza",
  "tipologies_detail": [
    {{"name": "Riserva", "sensory": "caratteristiche sensoriali", "notes": "note disciplinari"}}
  ],
  "food_pairings": "piatti abbinabili",
  "occasions": "aperitivo, pasto, meditazione...",
  "history": "storia e origini",
  "producers": "principali produttori",
  "curiosities": "curiosità, premi, peculiarità"
}}
"""

TIPOLOGY_BLOCK = """\
#### {name}

- **Caratteristiche sensoriali**: {sensory}
- **Note disciplinari specifiche** (es. invecchiamento, alcol): {notes}
"""

TEMPLATE = """\
---
type: {type}
name: {name}
id: {id}
aliases: {aliases}
year: {year}
region: "[[{region}]]"
subregions: {subregions}
provinces: {provinces}
grape_primary:
  - "[[{grape_primary}]]"
grape_primary_min: {grape_primary_min}
grape_secondary: {grape_secondary}
aging_min: {aging_min}
aging_min_riserva: {aging_min_riserva}
tipologies:
{tipologies_yaml}
production_area: "{production_area}"
climate: "{climate}"
soils: "{soils}"
tags: ["enologia", "enologia/italia", "enologia/regioni"]
---

# 🍷 [[{name}]]

## 🌄 Descrizione del Territorio

- **Descrizione area geografica**: {geo_description}
- **Altitudine media**: {altitude}
- **Clima**: {climate}
- **Suolo**: {soils}
- **Fattori distintivi (vento, esposizione, ecc.)**: {distinctive_factors}

---

## 🍇 Vitigni principali e secondari

- **Vitigno principale**: {grape_primary}
- **Percentuale minima**: {grape_primary_min}%
- **Vitigni secondari ammessi**: {grape_secondary_text}
- **Funzione dei secondari** (es. addolcire, acidificare, complessificare): {grape_secondary_role}

---

## ⚙️ Disciplinare

- **Resa per ettaro**: {yield_per_hectare}
- **Gradazione minima**: {min_alcohol}
- **Invecchiamento minimo (base)**: {aging_min} mesi
- **Invecchiamento minimo (Riserva)**: {aging_min_riserva} mesi
- **Tecniche di vinificazione particolari**: {winemaking_techniques}

---

## 👃 Caratteristiche organolettiche (denominazione base)

- **Colore**: {color}
- **Profumo**: {aroma}
- **Gusto**: {taste}
- **Struttura**: {structure}
- **Persistenza**: {persistence}

{tipologies_section}

---

## 🍽️ Abbinamenti gastronomici

- **Piatti tipici**: {food_pairings}
- **Occasioni d'uso**: {occasions}

---

## 🏷️ Note e curiosità

- **Storia della denominazione**: {history}
- **Produttori importanti**: {producers}
- **Eventuali controversie o peculiarità**: {curiosities}
"""

def _render_tipologies_section(tipologies_detail: list) -> str:
    if not tipologies_detail:
        return ""
    blocks = "\n".join(
        TIPOLOGY_BLOCK.format(
            name=t.get("name", ""),
            sensory=t.get("sensory", ""),
            notes=t.get("notes", ""),
        )
        for t in tipologies_detail
    )
    return "### 🍷 Tipologie specifiche (se presenti)\n\n" + blocks


def render(data: dict) -> str:
    gs = data.get("grape_secondary", [])
    grape_secondary_fmt = (
        "[" + ", ".join(f'"[[{g}]]"' for g in gs) + "]" if gs else "[]"
    )
    tipologies_yaml = "\n".join(
        f'  - "{t}"' for t in data.get("tipologies", ["Denominazione base"])
    )
    return TEMPLATE.format(
        type=data.get("type", ""),
        name=data.get("name", ""),
        id=data.get("id") or slugify(data.get("name", "unknown")),
        aliases=format_yaml_list(data.get("aliases", [])),
        year=data.get("year", ""),
        region=data.get("region", ""),
        subregions=format_yaml_list(data.get("subregions", [])),
        provinces=format_yaml_list(data.get("provinces", [])),
        grape_primary=data.get("grape_primary", ""),
        grape_primary_min=data.get("grape_primary_min", ""),
        grape_secondary=grape_secondary_fmt,
        aging_min=data.get("aging_min", ""),
        aging_min_riserva=data.get("aging_min_riserva", ""),
        tipologies_yaml=tipologies_yaml,
        production_area=data.get("production_area", ""),
        climate=data.get("climate", ""),
        soils=data.get("soils", ""),
        geo_description=data.get("geo_description", ""),
        altitude=data.get("altitude", ""),
        distinctive_factors=data.get("distinctive_factors", ""),
        grape_secondary_text=data.get("grape_secondary_text", ""),
        grape_secondary_role=data.get("grape_secondary_role", ""),
        yield_per_hectare=data.get("yield_per_hectare", ""),
        min_alcohol=data.get("min_alcohol", ""),
        winemaking_techniques=data.get("winemaking_techniques", ""),
        color=data.get("color", ""),
        aroma=data.get("aroma", ""),
        taste=data.get("taste", ""),
        structure=data.get("structure", ""),
        persistence=data.get("persistence", ""),
        tipologies_section=_render_tipologies_section(data.get("tipologies_detail", [])),
        food_pairings=data.get("food_pairings", ""),
        occasions=data.get("occasions", ""),
        history=data.get("history", ""),
        producers=data.get("producers", ""),
        curiosities=data.get("curiosities", ""),
    )


def make_processor(client):
    """Restituisce la funzione process(row) → (slug, markdown)."""
    def process(row: dict) -> tuple[str, str]:
        data = call_claude(client, SYSTEM_PROMPT, build_prompt(row))
        slug = data.get("id") or slugify(data.get("name", "unknown"))
        return slug, render(data)
    return process
