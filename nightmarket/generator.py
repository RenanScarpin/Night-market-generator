from __future__ import annotations

import secrets
import random
from typing import Callable, Optional

from .models import NightMarket, MarketSection, StockSlot
from .repository import MarketRepository


GENERATOR_VERSION = "0.1.0"

GMChooser = Callable[[dict, list[int], MarketRepository], Optional[int]]


class NightMarketGenerator:
    """
    Implements:
      * core_raw: exact Core Rulebook Night Market stock-table results.
      * expanded_2045: the same RAW rolls, but query/GM-choice slots resolve
        to concrete canon-2045 database items where possible.

    Static RAW results remain static in both modes because they are not all
    represented as canonical database items.
    """

    VALID_MODES = {"core_raw", "expanded_2045"}
    VALID_GM_BEHAVIORS = {"random", "leave", "prompt"}

    def __init__(self, repository: MarketRepository):
        self.repo = repository

    def generate(
        self,
        *,
        mode: str = "expanded_2045",
        seed: Optional[int] = None,
        gm_choice_behavior: str = "random",
        gm_chooser: Optional[GMChooser] = None,
    ) -> NightMarket:
        if mode not in self.VALID_MODES:
            raise ValueError(f"Unknown mode {mode!r}; expected one of {sorted(self.VALID_MODES)}")
        if gm_choice_behavior not in self.VALID_GM_BEHAVIORS:
            raise ValueError(
                f"Unknown gm_choice_behavior {gm_choice_behavior!r}; "
                f"expected one of {sorted(self.VALID_GM_BEHAVIORS)}"
            )
        if gm_choice_behavior == "prompt" and gm_chooser is None:
            raise ValueError("gm_choice_behavior='prompt' requires gm_chooser")

        if seed is None:
            seed = secrets.randbits(63)
        rng = random.Random(seed)

        # RAW: roll 1d6 twice; reroll second/duplicates until different.
        category_roll_attempts: list[int] = []
        accepted_category_rolls: list[int] = []
        while len(accepted_category_rolls) < 2:
            roll = rng.randint(1, 6)
            category_roll_attempts.append(roll)
            if roll not in accepted_category_rolls:
                accepted_category_rolls.append(roll)

        selected_item_ids: set[int] = set()
        sections: list[MarketSection] = []

        for category_roll in accepted_category_rolls:
            cat = self.repo.get_market_category_by_roll(category_roll)
            stock_count_roll = rng.randint(1, 10)

            slots: list[StockSlot] = []
            used_stock_roll_ids: set[int] = set()
            stock_roll_attempts: list[int] = []

            # RAW duplicate rule is interpreted as duplicate table result,
            # not merely the identical percentile number. Since each d100
            # band maps to one table result, uniqueness is by stock_roll_id.
            while len(slots) < stock_count_roll:
                d100 = rng.randint(1, 100)
                stock_roll_attempts.append(d100)
                rule = self.repo.get_stock_roll(cat["category_code"], d100)
                if rule["stock_roll_id"] in used_stock_roll_ids:
                    continue
                used_stock_roll_ids.add(rule["stock_roll_id"])

                selected_item = None
                supplemental = []
                supplemental_reason = None

                if mode == "expanded_2045" and rule["resolution_mode"] != "static":
                    candidates = self.repo.get_stock_candidates(
                        rule["stock_roll_id"],
                        exclude_item_ids=selected_item_ids,
                    )

                    if rule["resolution_mode"] == "gm_choice":
                        if gm_choice_behavior == "leave":
                            choice = None
                        elif gm_choice_behavior == "prompt":
                            choice = gm_chooser(rule, candidates, self.repo)
                            if choice is not None and choice not in candidates:
                                raise ValueError(
                                    f"GM chooser returned item_id={choice}, "
                                    "which is not an eligible candidate."
                                )
                        else:
                            choice = rng.choice(candidates) if candidates else None
                    else:
                        choice = rng.choice(candidates) if candidates else None

                    if choice is not None:
                        selected_item_ids.add(choice)
                        selected_item = self.repo.get_item(choice)

                        # RAW Cyberware special rule: foundational cyberware
                        # required by a rolled option is also available.
                        if cat["category_code"] == "cyberware":
                            foundation_ids = self.repo.get_required_foundational_cyberware(choice)
                            for foundation_id in foundation_ids:
                                if foundation_id not in selected_item_ids:
                                    selected_item_ids.add(foundation_id)
                                    supplemental.append(self.repo.get_item(foundation_id))
                            if supplemental:
                                supplemental_reason = (
                                    f"Required foundational cyberware for {selected_item.name}."
                                )

                slots.append(
                    StockSlot(
                        stock_roll_id=rule["stock_roll_id"],
                        category_code=cat["category_code"],
                        category_name=cat["name"],
                        d100_roll=d100,
                        d100_min=rule["d100_min"],
                        d100_max=rule["d100_max"],
                        raw_result=rule["display_text"],
                        raw_cost=rule["source_cost_text"],
                        resolution_mode=rule["resolution_mode"],
                        selector=rule["selector"],
                        selected_item=selected_item,
                        supplemental_items=supplemental,
                        supplemental_reason=supplemental_reason,
                    )
                )

            sections.append(
                MarketSection(
                    category_roll=category_roll,
                    category_code=cat["category_code"],
                    category_name=cat["name"],
                    description=cat["description"],
                    stock_count_roll=stock_count_roll,
                    stock_roll_attempts=stock_roll_attempts,
                    slots=slots,
                )
            )

        return NightMarket(
            generator_version=GENERATOR_VERSION,
            seed=seed,
            mode=mode,
            gm_choice_behavior=gm_choice_behavior,
            category_roll_attempts=category_roll_attempts,
            sections=sections,
        )
