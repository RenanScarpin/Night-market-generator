from __future__ import annotations

import json
import sqlite3
from collections import deque
from pathlib import Path
from typing import Iterable, Optional

from .models import ItemRecord


class MarketRepository:
    """Read-only access to the canon-2045 Night Market SQLite database."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self.con = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        self.con.row_factory = sqlite3.Row

    def close(self) -> None:
        self.con.close()

    def __enter__(self) -> "MarketRepository":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def get_market_category_by_roll(self, d6_roll: int) -> dict:
        row = self.con.execute(
            """
            SELECT category_code,d6_roll,name,description,source_code,printed_page
            FROM core_raw_market_categories
            WHERE d6_roll=?
            """,
            (d6_roll,),
        ).fetchone()
        if row is None:
            raise KeyError(f"No RAW market category for d6={d6_roll}")
        return dict(row)

    def get_stock_roll(self, category_code: str, d100_roll: int) -> dict:
        row = self.con.execute(
            """
            SELECT stock_roll_id,category_code,d100_min,d100_max,display_text,
                   source_cost_text,resolution_mode,selector_json,printed_page,notes
            FROM core_raw_stock_rolls
            WHERE category_code=? AND ? BETWEEN d100_min AND d100_max
            """,
            (category_code, d100_roll),
        ).fetchone()
        if row is None:
            raise KeyError(f"No RAW stock row for {category_code=} and d100={d100_roll}")
        result = dict(row)
        result["selector"] = json.loads(result.pop("selector_json"))
        return result

    def get_stock_candidates(
        self,
        stock_roll_id: int,
        exclude_item_ids: Iterable[int] = (),
    ) -> list[int]:
        excluded = set(exclude_item_ids)
        rows = self.con.execute(
            """
            SELECT item_id
            FROM core_raw_stock_matches
            WHERE stock_roll_id=?
            ORDER BY item_id
            """,
            (stock_roll_id,),
        ).fetchall()
        return [r["item_id"] for r in rows if r["item_id"] not in excluded]

    def get_item_id_by_name(self, name: str) -> Optional[int]:
        row = self.con.execute(
            "SELECT item_id FROM items WHERE canonical_name=? ORDER BY item_id LIMIT 1",
            (name,),
        ).fetchone()
        return None if row is None else row["item_id"]

    def get_item(self, item_id: int) -> ItemRecord:
        row = self.con.execute(
            """
            SELECT item_id,canonical_name,slug,info,item_kind
            FROM items WHERE item_id=?
            """,
            (item_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown item_id={item_id}")

        prices = [
            r["source_price_text"]
            for r in self.con.execute(
                """
                SELECT source_price_text
                FROM item_prices
                WHERE item_id=?
                ORDER BY item_price_id
                """,
                (item_id,),
            )
            if r["source_price_text"]
        ]

        manufacturers = [
            r["name"]
            for r in self.con.execute(
                """
                SELECT c.name
                FROM item_companies ic
                JOIN companies c USING(company_id)
                WHERE ic.item_id=? AND ic.role='manufacturer'
                ORDER BY c.name
                """,
                (item_id,),
            )
        ]

        source = self.con.execute(
            """
            SELECT s.code,isrc.printed_page
            FROM item_sources isrc
            JOIN sources s USING(source_id)
            WHERE isrc.item_id=? AND isrc.source_role='primary'
            ORDER BY isrc.item_source_id
            LIMIT 1
            """,
            (item_id,),
        ).fetchone()

        tags = [
            r["code"]
            for r in self.con.execute(
                """
                SELECT mt.code
                FROM item_market_tags imt
                JOIN market_tags mt USING(tag_id)
                WHERE imt.item_id=?
                ORDER BY mt.code
                """,
                (item_id,),
            )
        ]

        return ItemRecord(
            item_id=row["item_id"],
            name=row["canonical_name"],
            slug=row["slug"],
            info=row["info"],
            item_kind=row["item_kind"],
            prices=prices,
            manufacturers=manufacturers,
            primary_source=source["code"] if source else None,
            primary_page=source["printed_page"] if source else None,
            tags=tags,
        )

    def item_has_tag(self, item_id: int, tag_code: str) -> bool:
        return self.con.execute(
            """
            SELECT 1
            FROM item_market_tags imt
            JOIN market_tags mt USING(tag_id)
            WHERE imt.item_id=? AND mt.code=?
            LIMIT 1
            """,
            (item_id, tag_code),
        ).fetchone() is not None

    def get_direct_requirements(self, item_id: int) -> list[int]:
        return [
            r["target_item_id"]
            for r in self.con.execute(
                """
                SELECT target_item_id
                FROM item_relations
                WHERE source_item_id=? AND relation_type='requires'
                ORDER BY target_item_id
                """,
                (item_id,),
            )
        ]

    def get_required_foundational_cyberware(self, item_id: int) -> list[int]:
        """
        Follow `requires` relationships and return required items tagged as
        foundational cyberware. A small semantic fallback is used for option
        records whose source enrichment did not contain an explicit relation.
        """
        found: set[int] = set()
        visited = {item_id}
        queue = deque([item_id])

        while queue:
            current = queue.popleft()
            for target in self.get_direct_requirements(current):
                if target in visited:
                    continue
                visited.add(target)
                tags = self.get_item(target).tags
                if any(t.startswith("cyberware.foundation.") for t in tags):
                    found.add(target)
                queue.append(target)

        # Fallbacks for well-defined Core foundational relationships.
        source_tags = set(self.get_item(item_id).tags)
        fallback_names: list[str] = []
        if "cyberware.option.cybereye" in source_tags:
            fallback_names.append("Cybereye")
        if "cyberware.option.cyberaudio" in source_tags:
            fallback_names.append("Cyberaudio Suite")
        if "cyberware.option.neuralware" in source_tags:
            fallback_names.append("Neural Link")

        for name in fallback_names:
            target = self.get_item_id_by_name(name)
            if target is not None:
                found.add(target)

        return sorted(found)
