from __future__ import annotations

import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app


ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "cyberpunk_red_2045_market_ready.sqlite"


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(DB)
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["database_ok"])
        self.assertEqual(data["item_count"], 1150)

    def test_meta_contract(self):
        response = self.client.get("/api/meta")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["item_count"], 1150)
        self.assertIn("core_raw", data["supported_modes"])
        self.assertIn("expanded_2045", data["supported_modes"])
        self.assertEqual(set(data["supported_gm_choice"]), {"random", "leave"})

    def test_post_generate_is_deterministic(self):
        payload = {
            "mode": "expanded_2045",
            "seed": 2045,
            "gm_choice": "random",
        }
        a = self.client.post("/api/markets/generate", json=payload)
        b = self.client.post("/api/markets/generate", json=payload)
        self.assertEqual(a.status_code, 200)
        self.assertEqual(b.status_code, 200)
        self.assertEqual(a.json(), b.json())
        self.assertEqual(a.json()["seed"], 2045)

    def test_get_market_regenerates_post_market(self):
        payload = {
            "mode": "expanded_2045",
            "seed": 24680,
            "gm_choice": "random",
        }
        post = self.client.post("/api/markets/generate", json=payload)
        get = self.client.get(
            "/api/markets/24680",
            params={"mode": "expanded_2045", "gm_choice": "random"},
        )
        self.assertEqual(post.status_code, 200)
        self.assertEqual(get.status_code, 200)
        self.assertEqual(post.json(), get.json())

    def test_core_raw_does_not_resolve_items(self):
        response = self.client.post(
            "/api/markets/generate",
            json={"mode": "core_raw", "seed": 777, "gm_choice": "random"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for section in data["sections"]:
            for slot in section["slots"]:
                self.assertIsNone(slot["selected_item"])

    def test_prompt_is_not_part_of_http_contract(self):
        response = self.client.post(
            "/api/markets/generate",
            json={
                "mode": "expanded_2045",
                "seed": 1,
                "gm_choice": "prompt",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_extra_request_field_is_rejected(self):
        response = self.client.post(
            "/api/markets/generate",
            json={
                "mode": "expanded_2045",
                "seed": 1,
                "gm_choice": "random",
                "surprise": True,
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_item_search(self):
        response = self.client.get(
            "/api/items",
            params={"q": "Militech", "limit": 10},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["total"], 0)
        self.assertLessEqual(len(data["items"]), 10)
        self.assertTrue(
            any("militech" in item["canonical_name"].lower() for item in data["items"])
        )

    def test_item_filter_by_tag(self):
        response = self.client.get(
            "/api/items",
            params={"tag": "weapon.medium_pistol", "limit": 100},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["total"], 0)

    def test_invalid_cost_range_returns_400(self):
        response = self.client.get(
            "/api/items",
            params={"min_cost_eb": 1000, "max_cost_eb": 100},
        )
        self.assertEqual(response.status_code, 400)

    def test_item_detail(self):
        search = self.client.get(
            "/api/items",
            params={"q": "Militech Avenger", "limit": 10},
        )
        self.assertEqual(search.status_code, 200)
        items = search.json()["items"]
        exact = next(
            item for item in items if item["canonical_name"] == "Militech Avenger"
        )
        response = self.client.get(f"/api/items/{exact['item_id']}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["canonical_name"], "Militech Avenger")
        self.assertTrue(data["canon_2045"])
        self.assertTrue(data["sources"])
        self.assertTrue(data["categories"])
        self.assertIsInstance(data["mechanics"], (dict, type(None)))

    def test_unknown_item_404(self):
        response = self.client.get("/api/items/99999999")
        self.assertEqual(response.status_code, 404)

    def test_categories(self):
        response = self.client.get("/api/categories")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0)
        self.assertTrue(all("item_count" in row for row in data))

    def test_tags(self):
        response = self.client.get("/api/tags")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0)
        codes = {row["code"] for row in data}
        self.assertIn("market.expanded_2045", codes)

    def test_raw_market_categories(self):
        response = self.client.get("/api/market-categories")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 6)
        self.assertEqual([row["d6_roll"] for row in data], [1, 2, 3, 4, 5, 6])

    def test_openapi_contains_contract_endpoints(self):
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        paths = response.json()["paths"]
        for path in [
            "/api/health",
            "/api/meta",
            "/api/markets/generate",
            "/api/markets/{seed}",
            "/api/items",
            "/api/items/{item_id}",
            "/api/categories",
            "/api/tags",
            "/api/market-categories",
        ]:
            self.assertIn(path, paths)

    def test_cors_preflight_for_local_frontend(self):
        response = self.client.options(
            "/api/markets/generate",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:3000",
        )


if __name__ == "__main__":
    unittest.main()
