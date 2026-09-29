from __future__ import annotations

import unittest
from pathlib import Path

from nightmarket.repository import MarketRepository

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "cyberpunk_red_2045_market_ready.sqlite"


class DatabaseCleanupTests(unittest.TestCase):
    def setUp(self):
        self.repo = MarketRepository(DB)

    def tearDown(self):
        self.repo.close()

    def test_assault_rifle_description_is_not_table_dump(self):
        item_id = self.repo.get_item_id_by_name("Assault Rifle")
        self.assertIsNotNone(item_id)
        detail = self.repo.get_item_detail(item_id)
        self.assertEqual(detail["info"], "")
        rules = detail["mechanics"]["rules"]
        self.assertEqual(rules["weapon_skill"], "Shoulder Arms")
        self.assertEqual(rules["damage_values"], ["5d6"])
        self.assertEqual(rules["magazine"], "25")
        self.assertEqual(rules["rof"], 1)
        self.assertEqual(rules["hands"], 2)
        self.assertFalse(rules["concealable"])
        self.assertEqual(rules["alt_fire_modes"], "Autofire (4) • Suppressive Fire")

    def test_melee_weapon_classes_are_structured(self):
        expected = {
            "Light Melee Weapon": ("Combat Knife, Tomahawk", "1d6", 2, True),
            "Medium Melee Weapon": ("Baseball Bat, Crowbar, Machete", "2d6", 2, False),
            "Heavy Melee Weapon": ("Lead Pipe, Sword, Spiked Bat", "3d6", 2, False),
            "Very Heavy Melee Weapon": (
                "Chainsaw, Sledgehammer, Helicopter Blades, Naginata",
                "4d6",
                1,
                False,
            ),
        }
        for name, (info, damage, rof, concealable) in expected.items():
            item_id = self.repo.get_item_id_by_name(name)
            detail = self.repo.get_item_detail(item_id)
            self.assertEqual(detail["info"], info)
            rules = detail["mechanics"]["rules"]
            self.assertEqual(rules["weapon_skill"], "Melee Weapon")
            self.assertEqual(rules["hands"], "Varies by type")
            self.assertEqual(rules["damage_values"], [damage])
            self.assertEqual(rules["rof"], rof)
            self.assertEqual(rules["concealable"], concealable)
            self.assertNotIn("magazine", rules)

    def test_live_chicken_is_not_a_catalogue_item(self):
        self.assertIsNone(self.repo.get_item_id_by_name("Live Chicken"))
        items, total = self.repo.list_items(q="Live Chicken", limit=20, offset=0)
        self.assertEqual(items, [])
        self.assertEqual(total, 0)

    def test_live_chicken_raw_result_remains_static(self):
        row = self.repo.get_stock_roll("food_drugs", 58)
        self.assertEqual(row["display_text"], "Live Chicken")
        self.assertEqual(row["resolution_mode"], "static")
        self.assertEqual(row["selector"], {"type": "static"})
        self.assertEqual(self.repo.get_stock_candidates(row["stock_roll_id"]), [])


if __name__ == "__main__":
    unittest.main()
