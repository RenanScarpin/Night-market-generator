from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from nightmarket.generator import GENERATOR_VERSION, NightMarketGenerator
from nightmarket.repository import MarketRepository

from .schemas import (
    CategoryDetail,
    HealthResponse,
    ItemDetailResponse,
    MarketGenerateRequest,
    MarketResponse,
    MarketTagDetail,
    MetaResponse,
    PaginatedItems,
    RawMarketCategory,
)


API_VERSION = "0.1.0"


def default_db_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "data"
        / "cyberpunk_red_2045_market_ready.sqlite"
    )


def _cors_origins() -> list[str]:
    raw = os.getenv(
        "NIGHTMARKET_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app(db_path: str | Path | None = None) -> FastAPI:
    resolved_db = Path(
        db_path
        or os.getenv("NIGHTMARKET_DB")
        or default_db_path()
    ).resolve()

    if not resolved_db.exists():
        raise FileNotFoundError(
            f"Night Market database not found: {resolved_db}. "
            "Set NIGHTMARKET_DB or pass db_path to create_app()."
        )

    app = FastAPI(
        title="Cyberpunk RED Night Market API",
        version=API_VERSION,
        description=(
            "HTTP API for the deterministic canon-2045 Cyberpunk RED "
            "Night Market generator."
        ),
    )
    app.state.db_path = resolved_db

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def open_repo() -> MarketRepository:
        return MarketRepository(app.state.db_path)

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {
            "name": "Cyberpunk RED Night Market API",
            "api_version": API_VERSION,
            "generator_version": GENERATOR_VERSION,
            "docs": "/docs",
            "openapi": "/openapi.json",
        }

    @app.get("/api/health", response_model=HealthResponse, tags=["system"])
    def health() -> dict:
        with open_repo() as repo:
            meta = repo.get_meta()
        return {
            "status": "ok",
            "api_version": API_VERSION,
            "generator_version": GENERATOR_VERSION,
            "database_ok": True,
            "item_count": meta["item_count"],
        }

    @app.get("/api/meta", response_model=MetaResponse, tags=["system"])
    def meta() -> dict:
        with open_repo() as repo:
            data = repo.get_meta()
        return {
            "api_version": API_VERSION,
            "generator_version": GENERATOR_VERSION,
            "database": app.state.db_path.name,
            "item_count": data["item_count"],
            "tag_count": data["tag_count"],
            "category_count": data["category_count"],
            "supported_modes": ["core_raw", "expanded_2045"],
            "supported_gm_choice": ["random", "leave"],
            "market_profiles": data["market_profiles"],
        }

    @app.post(
        "/api/markets/generate",
        response_model=MarketResponse,
        tags=["markets"],
        summary="Generate a deterministic Night Market",
    )
    def generate_market(request: MarketGenerateRequest) -> dict:
        with open_repo() as repo:
            generator = NightMarketGenerator(repo)
            market = generator.generate(
                mode=request.mode,
                seed=request.seed,
                gm_choice_behavior=request.gm_choice,
            )
        return market.to_dict()

    @app.get(
        "/api/markets/{seed}",
        response_model=MarketResponse,
        tags=["markets"],
        summary="Regenerate a market from its seed",
        description=(
            "Markets are deterministic, not persisted. This endpoint regenerates "
            "the market for the supplied seed and settings."
        ),
    )
    def regenerate_market(
        seed: int,
        mode: Literal["core_raw", "expanded_2045"] = "expanded_2045",
        gm_choice: Literal["random", "leave"] = "random",
    ) -> dict:
        with open_repo() as repo:
            generator = NightMarketGenerator(repo)
            market = generator.generate(
                mode=mode,
                seed=seed,
                gm_choice_behavior=gm_choice,
            )
        return market.to_dict()

    @app.get(
        "/api/items",
        response_model=PaginatedItems,
        tags=["catalogue"],
        summary="Search and filter the canon-2045 catalogue",
    )
    def list_items(
        q: Optional[str] = Query(default=None, min_length=1),
        category: Optional[str] = Query(
            default=None,
            description="Category slug or exact category name.",
        ),
        tag: Optional[str] = Query(
            default=None,
            description="Exact market tag code.",
        ),
        manufacturer: Optional[str] = Query(default=None),
        item_kind: Optional[str] = Query(default=None),
        min_cost_eb: Optional[int] = Query(default=None, ge=0),
        max_cost_eb: Optional[int] = Query(default=None, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        if (
            min_cost_eb is not None
            and max_cost_eb is not None
            and min_cost_eb > max_cost_eb
        ):
            raise HTTPException(
                status_code=400,
                detail="min_cost_eb cannot be greater than max_cost_eb.",
            )

        with open_repo() as repo:
            items, total = repo.list_items(
                q=q,
                category=category,
                tag=tag,
                manufacturer=manufacturer,
                item_kind=item_kind,
                min_cost_eb=min_cost_eb,
                max_cost_eb=max_cost_eb,
                limit=limit,
                offset=offset,
            )
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    @app.get(
        "/api/items/{item_id}",
        response_model=ItemDetailResponse,
        tags=["catalogue"],
        summary="Get one complete item record",
    )
    def item_detail(item_id: int) -> dict:
        try:
            with open_repo() as repo:
                return repo.get_item_detail(item_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Item not found.")

    @app.get(
        "/api/categories",
        response_model=list[CategoryDetail],
        tags=["catalogue"],
    )
    def categories() -> list[dict]:
        with open_repo() as repo:
            return repo.list_categories()

    @app.get(
        "/api/tags",
        response_model=list[MarketTagDetail],
        tags=["catalogue"],
    )
    def tags() -> list[dict]:
        with open_repo() as repo:
            return repo.list_market_tags()

    @app.get(
        "/api/market-categories",
        response_model=list[RawMarketCategory],
        tags=["markets"],
        summary="List the six Core RAW Night Market categories",
    )
    def market_categories() -> list[dict]:
        with open_repo() as repo:
            return repo.list_market_categories()

    return app


app = create_app()
