"""API regression tests using a disposable SQLite database, never the configured DB."""
import os
import tempfile
import unittest

_database_dir = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{_database_dir.name}/test.db"

from fastapi.testclient import TestClient
from main import app
from database import engine, SessionLocal
from models import Base, User


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


if __name__ == "__main__":
    unittest.main()
