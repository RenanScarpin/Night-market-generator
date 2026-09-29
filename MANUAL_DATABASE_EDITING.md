# Manually editing the Night Market item database

The application reads this SQLite file by default:

```text
data/cyberpunk_red_2045_market_ready.sqlite
```

Stop the FastAPI server before editing the database, then make a backup. The safest workflow is either **DB Browser for SQLite** for visual editing or the included `scripts/db_item_admin.py` helper for simple description/mechanics changes.

## Option A — DB Browser for SQLite

1. Stop `uvicorn`.
2. Copy `data/cyberpunk_red_2045_market_ready.sqlite` somewhere safe.
3. Open the database in **DB Browser for SQLite**.
4. Use **Browse Data → items**.
5. Filter `canonical_name` for the item you want.
6. The two fields you will most commonly edit are:
   - `info`: the short description shown above the expandable details.
   - `mechanics_json`: the structured mechanics displayed inside **Mechanics**.
7. Click **Write Changes**.
8. Run the validation command below before starting the backend again.

### Example mechanics JSON

A normal generic weapon record looks like this:

```json
{
  "source": {
    "code": "CP:R",
    "printed_page": 341,
    "pdf_page": 342,
    "match_score": 100.0
  },
  "classification": {
    "primary_category": "Assault Rifles",
    "categories": ["Assault Rifles"]
  },
  "rules": {
    "source_cost_text": "500eb (Expensive)",
    "weapon_skill": "Shoulder Arms",
    "damage_values": ["5d6"],
    "magazine": "25",
    "ammunition_type": "Rifle",
    "rof": 1,
    "hands": 2,
    "concealable": false,
    "alt_fire_modes": "Autofire (4) • Suppressive Fire"
  },
  "special_rules": []
}
```

`mechanics_json` must remain valid JSON. Strings use double quotes, booleans are lowercase `true` / `false`, and there must be no trailing commas.

## Option B — included helper script

From the project root:

```bash
python scripts/db_item_admin.py show "Assault Rifle"
```

Change only the short description:

```bash
python scripts/db_item_admin.py set-info "Some Item" "New short description"
```

Replace structured mechanics using a JSON file:

```bash
python scripts/db_item_admin.py set-mechanics "Some Item" --file my_mechanics.json
```

Every modifying command automatically creates a timestamped backup next to the database.

Validate afterward:

```bash
python scripts/db_item_admin.py validate
```

The validator checks foreign keys, JSON validity, and whether a non-static Core RAW generator slot was accidentally left with zero eligible candidate items.

## Prices

Prices live in `item_prices`, not inside `items` except for the duplicated source text in `mechanics_json.rules.source_cost_text`.

Useful columns are:

- `item_id`: links back to `items.item_id`.
- `cost_eb`: numeric eurobuck cost.
- `price_category_id`: foreign key into `price_categories`.
- `source_price_text`: the human-facing price string shown by the UI.
- `variant_label`: used when one item has multiple prices or variants.

If you manually change a price, update both the numeric price data and any duplicated `source_cost_text` in mechanics when appropriate.

## Categories, manufacturers, aliases, and relationships

- `item_categories`: links an item to one or more `categories`.
- `item_companies`: links to `companies` and stores the role (`manufacturer`, `brand`, etc.).
- `item_aliases`: alternate names and source spellings.
- `item_relations`: `requires`, `includes`, `compatible_with`, `upgrade_for`, and other item-to-item relations.
- `item_market_tags`: generator-specific semantic tags.
- `market_eligibility`: whether the item belongs to a generation profile.

For these tables, prefer editing by `item_id` after finding the item in the `items` table.

## Deleting an item

Deleting an item is more dangerous than editing its text. Many linked rows use `ON DELETE CASCADE`, but the **Core RAW generator** may still need that item as a candidate.

Before deleting an item, check:

```sql
SELECT *
FROM core_raw_stock_matches
WHERE item_id = <ITEM_ID>;
```

If it is the only candidate for a non-static RAW stock row, simply deleting it will make that generator rule impossible to resolve. In that situation either provide another valid candidate or intentionally convert the stock row to a static RAW result.

Always enable foreign keys for manual SQL sessions:

```sql
PRAGMA foreign_keys = ON;
```

Then validate:

```sql
PRAGMA foreign_key_check;
```

The included helper script deliberately does **not** offer a general delete command for this reason.

## Important distinction: source data vs manual presentation cleanup

The source provenance tables should normally remain untouched. Editing `info` or `mechanics_json` changes how the application presents the verified item; it does not change the original source excerpt or source/page references.

For substantial corrections, it is useful to keep a note of what changed. The current database contains a `database_edits` audit table for this purpose.
