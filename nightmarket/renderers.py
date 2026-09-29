from __future__ import annotations

import json

from .models import NightMarket, StockSlot


def _item_price(item) -> str:
    return " | ".join(item.prices) if item.prices else "Price not listed"


def render_text(market: NightMarket) -> str:
    lines = [
        "CYBERPUNK RED — NIGHT MARKET",
        f"Mode: {market.mode}",
        f"Seed: {market.seed}",
        f"Generator: {market.generator_version}",
        "",
    ]

    for section in market.sections:
        lines.append(section.category_name.upper())
        lines.append("-" * len(section.category_name))
        lines.append(
            f"Category roll: {section.category_roll} | "
            f"Stock types: {section.stock_count_roll}"
        )
        for slot in section.slots:
            roll = f"{slot.d100_roll:02d} [{slot.d100_min}-{slot.d100_max}]"
            if market.mode == "core_raw" or slot.selected_item is None:
                cost = f" — {slot.raw_cost}" if slot.raw_cost else ""
                lines.append(f"  {roll}: {slot.raw_result}{cost}")
                if (
                    market.mode == "expanded_2045"
                    and slot.resolution_mode == "gm_choice"
                    and slot.selected_item is None
                ):
                    lines.append("      GM choice left unresolved.")
            else:
                item = slot.selected_item
                lines.append(f"  {roll}: {item.name} — {_item_price(item)}")
                if item.manufacturers:
                    lines.append(f"      Manufacturer: {', '.join(item.manufacturers)}")
                lines.append(f"      RAW slot: {slot.raw_result}")
                if item.info:
                    lines.append(f"      {item.info}")
                for extra in slot.supplemental_items:
                    lines.append(
                        f"      + {extra.name} — {_item_price(extra)} "
                        "(required foundational cyberware)"
                    )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_markdown(market: NightMarket) -> str:
    lines = [
        "# Cyberpunk RED — Night Market",
        "",
        f"- **Mode:** `{market.mode}`",
        f"- **Seed:** `{market.seed}`",
        f"- **Generator:** `{market.generator_version}`",
        "",
    ]

    for section in market.sections:
        lines.extend([
            f"## {section.category_name}",
            "",
            f"Category roll **{section.category_roll}**; "
            f"**{section.stock_count_roll}** item types.",
            "",
        ])
        for slot in section.slots:
            roll = f"{slot.d100_roll:02d} ({slot.d100_min}–{slot.d100_max})"
            if market.mode == "core_raw" or slot.selected_item is None:
                price = f" — {slot.raw_cost}" if slot.raw_cost else ""
                lines.append(f"- **{roll}: {slot.raw_result}**{price}")
                if (
                    market.mode == "expanded_2045"
                    and slot.resolution_mode == "gm_choice"
                    and slot.selected_item is None
                ):
                    lines.append("  - GM choice left unresolved.")
            else:
                item = slot.selected_item
                lines.append(f"- **{roll}: {item.name}** — {_item_price(item)}")
                lines.append(f"  - RAW slot: {slot.raw_result}")
                if item.manufacturers:
                    lines.append(f"  - Manufacturer: {', '.join(item.manufacturers)}")
                if item.info:
                    lines.append(f"  - {item.info}")
                for extra in slot.supplemental_items:
                    lines.append(
                        f"  - **Also available:** {extra.name} — {_item_price(extra)} "
                        "(required foundational cyberware)"
                    )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_json(market: NightMarket, *, indent: int = 2) -> str:
    return json.dumps(market.to_dict(), ensure_ascii=False, indent=indent)
