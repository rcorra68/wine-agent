# 🍷 Wine Agent

Agente Python che legge file CSV e genera automaticamente schede Markdown per **denominazioni vitivinicole** (DOC/DOCG/IGT) e **vitigni**, usando l'API di Claude.

## Struttura del progetto

```
wine-agent/
├── agent.py              ← entry point unificato
├── core/
│   └── utils.py          ← logica condivisa (client, CSV, slugify, runner)
├── modes/
│   ├── denomination.py   ← template + prompt per DOC/DOCG/IGT
│   └── grape.py          ← template + prompt per vitigni
├── data/
│   ├── denominazioni.csv
│   ├── vitigni.csv
└───┴── output/
        ├── denomination/     ← schede denominazioni generate
        └── grape/            ← schede vitigni generate
```

## Requisiti

- Python 3.9+
- Una API key di Anthropic (https://console.anthropic.com/)

```bash
pip install anthropic
```

## Configurazione

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Utilizzo

```bash
# Schede denominazioni
python agent.py --mode denomination --input data/denominazioni.csv

# Schede vitigni
python agent.py --mode grape --input data/vitigni.csv

# Dry-run (senza chiamate API)
python agent.py --mode grape --input data/vitigni.csv --dry-run

# Output personalizzato + rallentamento chiamate
python agent.py --mode grape --input data/vitigni.csv --output mia/cartella/ --delay 2.0
```

## Formato CSV

### Denominazioni

| Colonna | Obbligatoria | Esempio |
| --- | --- | --- |
| `name` | ✅ | `Barolo` |
| `type` | No | `DOCG` |
| `region` | No | `Piemonte` |
| `grape_primary` | No | `Nebbiolo` |
| `year` | No | `1980` |
| `provinces` | No | `Cuneo` |

### Vitigni

| Colonna | Obbligatoria | Esempio |
| --- | --- | --- |
| `name` | ✅ | `Nebbiolo` |
| `color` | No | `rosso` |
| `origin_region` | No | `Piemonte` |

In entrambi i casi basta solo `name`: Claude integra il resto.

## Aggiungere un nuovo tipo di scheda

1. Crea `modes/nuovo_tipo.py` con `build_prompt()`, `render()` e `make_processor()`
2. Aggiungi `"nuovo_tipo": nuovo_tipo` nel dizionario `MODES` in `agent.py`

## Costi API indicativi

Circa $0.01 per scheda con `claude-sonnet-4`.
