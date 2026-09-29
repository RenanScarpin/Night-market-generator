# Cyberpunk RED Night Market Generator

A deterministic Night Market generator backed by the canon-2045 item database.

## What is implemented

### `core_raw`

Implements the Core Rulebook Night Market procedure:

1. Roll `1d6` twice for two different market categories.
2. Roll `1d10` for the number of stock types in each category.
3. Roll `d100` for each stock type.
4. Reroll duplicate **table results** within the same category.
5. Preserve the RAW table result and RAW printed price as written.

This mode deliberately **does not** replace broad RAW entries with newer
supplement items.

### `expanded_2045`

Uses the exact same category and d100 rolls, but resolves non-static table
slots to concrete canon-2045 database records wherever the market layer has
eligible candidates.

- Candidate selection is uniform.
- The generator avoids selecting the same concrete item twice.
- RAW "GM's choice" entries support `random`, `leave`, and interactive
  `prompt` behavior.
- When a cyberware option requires foundational cyberware, the required
  foundation is added as supplemental availability and does not consume an
  additional stock roll.
- Static RAW results such as canned goods remain static instead of creating
  artificial item database records.

## Determinism

Every market has an integer seed. Reusing the same seed, mode, database, and
GM-choice setting reproduces the same result.

If no seed is provided, the generator creates one and prints it.

## Run it

Requires Python 3.10+ and uses only the standard library.

```bash
cd cyberpunk_night_market_generator
python -m nightmarket generate --mode expanded_2045 --seed 12345
```

RAW mode:

```bash
python -m nightmarket generate --mode core_raw --seed 12345
```

JSON:

```bash
python -m nightmarket generate \
  --mode expanded_2045 \
  --seed 12345 \
  --format json \
  --output examples/market_12345.json
```

Markdown:

```bash
python -m nightmarket generate \
  --mode expanded_2045 \
  --seed 12345 \
  --format markdown \
  --output examples/market_12345.md
```

Interactive GM choice:

```bash
python -m nightmarket generate \
  --mode expanded_2045 \
  --gm-choice prompt
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Project layout

```text
nightmarket/
  models.py       Structured generated-market objects
  repository.py   Read-only SQLite access
  generator.py    Seeded RAW + expanded generation engine
  renderers.py    Text / JSON / Markdown outputs
  cli.py          Command-line interface

data/
  cyberpunk_red_2045_market_ready.sqlite

tests/
  test_generator.py
```

## Important RAW discrepancy preserved

The Core Night Market d100 table prints **Very Heavy Melee Weapon —
100eb (Premium)**, even though the canonical Very Heavy Melee Weapon entry
elsewhere in the Core Rulebook is 500eb (Expensive).

The RAW mode preserves the Night Market table exactly rather than silently
"correcting" it.

## Next layer

The generator engine is intentionally independent of any web framework. A
future FastAPI/GUI layer can import `NightMarketGenerator` directly without
duplicating generation rules.
