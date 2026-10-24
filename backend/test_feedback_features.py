import unittest
import test_wardrobe
from feedback_features import summarize_features


class FeedbackFeatureTests(unittest.TestCase):
    setUp = test_wardrobe.WardrobeTests.setUp
    tearDown = test_wardrobe.WardrobeTests.tearDown

    def test_decisions_stay_separate_and_missing_ratings_unknown(self):
        def review(decision, reaction, rating, color):
            return dict(decision=decision, reaction=reaction, rating=rating,
                        item={'color': color, 'category': None})
        result = summarize_features([
            review('BUY', 'LIKE', 5, ' Pink '), review('BUY', 'DISLIKE', None, 'pink'),
            review('SKIP', 'LIKE', None, 'pink'),
            dict(decision='BUY', reaction='LIKE', rating=5, item=None)])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['review_count'], 2)
        self.assertEqual(result[0]['like_rate'], .5)
        self.assertEqual(result[0]['average_rating'], 5)
        self.assertEqual(result[0]['rating_count'], 1)
        self.assertEqual(result[1]['decision'], 'SKIP')
        self.assertIsNone(result[1]['average_rating'])

    def test_api_scope_and_updated_review(self):
        item = self.client.post('/users/1/wardrobe', json={'item_name': 'Top', 'primary_color': 'pink', 'category': 'Tops'}).json()
        rec = self.client.post('/users/1/recommendations', json={'item_id': item['item_id'], 'recommendation': 'BUY', 'recommendation_reason': 'Palette match'}).json()
        path = f"/users/1/recommendations/{rec['recommendation_id']}/feedback"
        for reaction in ['DISLIKE', 'LIKE']:
            self.assertEqual(self.client.put(path, json={'feedback': reaction}).status_code, 200)
        result = self.client.get('/users/1/feedback-features').json()
        self.assertEqual(result['reviewed_recommendations'], 1)
        self.assertEqual(len(result['metrics']), 2)
        self.assertTrue(all(row['like_rate'] == 1 for row in result['metrics']))
        self.assertEqual(self.client.get('/users/2/feedback-features').json()['metrics'], [])
        self.assertEqual(self.client.get('/users/999/feedback-features').status_code, 404)
