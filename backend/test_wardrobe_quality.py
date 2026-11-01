import unittest
from types import SimpleNamespace
import test_wardrobe
from wardrobe_quality import FIELDS, summarize_quality


class QualityTests(unittest.TestCase):
    setUp = test_wardrobe.WardrobeTests.setUp
    tearDown = test_wardrobe.WardrobeTests.tearDown

    def test_missing_details_and_scope(self):
        item = self.client.post('/users/1/wardrobe', json={'item_name': 'Shirt', 'primary_color': 'pink', 'category': 'Tops', 'material': '  '}).json()
        self.client.post('/users/2/wardrobe', json={'item_name': 'Other wardrobe'})
        response = self.client.get('/users/1/wardrobe-quality')
        self.assertEqual(response.status_code, 200)
        report = response.json()
        self.assertEqual(report['item_count'], 1)
        self.assertEqual(report['missing_counts']['primary_color'], 0)
        self.assertEqual(report['missing_counts']['material'], 1)
        self.assertEqual(report['items'][0]['item_id'], item['item_id'])
        self.assertEqual(report['items'][0]['missing_fields'], ['material', 'pattern', 'subcategory'])
        self.assertFalse(report['truncated'])
        self.client.patch(f"/users/1/wardrobe/{item['item_id']}", json={'material': 'cotton', 'pattern': 'solid', 'subcategory': 'shirt'})
        self.assertEqual(self.client.get('/users/1/wardrobe-quality').json()['items'], [])

    def test_empty_and_missing_user(self):
        report = self.client.get('/users/1/wardrobe-quality').json()
        self.assertEqual(report['item_count'], 0)
        self.assertEqual(report['items'], [])
        self.assertTrue(all(value == 0 for value in report['missing_counts'].values()))
        self.assertEqual(self.client.get('/users/999/wardrobe-quality').status_code, 404)

    def test_preview_limit_preserves_total_counts(self):
        items = [SimpleNamespace(item_id=i, item_name='Top', **dict.fromkeys(FIELDS)) for i in range(55, 0, -1)]
        report = summarize_quality(items)
        self.assertEqual(report['item_count'], 55)
        self.assertEqual(report['items_with_missing_details'], 55)
        self.assertEqual(report['missing_counts']['category'], 55)
        self.assertEqual(len(report['items']), 50)
        self.assertEqual(report['items'][0]['item_id'], 1)
        self.assertTrue(report['truncated'])
