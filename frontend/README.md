# Night Market Web GUI

React + TypeScript + Vite frontend for the Cyberpunk RED Night Market generator.

## What this milestone includes

- Core RAW vs Expanded 2045 mode selection.
- Optional deterministic seed.
- Random or unresolved handling for GM-choice slots.
- Generated Night Market sections and item cards.
- Clear RAW/Expanded visual distinction.
- Required foundational cyberware displayed as supplemental availability.
- Expandable item mechanics loaded on demand from `GET /api/items/{id}`.
- Responsive layout suitable for desktop, tablet, and mobile browsers.

## Development

First start the FastAPI backend from the project root:

```bash
python -m uvicorn api.app:app --reload
```

Then, in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

Vite proxies `/api` to `http://127.0.0.1:8000`, so no extra CORS setup is needed for this development flow.

## Different API origin

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Production build

```bash
npm run build
```

The static build is written to `frontend/dist/`.
