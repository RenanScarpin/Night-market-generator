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

## FastAPI backend

The project now includes an HTTP API designed to be the backend for the future
web GUI.

Install the API dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the development server from the project root:

```bash
python -m uvicorn api.app:app --reload
```

Then open:

- API documentation: `http://127.0.0.1:8000/docs`
- OpenAPI document: `http://127.0.0.1:8000/openapi.json`
- Health check: `http://127.0.0.1:8000/api/health`

### Main API contract

Generate a market:

```http
POST /api/markets/generate
Content-Type: application/json
```

```json
{
  "mode": "expanded_2045",
  "seed": 2045,
  "gm_choice": "random"
}
```

`seed` may be omitted. The generated seed is returned in the response.

Regenerate an existing deterministic market:

```http
GET /api/markets/2045?mode=expanded_2045&gm_choice=random
```

Catalogue endpoints:

```text
GET /api/items
GET /api/items/{item_id}
GET /api/categories
GET /api/tags
GET /api/market-categories
GET /api/meta
GET /api/health
```

`GET /api/items` currently supports these filters:

```text
q
category
tag
manufacturer
item_kind
min_cost_eb
max_cost_eb
limit
offset
```

Examples:

```http
GET /api/items?q=Militech&limit=20
GET /api/items?tag=weapon.medium_pistol
GET /api/items?min_cost_eb=500&max_cost_eb=1000
```

The HTTP contract intentionally supports only `gm_choice=random` and
`gm_choice=leave`. Interactive `prompt` remains a CLI-only behavior. A future
GUI can use `leave` and present GM-choice resolution in the browser.

### CORS

Development CORS is enabled for the common frontend ports:

```text
http://localhost:3000
http://127.0.0.1:3000
http://localhost:5173
http://127.0.0.1:5173
```

Override this with the comma-separated `NIGHTMARKET_CORS_ORIGINS`
environment variable.

You can also point the API at another compatible database with
`NIGHTMARKET_DB`. See `.env.example`.

### API tests

Install development dependencies and run the whole test suite:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```


## React web GUI

The first usable web GUI is in `frontend/`.

It currently provides:

- Core RAW and Expanded 2045 generation modes.
- Optional deterministic seed input.
- Random or unresolved handling of GM-choice slots.
- Responsive Night Market cards for desktop, tablet, and mobile browsers.
- A clear visual distinction between RAW table results and expanded catalogue resolutions.
- Supplemental foundational cyberware displayed under the option that caused it to become available.
- Expandable mechanics, relationships, categories, prices, and source information loaded from the FastAPI item endpoint.

Run the backend from the project root:

```bash
python -m uvicorn api.app:app --reload
```

Then run the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

The Vite development server proxies `/api` to FastAPI on port 8000. If the API is hosted somewhere else, copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_BASE_URL`.

The frontend is deliberately split into API, types, components, pages, and utility layers so these pieces can later be extracted into shared packages for a React Native / Expo mobile client.

### Session-friendly market URLs and local history

The web GUI now treats generated markets as deterministic routes. A market can
be shared or reopened with a URL such as:

```text
http://127.0.0.1:5173/market?seed=2045&mode=expanded_2045&gmChoice=random
```

The browser client automatically regenerates that market through FastAPI. It
also keeps up to 12 recent markets in local browser storage, persists the
last-used mode / GM-choice settings, supports browser back/forward navigation,
and adds Regenerate, New Random, and Copy Link controls.

Browser-only routing, storage, and clipboard behavior is isolated under
`frontend/src/platform/browser/` so the generator/API-facing logic stays easy
to reuse later in a React Native / Expo client.
