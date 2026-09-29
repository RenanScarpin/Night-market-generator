from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sqlite3
from pathlib import Path

RANGED_RULES = {
    "Medium Pistol": {"weapon_skill": "Handgun", "damage_values": ["2d6"], "magazine": "12", "ammunition_type": "M Pistol", "rof": 2, "hands": 1, "concealable": True, "alt_fire_modes": "None"},
    "Heavy Pistol": {"weapon_skill": "Handgun", "damage_values": ["3d6"], "magazine": "8", "ammunition_type": "H Pistol", "rof": 2, "hands": 1, "concealable": True, "alt_fire_modes": "None"},
    "Very Heavy Pistol": {"weapon_skill": "Handgun", "damage_values": ["4d6"], "magazine": "8", "ammunition_type": "VH Pistol", "rof": 1, "hands": 1, "concealable": False, "alt_fire_modes": "None"},
    "SMG": {"weapon_skill": "Handgun", "damage_values": ["2d6"], "magazine": "30", "ammunition_type": "M Pistol", "rof": 1, "hands": 1, "concealable": True, "alt_fire_modes": "Autofire (3) • Suppressive Fire"},
    "Heavy SMG": {"weapon_skill": "Handgun", "damage_values": ["3d6"], "magazine": "40", "ammunition_type": "H Pistol", "rof": 1, "hands": 1, "concealable": False, "alt_fire_modes": "Autofire (3) • Suppressive Fire"},
    "Shotgun": {"weapon_skill": "Shoulder Arms", "damage_values": ["5d6"], "magazine": "4", "ammunition_type": "Slug", "rof": 1, "hands": 2, "concealable": False, "alt_fire_modes": "Shotgun Shell"},
    "Assault Rifle": {"weapon_skill": "Shoulder Arms", "damage_values": ["5d6"], "magazine": "25", "ammunition_type": "Rifle", "rof": 1, "hands": 2, "concealable": False, "alt_fire_modes": "Autofire (4) • Suppressive Fire"},
    "Sniper Rifle": {"weapon_skill": "Shoulder Arms", "damage_values": ["5d6"], "magazine": "4", "ammunition_type": "Rifle", "rof": 1, "hands": 2, "concealable": False, "alt_fire_modes": "None"},
    "Bow": {"weapon_skill": "Archery", "damage_values": ["4d6"], "magazine": "N/A", "ammunition_type": "Arrow", "rof": 1, "hands": 2, "concealable": False, "alt_fire_modes": "Arrows"},
    "Crossbow": {"weapon_skill": "Archery", "damage_values": ["4d6"], "magazine": "N/A", "ammunition_type": "Arrow", "rof": 1, "hands": 2, "concealable": False, "alt_fire_modes": "Arrows"},
    "Grenade Launcher": {"weapon_skill": "Heavy Weapons", "damage_values": ["6d6"], "magazine": "2", "ammunition_type": "Grenade", "rof": 1, "hands": 2, "concealable": False, "alt_fire_modes": "Explosive"},
    "Rocket Launcher": {"weapon_skill": "Heavy Weapons", "damage_values": ["8d6"], "magazine": "1", "ammunition_type": "Rocket", "rof": 1, "hands": 2, "concealable": False, "alt_fire_modes": "Explosive"},
}

MELEE_DATA = {
    "Light Melee Weapon": {"info": "Combat Knife, Tomahawk", "damage": "1d6", "rof": 2, "concealable": True},
    "Medium Melee Weapon": {"info": "Baseball Bat, Crowbar, Machete", "damage": "2d6", "rof": 2, "concealable": False},
    "Heavy Melee Weapon": {"info": "Lead Pipe, Sword, Spiked Bat", "damage": "3d6", "rof": 2, "concealable": False},
    "Very Heavy Melee Weapon": {"info": "Chainsaw, Sledgehammer, Helicopter Blades, Naginata", "damage": "4d6", "rof": 1, "concealable": False},
}


def table_exists(con: sqlite3.Connection, table: str) -> bool:
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def price_text(con: sqlite3.Connection, item_id: int) -> str | None:
    row = con.execute("SELECT source_price_text FROM item_prices WHERE item_id=? ORDER BY item_price_id LIMIT 1", (item_id,)).fetchone()
    return row[0] if row else None


def update_item(con: sqlite3.Connection, name: str, info: str, rules: dict) -> None:
    row = con.execute("SELECT item_id,mechanics_json FROM items WHERE canonical_name=?", (name,)).fetchone()
    if row is None:
        raise RuntimeError(f"Missing expected item: {name}")
    item_id = row["item_id"]
    old = json.loads(row["mechanics_json"]) if row["mechanics_json"] else {}
    source = dict(old.get("source") or {})
    source.setdefault("code", "CP:R")
    source.setdefault("printed_page", 341)
    source.setdefault("pdf_page", 342)
    source["match_score"] = 100.0
    mechanics = {
        "source": source,
        "classification": old.get("classification", {}),
        "rules": {"source_cost_text": price_text(con, item_id), **rules},
        "special_rules": [],
    }
    con.execute(
        "UPDATE items SET info=?, mechanics_json=?, review_note=NULL WHERE item_id=?",
        (info, json.dumps(mechanics, ensure_ascii=False), item_id),
    )
    if table_exists(con, "enrichment_audit"):
        note = "Manually source-verified cleanup of Core Rulebook weapon-table parsing."
        con.execute(
            """
            UPDATE enrichment_audit
            SET match_score=100.0,
                info_method='manual_source_cleanup',
                mechanics_field_count=?,
                notes=CASE WHEN notes IS NULL OR trim(notes)='' THEN ? ELSE notes || ' | ' || ? END
            WHERE item_id=?
            """,
            (len(mechanics["rules"]), note, note, item_id),
        )


def apply(db: Path, make_backup: bool = True) -> None:
    if make_backup:
        stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(db, db.with_name(f"{db.stem}.backup_{stamp}{db.suffix}"))

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    try:
        con.execute("BEGIN")
        for name, rules in RANGED_RULES.items():
            update_item(con, name, "", rules)
        for name, data in MELEE_DATA.items():
            update_item(
                con,
                name,
                data["info"],
                {
                    "weapon_skill": "Melee Weapon",
                    "damage_values": [data["damage"]],
                    "hands": "Varies by type",
                    "rof": data["rof"],
                    "concealable": data["concealable"],
                },
            )

        # Keep the official Core RAW result, but no longer resolve it to the bad catalogue record.
        if table_exists(con, "core_raw_stock_rolls"):
            raw = con.execute(
                """
                SELECT stock_roll_id,notes FROM core_raw_stock_rolls
                WHERE category_code='food_drugs' AND d100_min=56 AND d100_max=60 AND display_text='Live Chicken'
                """
            ).fetchone()
            if raw:
                note = "Live Chicken remains a Core RAW static stock result; the erroneous canonical catalogue record was removed."
                notes = note if not raw["notes"] else f"{raw['notes']} | {note}"
                con.execute(
                    "UPDATE core_raw_stock_rolls SET resolution_mode='static', selector_json=?, notes=? WHERE stock_roll_id=?",
                    (json.dumps({"type": "static"}), notes, raw["stock_roll_id"]),
                )
                con.execute("DELETE FROM core_raw_stock_matches WHERE stock_roll_id=?", (raw["stock_roll_id"],))

        live = con.execute("SELECT item_id FROM items WHERE canonical_name='Live Chicken'").fetchone()
        if live:
            con.execute("DELETE FROM items WHERE item_id=?", (live["item_id"],))

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS database_edits (
                edit_id INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL,
                edit_scope TEXT NOT NULL,
                description TEXT NOT NULL
            )
            """
        )
        con.execute(
            "INSERT INTO database_edits(applied_at,edit_scope,description) VALUES (?,?,?)",
            (
                dt.datetime.now(dt.UTC).isoformat(),
                "core_weapon_cleanup",
                "Cleaned CP:R generic ranged/melee descriptions and mechanics; removed erroneous Live Chicken catalogue record.",
            ),
        )

        fk_errors = con.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise RuntimeError(f"Foreign-key errors: {fk_errors}")
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("db", type=Path)
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()
    apply(args.db, make_backup=not args.no_backup)
    print(f"Applied database cleanup to {args.db}")


if __name__ == "__main__":
    main()
