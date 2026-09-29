from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass(frozen=True)
class ItemRecord:
    item_id: int
    name: str
    slug: str
    info: str
    item_kind: str
    prices: list[str] = field(default_factory=list)
    manufacturers: list[str] = field(default_factory=list)
    primary_source: Optional[str] = None
    primary_page: Optional[int] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StockSlot:
    stock_roll_id: int
    category_code: str
    category_name: str
    d100_roll: int
    d100_min: int
    d100_max: int
    raw_result: str
    raw_cost: Optional[str]
    resolution_mode: str
    selector: dict[str, Any]
    selected_item: Optional[ItemRecord] = None
    supplemental_items: list[ItemRecord] = field(default_factory=list)
    supplemental_reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


@dataclass(frozen=True)
class MarketSection:
    category_roll: int
    category_code: str
    category_name: str
    description: str
    stock_count_roll: int
    stock_roll_attempts: list[int]
    slots: list[StockSlot]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NightMarket:
    generator_version: str
    seed: int
    mode: str
    gm_choice_behavior: str
    category_roll_attempts: list[int]
    sections: list[MarketSection]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
