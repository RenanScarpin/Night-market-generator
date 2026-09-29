from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "cyberpunk_red_2045_market_ready.sqlite"


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def backup(path: Path) -> Path:
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    target = path.with_name(f"{path.stem}.manual_backup_{stamp}{path.suffix}")
    shutil.copy2(path, target)
    return target


def find_item(con: sqlite3.Connection, name: str) -> sqlite3.Row:
    rows = con.execute(
        "SELECT item_id,canonical_name,slug,info,mechanics_json,item_kind FROM items WHERE lower(canonical_name)=lower(?)",
        (name,),
    ).fetchall()
    if not rows:
        suggestions = con.execute(
            "SELECT canonical_name FROM items WHERE lower(canonical_name) LIKE lower(?) ORDER BY canonical_name LIMIT 15",
            (f"%{name}%",),
        ).fetchall()
        hint = ", ".join(r[0] for r in suggestions)
        raise SystemExit(f"Item not found: {name}" + (f"\nPossible matches: {hint}" if hint else ""))
    if len(rows) > 1:
        raise SystemExit(f"More than one exact case-insensitive match for {name!r}; edit by SQLite directly.")
    return rows[0]


def cmd_show(args) -> None:
    with connect(args.db) as con:
        item = find_item(con, args.name)
        print(f"ID: {item['item_id']}")
        print(f"Name: {item['canonical_name']}")
        print(f"Kind: {item['item_kind']}")
        print(f"Info: {item['info']!r}")
        print("Mechanics:")
        if item["mechanics_json"]:
            print(json.dumps(json.loads(item["mechanics_json"]), ensure_ascii=False, indent=2))
        else:
            print("null")
        print("Prices:")
        for row in con.execute(
            "SELECT source_price_text,cost_eb,price_kind FROM item_prices WHERE item_id=? ORDER BY item_price_id",
            (item["item_id"],),
        ):
            print(f"  - {row['source_price_text']} (cost_eb={row['cost_eb']}, kind={row['price_kind']})")
        print("Categories:")
        for row in con.execute(
            "SELECT c.name,ic.is_primary FROM item_categories ic JOIN categories c USING(category_id) WHERE ic.item_id=? ORDER BY ic.is_primary DESC,c.name",
            (item["item_id"],),
        ):
            print(f"  - {row['name']}{' [primary]' if row['is_primary'] else ''}")


def cmd_set_info(args) -> None:
    b = backup(args.db)
    with connect(args.db) as con:
        item = find_item(con, args.name)
        con.execute("UPDATE items SET info=? WHERE item_id=?", (args.text, item["item_id"]))
        con.commit()
    print(f"Updated info for {args.name}. Backup: {b}")


def cmd_set_mechanics(args) -> None:
    data = json.loads(args.file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("Mechanics JSON must be a JSON object.")
    encoded = json.dumps(data, ensure_ascii=False)
    b = backup(args.db)
    with connect(args.db) as con:
        item = find_item(con, args.name)
        con.execute("UPDATE items SET mechanics_json=? WHERE item_id=?", (encoded, item["item_id"]))
        con.commit()
    print(f"Updated mechanics for {args.name}. Backup: {b}")


def cmd_validate(args) -> None:
    with connect(args.db) as con:
        fk = con.execute("PRAGMA foreign_key_check").fetchall()
        bad_json = con.execute(
            "SELECT item_id,canonical_name FROM items WHERE mechanics_json IS NOT NULL AND json_valid(mechanics_json)=0"
        ).fetchall()
        zero_candidates = []
        table_exists = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='core_raw_stock_rolls'"
        ).fetchone()
        if table_exists:
            zero_candidates = con.execute(
                """
                SELECT stock_roll_id,category_code,d100_min,d100_max,display_text
                FROM core_raw_stock_rolls r
                WHERE resolution_mode <> 'static'
                  AND NOT EXISTS (
                      SELECT 1 FROM core_raw_stock_matches m WHERE m.stock_roll_id=r.stock_roll_id
                  )
                ORDER BY stock_roll_id
                """
            ).fetchall()
        print(f"Foreign-key errors: {len(fk)}")
        print(f"Invalid mechanics JSON rows: {len(bad_json)}")
        print(f"Non-static RAW stock rows with zero candidates: {len(zero_candidates)}")
        if zero_candidates:
            for row in zero_candidates:
                print("  -", dict(row))
        if fk or bad_json or zero_candidates:
            raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Small safe helper for manual item edits.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="Show an item's current database record.")
    show.add_argument("name")
    show.set_defaults(func=cmd_show)

    info = sub.add_parser("set-info", help="Replace only the human-facing description.")
    info.add_argument("name")
    info.add_argument("text")
    info.set_defaults(func=cmd_set_info)

    mechanics = sub.add_parser("set-mechanics", help="Replace mechanics_json from a JSON file.")
    mechanics.add_argument("name")
    mechanics.add_argument("--file", type=Path, required=True)
    mechanics.set_defaults(func=cmd_set_mechanics)

    validate = sub.add_parser("validate", help="Run integrity checks after manual edits.")
    validate.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
