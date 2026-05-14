"""
modes/grape.py — Gestione delle schede vitigno.
"""

import json
from core.utils import call_claude, slugify, format_yaml_list

SYSTEM_PROMPT = """\
Sei un esperto ampelografo e scrittore specializzato in vitigni italiani e internazionali.
Rispondi SEMPRE e SOLO con un oggetto JSON valido, senza testo aggiuntivo, senza backtick.
Ogni campo deve essere una stringa o lista di stringhe dove indicato.
Usa linguaggio tecnico ma accessibile. Se un dato non è disponibile, usa "" o [].
"""

def build_prompt(row: dict) -> str:
    return f"""\
Compila la scheda ampelografica per questo vitigno usando i dati forniti e le tue conoscenze.

DATI DISPONIBILI:
{json.dumps(row, ensure_ascii=False, indent=2)}

Rispondi con un oggetto JSON con ESATTAMENTE questi campi:
{{
  "name": "nome ufficiale vitigno",
  "id": "slug-kebab-case",
  "aliases": ["sinonimo1", "sinonimo2"],
  "color": "rosso oppure bianco oppure rosé",
  "origin_country": "paese d'origine es. Italia",
  "origin_region": ["Regione1", "Regione2"],
  "aromatic_profile": "neutro oppure aromatico oppure semi-aromatico",
  "ripening": "precoce oppure medio oppure tardivo",
  "origin_country_text": "paese d'origine per il corpo",
  "origin_region_text": "regione storica d'origine",
  "first_attestation": "prima attestazione storica documentata",
  "berry_type": "bianca / rossa / nera",
  "vigor": "descrizione vigoria della pianta",
  "yield": "resa media es. 80-100 q/ha",
  "ripening_text": "descrizione maturazione con periodo approssimativo",
  "climate_resistance": "resistenza a siccità, freddo, malattie",
  "aroma_notes": "note aromatiche principali (frutti, fiori, spezie, ecc.)",
  "aroma_intensity": "bassa / media / elevata / molto elevata",
  "aroma_evolution": "come evolve il profilo aromatico nel tempo",
  "enological_role": "base / blend / marginale",
  "vinification": "tipologie di vinificazione più comuni",
  "wine_styles": "stili di vino associati (es. vini strutturati da invecchiamento)",
  "aging_potential": "capacità di invecchiamento in anni o descrizione",
  "italian_regions": ["Regione1", "Regione2"],
  "international_spread": "diffusione internazionale",
  "key_denominations": ["[[Denominazione1]]", "[[Denominazione2]]"],
  "similar_grapes": ["[[Vitigno simile1]]"],
  "associated_grapes": ["[[Vitigno associato1]]"],
  "related_denominations": ["[[Denominazione1]]"],
  "name_origin": "origine ed etimologia del nome",
  "history": "storia del vitigno",
  "evolution": "evoluzione nel tempo e riscoperta moderna",
  "ampelographic_curiosities": "curiosità ampelografiche, cloni, mutazioni"
}}
"""

TEMPLATE = """\
---
type: grape
name: "{name}"
id: {id}
aliases: {aliases}
color: {color}
origin_country: {origin_country}
origin_region: {origin_region}
aromatic_profile: {aromatic_profile}
ripening: {ripening}
tags: ["enologia", "enologia/vitigni", "enologia/italia"]
---

# 🍇 {name}

## 🌍 Origine

- **Paese d'origine**: {origin_country_text}
- **Regione storica**: {origin_region_text}
- **Prima attestazione storica**: {first_attestation}

---

## 🌱 Caratteristiche ampelografiche

- **Tipo di bacca**: {berry_type}
- **Vigoria della pianta**: {vigor}
- **Resa media**: {yield}
- **Maturazione**: {ripening_text}
- **Resistenza climatica**: {climate_resistance}

---

## 👃 Profilo aromatico

- **Note principali**: {aroma_notes}
- **Intensità aromatica**: {aroma_intensity}
- **Evoluzione nel tempo**: {aroma_evolution}

---

## 🍷 Ruolo enologico

- **Ruolo principale**: {enological_role}
- **Vinificazione tipica**: {vinification}
- **Stili di vino associati**: {wine_styles}
- **Capacità di invecchiamento**: {aging_potential}

---

## 🌐 Diffusione

- **Regioni principali in Italia**: {italian_regions_text}
- **Diffusione internazionale**: {international_spread}
- **Denominazioni importanti**: {key_denominations_text}

---

## 🧬 Relazioni WineDB

- **Vitigni simili**: {similar_grapes_text}
- **Vitigni spesso associati**: {associated_grapes_text}
- **Denominazioni chiave**: {related_denominations_text}

---

## 🏷️ Note e curiosità

- Origine del nome: {name_origin}
- Storia: {history}
- Evoluzione nel tempo: {evolution}
- Curiosità ampelografiche: {ampelographic_curiosities}

---

## 🧠 Appunti personali

- (impressioni, collegamenti mentali, confronti con altri vitigni)

---

![[wine-classification.base#by-grape]]
"""

def _link_list(items: list) -> str:
    """Converte una lista in testo leggibile con link Obsidian."""
    if not items:
        return ""
    return ", ".join(
        item if item.startswith("[[") else f"[[{item}]]"
        for item in items
    )

def _plain_list(items: list) -> str:
    if not items:
        return ""
    return ", ".join(items)

def render(data: dict) -> str:
    origin_region = data.get("origin_region", [])
    origin_region_fmt = (
        "[" + ", ".join(f'"[[{r}]]"' for r in origin_region) + "]"
        if origin_region else "[]"
    )

    return TEMPLATE.format(
        name=data.get("name", ""),
        id=data.get("id") or slugify(data.get("name", "unknown")),
        aliases=format_yaml_list(data.get("aliases", [])),
        color=data.get("color", ""),
        origin_country=data.get("origin_country", "Italia"),
        origin_region=origin_region_fmt,
        aromatic_profile=data.get("aromatic_profile", ""),
        ripening=data.get("ripening", ""),
        origin_country_text=data.get("origin_country_text", ""),
        origin_region_text=data.get("origin_region_text", ""),
        first_attestation=data.get("first_attestation", ""),
        berry_type=data.get("berry_type", ""),
        vigor=data.get("vigor", ""),
        yield_avg=data.get("yield", ""),
        ripening_text=data.get("ripening_text", ""),
        climate_resistance=data.get("climate_resistance", ""),
        aroma_notes=data.get("aroma_notes", ""),
        aroma_intensity=data.get("aroma_intensity", ""),
        aroma_evolution=data.get("aroma_evolution", ""),
        enological_role=data.get("enological_role", ""),
        vinification=data.get("vinification", ""),
        wine_styles=data.get("wine_styles", ""),
        aging_potential=data.get("aging_potential", ""),
        italian_regions_text=_plain_list(data.get("italian_regions", [])),
        international_spread=data.get("international_spread", ""),
        key_denominations_text=_link_list(data.get("key_denominations", [])),
        similar_grapes_text=_link_list(data.get("similar_grapes", [])),
        associated_grapes_text=_link_list(data.get("associated_grapes", [])),
        related_denominations_text=_link_list(data.get("related_denominations", [])),
        name_origin=data.get("name_origin", ""),
        history=data.get("history", ""),
        evolution=data.get("evolution", ""),
        ampelographic_curiosities=data.get("ampelographic_curiosities", ""),
    )


def make_processor(client):
    """Restituisce la funzione process(row) → (slug, markdown)."""
    def process(row: dict) -> tuple[str, str]:
        data = call_claude(client, SYSTEM_PROMPT, build_prompt(row))
        slug = data.get("id") or slugify(data.get("name", "unknown"))
        return slug, render(data)
    return process
