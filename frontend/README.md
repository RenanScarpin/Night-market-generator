# Night Market Web GUI

React + TypeScript + Vite frontend for the Cyberpunk RED Night Market generator.

## Current milestone

The GUI now includes both the session-ready generator and the first complete Catalogue browser:

- Core RAW vs Expanded 2045 mode selection.
- Optional deterministic seed.
- Random or unresolved handling for GM-choice slots.
- Generated Night Market sections and item cards.
- Clear RAW/Expanded visual distinction.
- Required foundational cyberware displayed as supplemental availability.
- Expandable item mechanics loaded on demand from `GET /api/items/{id}`.
- Responsive layout suitable for desktop, tablet, and mobile browsers.
- Client-side `/market` route using the browser History API.
- Deterministic market URLs, for example:

  ```text
  /market?seed=2045&mode=expanded_2045&gmChoice=random
  ```

- Opening a deterministic URL automatically regenerates the market from FastAPI.
- Browser back/forward navigation between generated markets.
- Recent Markets stored locally in the browser (up to 12 unique seed/mode/settings combinations).
- Reopen and remove recent markets; clear local market history.
- `Regenerate`, `New random`, and `Copy link` actions.
- Last-used generation mode and GM-choice behavior persisted in `localStorage`.

- A `/catalogue` route for browsing the complete 1,150-item canon-2045 database.
- Catalogue search by canonical name or known alias.
- Filters for source/index category, market semantic tag, explicit manufacturer, and eurobuck price range.
- Filter state encoded in the URL so searches can be bookmarked or shared.
- Responsive 24-item result pages with expandable mechanics/source/relationship details.
- Manufacturer filter options loaded from `GET /api/manufacturers`.

Browser-specific routing, storage, and clipboard code lives under
`src/platform/browser/` so those concerns can later be replaced with mobile
navigation/storage implementations for React Native / Expo.

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

Open `http://127.0.0.1:5173`. The root path automatically redirects to `/market`.

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

Because the GUI now uses client-side routes such as `/market`, a production
static host must fall back unknown application paths to `index.html`.

## Local browser data

The GUI currently stores only convenience data in the browser:

- the last-used generator settings;
- up to 12 recent deterministic market references.

The generated inventory itself is not persisted. Reopening a recent entry asks
the backend to regenerate it from the saved seed/settings.
