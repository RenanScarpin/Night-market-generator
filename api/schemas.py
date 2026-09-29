from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MarketGenerateRequest(StrictModel):
    mode: Literal["core_raw", "expanded_2045"] = "expanded_2045"
    seed: Optional[int] = None
    gm_choice: Literal["random", "leave"] = "random"


class MarketItem(BaseModel):
    item_id: int
    name: str
    slug: str
    info: str
    item_kind: str
    prices: list[str]
    manufacturers: list[str]
    primary_source: Optional[str] = None
    primary_page: Optional[int] = None
    tags: list[str]


class StockSlotResponse(BaseModel):
    stock_roll_id: int
    category_code: str
    category_name: str
    d100_roll: int
    d100_min: int
    d100_max: int
    raw_result: str
    raw_cost: Optional[str] = None
    resolution_mode: str
    selector: dict[str, Any]
    selected_item: Optional[MarketItem] = None
    supplemental_items: list[MarketItem] = Field(default_factory=list)
    supplemental_reason: Optional[str] = None


class MarketSectionResponse(BaseModel):
    category_roll: int
    category_code: str
    category_name: str
    description: str
    stock_count_roll: int
    stock_roll_attempts: list[int]
    slots: list[StockSlotResponse]


class MarketResponse(BaseModel):
    generator_version: str
    seed: int
    mode: str
    gm_choice_behavior: str
    category_roll_attempts: list[int]
    sections: list[MarketSectionResponse]


class ItemPriceSummary(BaseModel):
    cost_eb: Optional[int] = None
    price_category: Optional[str] = None
    source_price_text: Optional[str] = None
    variant_label: Optional[str] = None


class ItemCategorySummary(BaseModel):
    name: str
    slug: str
    is_primary: bool


class ItemSummary(BaseModel):
    item_id: int
    canonical_name: str
    slug: str
    item_kind: str
    info: str
    prices: list[ItemPriceSummary]
    categories: list[ItemCategorySummary]
    manufacturers: list[str]


class PaginatedItems(BaseModel):
    items: list[ItemSummary]
    total: int
    limit: int
    offset: int


class ItemPriceDetail(BaseModel):
    item_price_id: int
    variant_label: Optional[str] = None
    price_kind: str
    cost_eb: Optional[int] = None
    price_category: Optional[str] = None
    unit: str
    unit_quantity: float
    cost_basis: Optional[str] = None
    source_price_text: Optional[str] = None
    notes: Optional[str] = None


class CategoryDetail(BaseModel):
    category_id: int
    parent_category_id: Optional[int] = None
    name: str
    slug: str
    sort_order: Optional[int] = None
    is_primary: Optional[bool] = None
    item_count: Optional[int] = None


class CompanyDetail(BaseModel):
    company_id: int
    name: str
    role: str


class AliasDetail(BaseModel):
    alias: str
    alias_type: str


class MarketTagDetail(BaseModel):
    tag_id: int
    code: str
    name: str
    tag_group: str
    description: Optional[str] = None
    origin: Optional[str] = None
    notes: Optional[str] = None
    item_count: Optional[int] = None


class SourceDetail(BaseModel):
    source_id: int
    code: str
    title: str
    version: Optional[str] = None
    publication_date: Optional[str] = None
    source_role: str
    source_name: Optional[str] = None
    printed_page: Optional[int] = None
    pdf_page: Optional[int] = None
    section: Optional[str] = None
    notes: Optional[str] = None


class RelationshipDetail(BaseModel):
    relation_type: str
    target_item_id: int
    target_name: str
    target_slug: str
    notes: Optional[str] = None


class EligibilityDetail(BaseModel):
    profile_code: str
    profile_name: str
    status: str
    reason: Optional[str] = None


class ItemDetailResponse(BaseModel):
    item_id: int
    canonical_name: str
    slug: str
    info: str
    mechanics: Optional[dict[str, Any]] = None
    item_kind: str
    record_status: str
    needs_review: bool
    review_note: Optional[str] = None
    canon_2045: bool
    prices: list[ItemPriceDetail]
    categories: list[CategoryDetail]
    companies: list[CompanyDetail]
    aliases: list[AliasDetail]
    tags: list[MarketTagDetail]
    sources: list[SourceDetail]
    relationships: list[RelationshipDetail]
    eligibility: list[EligibilityDetail]


class RawMarketCategory(BaseModel):
    category_code: str
    d6_roll: int
    name: str
    description: str
    source_code: str
    printed_page: int


class MarketProfile(BaseModel):
    code: str
    name: str
    description: str


class MetaResponse(BaseModel):
    api_version: str
    generator_version: str
    database: str
    item_count: int
    tag_count: int
    category_count: int
    supported_modes: list[str]
    supported_gm_choice: list[str]
    market_profiles: list[MarketProfile]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    api_version: str
    generator_version: str
    database_ok: bool
    item_count: int
