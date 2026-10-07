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
