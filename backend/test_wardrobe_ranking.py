"""Exercise ranking through the API with the disposable test database."""
import unittest
import test_wardrobe


class RankingTests(unittest.TestCase):
    setUp = test_wardrobe.WardrobeTests.setUp
    tearDown = test_wardrobe.WardrobeTests.tearDown

    def test_rank_palette_and_keywords_and_scope(self):
        self.client.patch('/users/1/style-profile', json={'undertone': 'warm', 'preferred_styles': 'casual, knit'})
        plain = self.client.post('/users/1/wardrobe', json={'item_name': 'Shirt', 'primary_color': 'blue'}).json()
        match = self.client.post('/users/1/wardrobe', json={'item_name': 'Casual knit top', 'primary_color': ' Cream '}).json()
        self.client.post('/users/2/wardrobe', json={'item_name': 'Casual knit secret', 'primary_color': 'cream'})
        result = self.client.get('/users/1/wardrobe-ranking').json()
        self.assertEqual([row['item_id'] for row in result['items']], [match['item_id'], plain['item_id']])
        self.assertEqual(result['items'][0]['score'], 3)
        self.assertEqual(len(result['items'][0]['reasons']), 2)
        self.assertEqual(len(self.client.get('/users/1/wardrobe-ranking?limit=1').json()['items']), 1)

    def test_cold_start_unknown_palette_and_validation(self):
        self.assertEqual(self.client.get('/users/1/wardrobe-ranking').json()['items'], [])
        self.client.post('/users/1/wardrobe', json={'item_name': 'Navy shirt', 'primary_color': 'navy'})
        self.assertEqual(self.client.get('/users/1/wardrobe-ranking').json()['items'][0]['score'], 0)
        self.client.patch('/users/1/style-profile', json={'color_season': 'unknown'})
        self.assertEqual(self.client.get('/users/1/wardrobe-ranking').json()['items'][0]['score'], 0)
        self.assertEqual(self.client.get('/users/999/wardrobe-ranking').status_code, 404)
        self.assertEqual(self.client.get('/users/1/wardrobe-ranking?limit=0').status_code, 422)
