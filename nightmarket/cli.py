from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .generator import NightMarketGenerator
from .repository import MarketRepository
from .renderers import render_json, render_markdown, render_text


def default_db_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "cyberpunk_red_2045_market_ready.sqlite"


def prompt_choice(rule: dict, candidates: list[int], repo: MarketRepository) -> Optional[int]:
    if not candidates:
        return None

    print(f"\nGM choice: {rule['display_text']}")
    for index, item_id in enumerate(candidates, start=1):
        item = repo.get_item(item_id)
        price = " | ".join(item.prices) if item.prices else "Price not listed"
        print(f"  {index:>3}. {item.name} — {price}")
    print("    0. Leave unresolved")

    while True:
        try:
            raw = input("Choose item: ").strip()
            value = int(raw)
        except ValueError:
            print("Enter a number.")
            continue
        if value == 0:
            return None
        if 1 <= value <= len(candidates):
            return candidates[value - 1]
        print("Choice out of range.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nightmarket",
        description="Cyberpunk RED canon-2045 Night Market generator.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    generate = sub.add_parser("generate", help="Generate a Night Market.")
    generate.add_argument(
        "--db",
        type=Path,
        default=default_db_path(),
        help="Path to the market-ready SQLite database.",
    )
    generate.add_argument(
        "--mode",
        choices=["core_raw", "expanded_2045"],
        default="expanded_2045",
    )
    generate.add_argument("--seed", type=int, default=None)
    generate.add_argument(
        "--gm-choice",
        choices=["random", "leave", "prompt"],
        default="random",
        help="How expanded mode resolves RAW 'GM's choice' slots.",
    )
    generate.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
    )
    generate.add_argument(
        "--output",
        type=Path,
        help="Write output to a file instead of stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "generate":
        with MarketRepository(args.db) as repo:
            generator = NightMarketGenerator(repo)
            market = generator.generate(
                mode=args.mode,
                seed=args.seed,
                gm_choice_behavior=args.gm_choice,
                gm_chooser=prompt_choice if args.gm_choice == "prompt" else None,
            )

        renderer = {
            "text": render_text,
            "json": render_json,
            "markdown": render_markdown,
        }[args.format]
        content = renderer(market)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
            print(f"Wrote {args.output}")
        else:
            print(content, end="")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
