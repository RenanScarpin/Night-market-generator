from __future__ import annotations

import json
import unittest
from pathlib import Path

from nightmarket.generator import NightMarketGenerator
from nightmarket.repository import MarketRepository
from nightmarket.renderers import render_json


ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "cyberpunk_red_2045_market_ready.sqlite"


class NightMarketTests(unittest.TestCase):
    def setUp(self):
        self.repo = MarketRepository(DB)
        self.gen = NightMarketGenerator(self.repo)

    def tearDown(self):
        self.repo.close()

    def test_same_seed_is_identical(self):
        a = self.gen.generate(mode="expanded_2045", seed=123456)
        b = self.gen.generate(mode="expanded_2045", seed=123456)
        self.assertEqual(render_json(a), render_json(b))

    def test_different_seed_changes_market(self):
        a = self.gen.generate(mode="expanded_2045", seed=111)
        b = self.gen.generate(mode="expanded_2045", seed=222)
        self.assertNotEqual(render_json(a), render_json(b))

    def test_two_different_categories(self):
        market = self.gen.generate(mode="core_raw", seed=42)
        self.assertEqual(len(market.sections), 2)
        self.assertNotEqual(
            market.sections[0].category_roll,
            market.sections[1].category_roll,
        )

    def test_no_duplicate_table_result_within_section(self):
        market = self.gen.generate(mode="core_raw", seed=777)
        for section in market.sections:
            ids = [s.stock_roll_id for s in section.slots]
            self.assertEqual(len(ids), len(set(ids)))

    def test_stock_count_is_d10_result(self):
        for seed in range(25):
            market = self.gen.generate(mode="core_raw", seed=seed)
            for section in market.sections:
                self.assertGreaterEqual(section.stock_count_roll, 1)
                self.assertLessEqual(section.stock_count_roll, 10)
                self.assertEqual(len(section.slots), section.stock_count_roll)

    def test_expanded_selected_items_are_candidates(self):
        market = self.gen.generate(mode="expanded_2045", seed=998877)
        for section in market.sections:
            for slot in section.slots:
                if slot.selected_item is None:
                    continue
                candidate_ids = self.repo.get_stock_candidates(slot.stock_roll_id)
                self.assertIn(slot.selected_item.item_id, candidate_ids)

    def test_core_raw_never_resolves_to_concrete_item(self):
        market = self.gen.generate(mode="core_raw", seed=24680)
        for section in market.sections:
            for slot in section.slots:
                self.assertIsNone(slot.selected_item)

    def test_gm_leave_is_supported(self):
        # Find a seed that produces at least one GM-choice slot, then ensure
        # it can remain unresolved without breaking generation.
        found = False
        for seed in range(5000):
            market = self.gen.generate(
                mode="expanded_2045",
                seed=seed,
                gm_choice_behavior="leave",
            )
            gm_slots = [
                slot
                for section in market.sections
                for slot in section.slots
                if slot.resolution_mode == "gm_choice"
            ]
            if gm_slots:
                found = True
                self.assertTrue(all(s.selected_item is None for s in gm_slots))
                break
        self.assertTrue(found, "No GM-choice stock slot found in seed search.")

    def test_cyberware_foundation_rule_can_trigger(self):
        # Search deterministic seeds for a cyberware option that resolves to
        # an item with required foundational cyberware.
        found = False
        for seed in range(20000):
            market = self.gen.generate(mode="expanded_2045", seed=seed)
            for section in market.sections:
                for slot in section.slots:
                    if slot.supplemental_items:
                        found = True
                        self.assertEqual(section.category_code, "cyberware")
                        self.assertIsNotNone(slot.selected_item)
                        break
                if found:
                    break
            if found:
                break
        self.assertTrue(found, "Did not encounter foundational cyberware in seed search.")

    def test_raw_table_known_entry(self):
        row = self.repo.get_stock_roll("weapons_armor", 73)
        self.assertEqual(row["display_text"], "Very Heavy Melee Weapon")
        self.assertEqual(row["source_cost_text"], "100eb (Premium)")


if __name__ == "__main__":
    unittest.main()
