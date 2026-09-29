from __future__ import annotations

import json
import sqlite3
from collections import deque
from pathlib import Path
from typing import Any, Iterable, Optional

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

    # ------------------------------------------------------------------
    # Night Market rule access
    # ------------------------------------------------------------------

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

    def list_market_categories(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.con.execute(
                """
                SELECT category_code,d6_roll,name,description,source_code,printed_page
                FROM core_raw_market_categories
                ORDER BY d6_roll
                """
            )
        ]

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

    # ------------------------------------------------------------------
    # Item helpers used by both the engine and API
    # ------------------------------------------------------------------

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

    def get_item_detail(self, item_id: int) -> dict[str, Any]:
        row = self.con.execute(
            """
            SELECT item_id,canonical_name,slug,info,mechanics_json,item_kind,
                   record_status,needs_review,review_note,canon_2045
            FROM items
            WHERE item_id=?
            """,
            (item_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Unknown item_id={item_id}")

        detail = dict(row)
        detail["mechanics"] = (
            json.loads(detail.pop("mechanics_json"))
            if detail["mechanics_json"]
            else None
        )
        detail["needs_review"] = bool(detail["needs_review"])
        detail["canon_2045"] = bool(detail["canon_2045"])

        detail["prices"] = [
            dict(r)
            for r in self.con.execute(
                """
                SELECT ip.item_price_id,ip.variant_label,ip.price_kind,ip.cost_eb,
                       pc.name AS price_category,ip.unit,ip.unit_quantity,
                       ip.cost_basis,ip.source_price_text,ip.notes
                FROM item_prices ip
                LEFT JOIN price_categories pc USING(price_category_id)
                WHERE ip.item_id=?
                ORDER BY ip.item_price_id
                """,
                (item_id,),
            )
        ]

        detail["categories"] = [
            dict(r)
            for r in self.con.execute(
                """
                SELECT c.category_id,c.parent_category_id,c.name,c.slug,c.sort_order,
                       ic.is_primary
                FROM item_categories ic
                JOIN categories c USING(category_id)
                WHERE ic.item_id=?
                ORDER BY ic.is_primary DESC,c.sort_order,c.name
                """,
                (item_id,),
            )
        ]
        for category in detail["categories"]:
            category["is_primary"] = bool(category["is_primary"])

        detail["companies"] = [
            dict(r)
            for r in self.con.execute(
                """
                SELECT c.company_id,c.name,ic.role
                FROM item_companies ic
                JOIN companies c USING(company_id)
                WHERE ic.item_id=?
                ORDER BY ic.role,c.name
                """,
                (item_id,),
            )
        ]

        detail["aliases"] = [
            dict(r)
            for r in self.con.execute(
                """
                SELECT alias,alias_type
                FROM item_aliases
                WHERE item_id=?
                ORDER BY alias
                """,
                (item_id,),
            )
        ]

        detail["tags"] = [
            dict(r)
            for r in self.con.execute(
                """
                SELECT mt.tag_id,mt.code,mt.name,mt.tag_group,mt.description,
                       imt.origin,imt.notes
                FROM item_market_tags imt
                JOIN market_tags mt USING(tag_id)
                WHERE imt.item_id=?
                ORDER BY mt.tag_group,mt.code
                """,
                (item_id,),
            )
        ]

        detail["sources"] = [
            dict(r)
            for r in self.con.execute(
                """
                SELECT s.source_id,s.code,s.title,s.version,s.publication_date,
                       isrc.source_role,isrc.source_name,isrc.printed_page,
                       isrc.pdf_page,isrc.section,isrc.notes
                FROM item_sources isrc
                JOIN sources s USING(source_id)
                WHERE isrc.item_id=?
                ORDER BY
                    CASE isrc.source_role
                        WHEN 'primary' THEN 0
                        WHEN 'index' THEN 1
                        WHEN 'reprint' THEN 2
                        ELSE 3
                    END,
                    s.code,
                    isrc.printed_page
                """,
                (item_id,),
            )
        ]

        detail["relationships"] = [
            dict(r)
            for r in self.con.execute(
                """
                SELECT ir.relation_type,ir.target_item_id,
                       target.canonical_name AS target_name,
                       target.slug AS target_slug,
                       ir.notes
                FROM item_relations ir
                JOIN items target ON target.item_id=ir.target_item_id
                WHERE ir.source_item_id=?
                ORDER BY ir.relation_type,target.canonical_name
                """,
                (item_id,),
            )
        ]

        detail["eligibility"] = [
            dict(r)
            for r in self.con.execute(
                """
                SELECT mp.code AS profile_code,mp.name AS profile_name,
                       me.status,me.reason
                FROM market_eligibility me
                JOIN market_profiles mp USING(profile_id)
                WHERE me.item_id=?
                ORDER BY mp.profile_id
                """,
                (item_id,),
            )
        ]

        return detail

    def list_items(
        self,
        *,
        q: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        manufacturer: Optional[str] = None,
        item_kind: Optional[str] = None,
        min_cost_eb: Optional[int] = None,
        max_cost_eb: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        where = ["i.canon_2045=1"]
        params: list[Any] = []

        if q:
            where.append(
                """
                (
                    lower(i.canonical_name) LIKE lower(?)
                    OR EXISTS (
                        SELECT 1
                        FROM item_aliases ia
                        WHERE ia.item_id=i.item_id
                          AND lower(ia.alias) LIKE lower(?)
                    )
                )
                """
            )
            like = f"%{q}%"
            params.extend([like, like])

        if category:
            where.append(
                """
                EXISTS (
                    SELECT 1
                    FROM item_categories ic
                    JOIN categories c USING(category_id)
                    WHERE ic.item_id=i.item_id
                      AND (c.slug=? OR lower(c.name)=lower(?))
                )
                """
            )
            params.extend([category, category])

        if tag:
            where.append(
                """
                EXISTS (
                    SELECT 1
                    FROM item_market_tags imt
                    JOIN market_tags mt USING(tag_id)
                    WHERE imt.item_id=i.item_id AND mt.code=?
                )
                """
            )
            params.append(tag)

        if manufacturer:
            where.append(
                """
                EXISTS (
                    SELECT 1
                    FROM item_companies ico
                    JOIN companies co USING(company_id)
                    WHERE ico.item_id=i.item_id
                      AND lower(co.name)=lower(?)
                )
                """
            )
            params.append(manufacturer)

        if item_kind:
            where.append("i.item_kind=?")
            params.append(item_kind)

        if min_cost_eb is not None:
            where.append(
                """
                EXISTS (
                    SELECT 1 FROM item_prices ip
                    WHERE ip.item_id=i.item_id
                      AND ip.price_kind='fixed'
                      AND ip.cost_eb>=?
                )
                """
            )
            params.append(min_cost_eb)

        if max_cost_eb is not None:
            where.append(
                """
                EXISTS (
                    SELECT 1 FROM item_prices ip
                    WHERE ip.item_id=i.item_id
                      AND ip.price_kind='fixed'
                      AND ip.cost_eb<=?
                )
                """
            )
            params.append(max_cost_eb)

        where_sql = " AND ".join(where)

        total = self.con.execute(
            f"SELECT COUNT(*) AS n FROM items i WHERE {where_sql}",
            params,
        ).fetchone()["n"]

        rows = self.con.execute(
            f"""
            SELECT i.item_id,i.canonical_name,i.slug,i.item_kind,i.info
            FROM items i
            WHERE {where_sql}
            ORDER BY i.canonical_name COLLATE NOCASE,i.item_id
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            item_id = row["item_id"]
            summary = dict(row)

            summary["prices"] = [
                dict(r)
                for r in self.con.execute(
                    """
                    SELECT ip.cost_eb,pc.name AS price_category,
                           ip.source_price_text,ip.variant_label
                    FROM item_prices ip
                    LEFT JOIN price_categories pc USING(price_category_id)
                    WHERE ip.item_id=?
                    ORDER BY ip.item_price_id
                    """,
                    (item_id,),
                )
            ]

            summary["categories"] = [
                dict(r)
                for r in self.con.execute(
                    """
                    SELECT c.name,c.slug,ic.is_primary
                    FROM item_categories ic
                    JOIN categories c USING(category_id)
                    WHERE ic.item_id=?
                    ORDER BY ic.is_primary DESC,c.name
                    """,
                    (item_id,),
                )
            ]
            for cat in summary["categories"]:
                cat["is_primary"] = bool(cat["is_primary"])

            summary["manufacturers"] = [
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

            results.append(summary)

        return results, total

    def list_categories(self) -> list[dict[str, Any]]:
        return [
            dict(r)
            for r in self.con.execute(
                """
                SELECT c.category_id,c.parent_category_id,c.name,c.slug,c.sort_order,
                       COUNT(ic.item_id) AS item_count
                FROM categories c
                LEFT JOIN item_categories ic USING(category_id)
                GROUP BY c.category_id
                ORDER BY
                    CASE WHEN c.parent_category_id IS NULL THEN 0 ELSE 1 END,
                    c.sort_order,
                    c.name
                """
            )
        ]

    def list_market_tags(self) -> list[dict[str, Any]]:
        return [
            dict(r)
            for r in self.con.execute(
                """
                SELECT mt.tag_id,mt.code,mt.name,mt.tag_group,mt.description,
                       COUNT(imt.item_id) AS item_count
                FROM market_tags mt
                LEFT JOIN item_market_tags imt USING(tag_id)
                GROUP BY mt.tag_id
                ORDER BY mt.tag_group,mt.code
                """
            )
        ]

    def list_manufacturers(self) -> list[dict[str, Any]]:
        return [
            dict(r)
            for r in self.con.execute(
                """
                SELECT c.company_id,c.name,COUNT(DISTINCT ic.item_id) AS item_count
                FROM companies c
                JOIN item_companies ic USING(company_id)
                WHERE ic.role='manufacturer'
                GROUP BY c.company_id,c.name
                ORDER BY c.name COLLATE NOCASE
                """
            )
        ]

    def get_meta(self) -> dict[str, Any]:
        return {
            "item_count": self.con.execute(
                "SELECT COUNT(*) AS n FROM items WHERE canon_2045=1"
            ).fetchone()["n"],
            "tag_count": self.con.execute(
                "SELECT COUNT(*) AS n FROM market_tags"
            ).fetchone()["n"],
            "category_count": self.con.execute(
                "SELECT COUNT(*) AS n FROM categories"
            ).fetchone()["n"],
            "market_profiles": [
                dict(r)
                for r in self.con.execute(
                    """
                    SELECT code,name,description
                    FROM market_profiles
                    ORDER BY profile_id
                    """
                )
            ],
        }

    # ------------------------------------------------------------------
    # Relationship helpers for the generator
    # ------------------------------------------------------------------

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
