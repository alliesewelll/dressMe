"""API regression tests using a disposable SQLite database, never the configured DB."""
import os
import tempfile
import unittest

_database_dir = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{_database_dir.name}/test.db"

from fastapi.testclient import TestClient
from main import app
from database import engine, SessionLocal
from models import Base, User, StyleProfile
from schemas import UserCreate, UserResponse
from pydantic import ValidationError
from sqlalchemy import select, func


class WardrobeTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        with SessionLocal() as db:
            db.add_all([
                User(username="one", email="one@example.com", password_hash="test-only"),
                User(username="two", email="two@example.com", password_hash="test-only"),
            ])
            db.commit()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_summary_totals_and_missing_prices(self):
        for payload in [
            {"item_name": "Shirt", "purchase_price": "19.95", "times_worn": 3},
            {"item_name": "Jeans", "purchase_price": "40.10", "times_worn": 2},
            {"item_name": "Gift", "purchase_price": "0.00"},
            {"item_name": "Unknown price"},
        ]:
            self.assertEqual(self.client.post("/users/1/wardrobe", json=payload).status_code, 201)
        self.client.post("/users/2/wardrobe", json={"item_name": "Other user's coat", "purchase_price": "100", "times_worn": 50})
        response = self.client.get("/users/1/wardrobe/summary")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "user_id": 1, "item_count": 4, "priced_item_count": 3,
            "total_recorded_spend": "60.05", "total_wears": 5, "unworn_item_count": 2,
        })
        item_id = self.client.get("/users/1/wardrobe").json()[0]["item_id"]
        self.client.patch(f"/users/1/wardrobe/{item_id}", json={"purchase_price": "10.00", "times_worn": 1})
        updated = self.client.get("/users/1/wardrobe/summary").json()
        self.assertEqual(updated["total_recorded_spend"], "70.05")
        self.assertEqual(updated["priced_item_count"], 4)
        self.assertEqual(updated["total_wears"], 6)
        self.assertEqual(updated["unworn_item_count"], 1)

    def test_summary_empty_wardrobe_and_missing_user(self):
        response = self.client.get("/users/1/wardrobe/summary")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "user_id": 1, "item_count": 0, "priced_item_count": 0,
            "total_recorded_spend": "0.00", "total_wears": 0, "unworn_item_count": 0,
        })
        self.assertEqual(self.client.get("/users/999/wardrobe/summary").status_code, 404)

    def test_saved_item_and_user_isolation(self):
        response = self.client.post("/users/1/wardrobe", json={
            "item_name": "  Blue shirt  ", "primary_color": "Blue", "purchase_price": "29.95"
        })
        self.assertEqual(response.status_code, 201)
        item = response.json()
        self.assertEqual(item["item_name"], "Blue shirt")
        self.assertEqual(item["purchase_price"], "29.95")
        self.assertEqual(item["times_worn"], 0)
        self.assertEqual(self.client.get("/users/1/wardrobe").json(), [item])
        self.assertEqual(self.client.get("/users/2/wardrobe").json(), [])

    def test_missing_user(self):
        self.assertEqual(self.client.get("/users/999/wardrobe").status_code, 404)
        self.assertEqual(self.client.post("/users/999/wardrobe", json={"item_name": "Shirt"}).status_code, 404)

    def test_invalid_input(self):
        for invalid in [{"item_name": " "}, {"purchase_price": -1},
                        {"purchase_price": "1.001"}, {"times_worn": -1},
                        {"category": "x" * 51}, {"user_id": 2}]:
            with self.subTest(invalid=invalid):
                response = self.client.post("/users/1/wardrobe", json={"item_name": "Shirt", **invalid})
                self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get("/users/1/wardrobe").json(), [])

    def test_edit_item_preserves_omitted_fields_and_clears_optional_fields(self):
        original = self.client.post("/users/1/wardrobe", json={
            "item_name": "Shirt", "brand": "Example", "times_worn": 5,
            "purchase_price": "25.50"
        }).json()
        path = f"/users/1/wardrobe/{original['item_id']}"
        response = self.client.patch(path, json={"item_name": " Blue shirt ", "brand": None})
        self.assertEqual(response.status_code, 200)
        edited = response.json()
        self.assertEqual(edited["item_name"], "Blue shirt")
        self.assertIsNone(edited["brand"])
        self.assertEqual(edited["times_worn"], 5)
        self.assertEqual(edited["purchase_price"], "25.50")
        self.assertEqual(edited["created_at"], original["created_at"])
        response = self.client.patch(path, json={"times_worn": 6})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/users/1/wardrobe").json(), [response.json()])

    def test_edit_rejects_invalid_input_without_changing_item(self):
        original = self.client.post("/users/1/wardrobe", json={"item_name": "Shirt"}).json()
        path = f"/users/1/wardrobe/{original['item_id']}"
        for payload in [{}, {"item_name": None}, {"item_name": " "},
                        {"times_worn": None}, {"times_worn": -1},
                        {"purchase_price": "1.001"}, {"purchase_price": -1},
                        {"category": "x" * 51}, {"user_id": 2}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.patch(path, json=payload).status_code, 422)
        self.assertEqual(self.client.get("/users/1/wardrobe").json(), [original])

    def test_edit_requires_item_to_belong_to_selected_user(self):
        original = self.client.post("/users/1/wardrobe", json={"item_name": "Shirt"}).json()
        for path in [f"/users/2/wardrobe/{original['item_id']}",
                     "/users/1/wardrobe/999", "/users/999/wardrobe/1"]:
            self.assertEqual(self.client.patch(path, json={"times_worn": 10}).status_code, 404)
        self.assertEqual(self.client.get("/users/1/wardrobe").json(), [original])

    def test_wardrobe_search_and_combined_filters(self):
        for user_id, name, category, color in [
            (1, "Blue shirt", "Tops", "Blue"),
            (1, "Blue jeans", "Bottoms", "Blue"),
            (1, "White shirt", "Tops", "White"),
            (2, "Blue shirt", "Tops", "Blue"),
        ]:
            self.client.post(f"/users/{user_id}/wardrobe", json={
                "item_name": name, "category": category, "primary_color": color
            })
        path = "/users/1/wardrobe"
        response = self.client.get(path, params={"search": " SHIRT ", "category": " tops ", "color": "BLUE"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["item_name"] for item in response.json()], ["Blue shirt"])
        page = self.client.get(path, params={"category": "tops", "limit": 1, "offset": 1})
        self.assertEqual([item["item_name"] for item in page.json()], ["Blue shirt"])
        self.assertEqual(self.client.get(path, params={"color": "green"}).json(), [])
        self.assertEqual(len(self.client.get(path, params={"search": " ", "category": ""}).json()), 3)

    def test_search_treats_wildcards_as_literal_text(self):
        for name in ["100% cotton", "Size_M shirt", "Plain shirt"]:
            self.client.post("/users/1/wardrobe", json={"item_name": name})
        for term, expected in [("%", "100% cotton"), ("_", "Size_M shirt")]:
            response = self.client.get("/users/1/wardrobe", params={"search": term})
            self.assertEqual([item["item_name"] for item in response.json()], [expected])
        for field, length in [("search", 101), ("category", 51), ("color", 51)]:
            self.assertEqual(self.client.get("/users/1/wardrobe", params={field: "x" * length}).status_code, 422)

    def test_pagination(self):
        for name in ["First", "Second", "Third"]:
            self.client.post("/users/1/wardrobe", json={"item_name": name})
        response = self.client.get("/users/1/wardrobe?limit=1&offset=1")
        self.assertEqual([item["item_name"] for item in response.json()], ["Second"])
        self.assertEqual(self.client.get("/users/1/wardrobe?limit=101").status_code, 422)

    def test_save_retrieve_and_update_preferences(self):
        path = "/users/1/style-profile"
        response = self.client.patch(path, json={"color_season": " Autumn ", "preferred_styles": "Classic, relaxed"})
        self.assertEqual(response.status_code, 200)
        original = response.json()
        self.assertEqual(original["color_season"], "Autumn")
        self.assertEqual(self.client.get(path).json(), original)
        updated = self.client.patch(path, json={"undertone": "Warm"}).json()
        self.assertEqual(updated["profile_id"], original["profile_id"])
        self.assertEqual(updated["preferred_styles"], "Classic, relaxed")
        self.assertEqual(updated["undertone"], "Warm")
        cleared = self.client.patch(path, json={"undertone": None}).json()
        self.assertIsNone(cleared["undertone"])
        self.assertEqual(cleared["color_season"], "Autumn")
        with SessionLocal() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(StyleProfile)), 1)

    def test_preferences_are_scoped_to_user(self):
        self.client.patch("/users/1/style-profile", json={"preferred_styles": "Classic"})
        self.assertEqual(self.client.get("/users/2/style-profile").status_code, 404)
        self.client.patch("/users/2/style-profile", json={"preferred_styles": "Minimal"})
        self.assertEqual(self.client.get("/users/1/style-profile").json()["preferred_styles"], "Classic")
        self.assertEqual(self.client.get("/users/2/style-profile").json()["preferred_styles"], "Minimal")

    def test_profile_missing_user_and_invalid_input(self):
        self.assertEqual(self.client.get("/users/999/style-profile").status_code, 404)
        self.assertEqual(self.client.patch("/users/999/style-profile", json={"undertone": "Warm"}).status_code, 404)
        for payload in [{}, {"undertone": " "}, {"color_season": "x" * 51},
                        {"preferred_styles": "x" * 2001}, {"user_id": 2},
                        {"preferred_styles": ["Classic"]}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.patch("/users/1/style-profile", json=payload).status_code, 422)
        self.assertEqual(self.client.get("/users/1/style-profile").status_code, 404)

    def test_user_schema_matches_model_without_exposing_hash(self):
        with SessionLocal() as db:
            data = UserResponse.model_validate(db.get(User, 1)).model_dump()
        self.assertEqual(data["username"], "one")
        self.assertNotIn("password_hash", data)
        self.assertNotIn("password", data)
        request = UserCreate(username="new", email="new@example.com", password="secret-pass")
        self.assertNotIn("secret-pass", request.model_dump_json())
        with self.assertRaises(ValidationError):
            UserCreate(name="old", email="new@example.com")


if __name__ == "__main__":
    unittest.main()
