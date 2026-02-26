# budget_tool

`budget_tool` is een Python-based budgetanalyse MVP voor het inlezen, normaliseren, categoriseren en rapporteren van transacties.

## Features

- CSV import met generieke kolommapping via YAML-config.
- Canoniek intern transactiemodel:
  - `date` (`YYYY-MM-DD`)
  - `amount` (`float`, negatief=uitgave, positief=inkomen)
  - `description` (`str`)
  - `account` (`str`, optioneel)
  - `tx_id` (hash voor deduplicatie)
- Regelgebaseerde categorisatie met fallback `Ongecategoriseerd`.
- Maandrapporten met:
  - inkomsten per categorie
  - uitgaven per categorie
  - netto cashflow
  - top 10 descriptions/merchants
- Export naar Excel en HTML.
- Parquet tussenstappen.
- Web dashboard voor pipeline-run, preview en report downloads.

## Installatie

```bash
pip install -r requirements.txt
pip install -e .
```

## Configuratiebestanden

- `import_config.yml` – voorbeeld voor CSV-kolommen.
- `categories.yml` – definitieve categorie-structuur.
- `rules.yml` – lege overrides en pattern rules om later te vullen.

## CLI gebruik

### 1) Import

```bash
budget import --csv data/sample_generic.csv --config import_config.yml --out normalized.parquet
```

### 2) Categorize

```bash
budget categorize --in normalized.parquet --rules rules.yml --categories categories.yml --out categorized.parquet
```

### 3) Report

```bash
budget report --month 2024-01 --in categorized.parquet --out reports/
```

Dit maakt:
- `reports/budget_report_2024-01.xlsx`
- `reports/budget_report_2024-01.html`

## Web dashboard

Start de website lokaal:

```bash
budget-web
```

Open daarna in je browser:

```text
http://localhost:8000
```

Wat je kunt doen in de UI:
- CSV pad invullen (standaard `data/sample_generic.csv`)
- Pipeline draaien (import + categorize)
- Optioneel direct een maandrapport genereren
- Maandpreview bekijken
- XLSX/HTML rapporten downloaden

## Voorbeelddata

- `data/sample_generic.csv` bevat 30 neptranacties.

## Tests

```bash
pytest
```

Geteste onderdelen:
- CSV → canonieke mapping
- categorisatie + fallback
- rapportberekeningen voor sample data
- webpagina routes
