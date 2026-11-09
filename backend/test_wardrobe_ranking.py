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

    def test_related_colors_score_below_exact_matches(self):
        self.client.patch('/users/1/style-profile', json={'undertone': 'warm'})
        for color in [' OFF-WHITE ', 'cream', 'white', 'blue', None, 'ivory']:
            self.client.post('/users/1/wardrobe', json={'item_name': str(color), 'primary_color': color})
        response = self.client.get('/users/1/wardrobe-ranking').json()
        self.assertEqual(response['method'], 'palette-keywords-v2')
        rows = response['items']
        self.assertEqual([row['score'] for row in rows], [2, 1, 1, 0, 0, 0])
        self.assertEqual(rows[0]['item_name'], 'cream')
        self.assertIn('related shade of cream', rows[1]['reasons'][0])
        self.assertIn('exactly matches', rows[0]['reasons'][0])

    def test_related_colors_require_recognized_preferences(self):
        self.client.post('/users/1/wardrobe', json={'item_name': 'Ivory top', 'primary_color': 'ivory'})
        self.client.patch('/users/1/style-profile', json={'color_season': 'unknown'})
        self.assertEqual(self.client.get('/users/1/wardrobe-ranking').json()['items'][0]['score'], 0)
        self.client.patch('/users/1/style-profile', json={'color_season': 'Light Spring'})
        result = self.client.get('/users/1/wardrobe-ranking').json()['items'][0]
        self.assertEqual(result['score'], 1)
        self.assertIn('warm white', result['reasons'][0])

    def test_category_filter_runs_before_limit_and_is_user_scoped(self):
        self.client.patch('/users/1/style-profile', json={'undertone': 'warm'})
        for owner, name, category, color in [(1, 'Coat', 'Outerwear', 'cream'),
                (1, 'Shirt', ' Tops ', 'blue'), (2, 'Other shirt', 'Tops', 'cream')]:
            self.client.post(f'/users/{owner}/wardrobe', json={
                'item_name': name, 'category': category, 'primary_color': color})
        response = self.client.get('/users/1/wardrobe-ranking', params={'category': ' tops ', 'limit': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['item_name'] for item in response.json()['items']], ['Shirt'])
        self.assertEqual(self.client.get('/users/1/wardrobe-ranking?category=Dresses').json()['items'], [])
        self.assertEqual(len(self.client.get('/users/1/wardrobe-ranking').json()['items']), 2)

    def test_breakdown_explains_total_without_double_counting_keywords(self):
        self.client.patch('/users/1/style-profile', json={'undertone': 'warm', 'preferred_styles': 'knit, casual'})
        for name, color in [('Casual knit top', 'cream'), ('Knit shirt', 'ivory'), ('Plain shirt', 'blue')]:
            self.client.post('/users/1/wardrobe', json={'item_name': name, 'primary_color': color})
        rows = self.client.get('/users/1/wardrobe-ranking').json()['items']
        self.assertEqual([row['score'] for row in rows], [3, 2, 0])
        self.assertEqual([row['breakdown']['color_match'] for row in rows], ['exact', 'related', 'none'])
        self.assertEqual(rows[0]['breakdown']['matched_style_keywords'], ['casual', 'knit'])
        self.assertEqual(rows[0]['breakdown']['style_points'], 1)
        for row in rows:
            self.assertEqual(row['score'], row['breakdown']['color_points'] + row['breakdown']['style_points'])

    def test_minimum_score_filters_and_combines_with_category(self):
        self.client.patch('/users/1/style-profile', json={'undertone': 'warm', 'preferred_styles': 'knit'})
        for name, color, category in [('Plain', 'blue', 'Tops'), ('Ivory', 'ivory', 'Tops'),
                                      ('Knit', 'cream', 'Tops'), ('Coat', 'cream', 'Outerwear')]:
            self.client.post('/users/1/wardrobe', json={'item_name': name, 'primary_color': color, 'category': category})
        base = '/users/1/wardrobe-ranking'
        self.assertEqual(len(self.client.get(base).json()['items']), 4)
        rows = self.client.get(base, params={'min_score': 1, 'category': 'Tops'}).json()['items']
        self.assertEqual([row['item_name'] for row in rows], ['Knit', 'Ivory'])
        rows = self.client.get(base, params={'min_score': 3, 'limit': 1}).json()['items']
        self.assertEqual([row['item_name'] for row in rows], ['Knit'])
        self.assertEqual(self.client.get(base, params={'min_score': 3, 'category': 'Outerwear'}).json()['items'], [])
        for invalid in [-1, 4, 'bad']:
            self.assertEqual(self.client.get(base, params={'min_score': invalid}).status_code, 422)

    def test_minimum_score_without_preferences_returns_no_matches(self):
        self.client.post('/users/1/wardrobe', json={'item_name': 'Shirt', 'primary_color': 'pink'})
        self.assertEqual(self.client.get('/users/1/wardrobe-ranking?min_score=1').json()['items'], [])

    def test_optional_coverage_uses_full_filtered_pool(self):
        self.client.patch('/users/1/style-profile', json={'undertone': 'warm'})
        for owner, color, category in [(1, 'cream', 'Tops'), (1, 'blue', 'Tops'),
                                       (1, 'cream', 'Outerwear'), (2, 'cream', 'Tops')]:
            self.client.post(f'/users/{owner}/wardrobe', json={'item_name': 'Piece', 'primary_color': color, 'category': category})
        url = '/users/1/wardrobe-ranking'
        self.assertNotIn('coverage', self.client.get(url).json())
        result = self.client.get(url, params={'include_coverage': True, 'category': 'Tops', 'limit': 1, 'min_score': 1}).json()
        report = result['coverage']
        self.assertEqual(report['candidate_count'], 2)
        self.assertEqual(report['match_coverage'], .5)
        self.assertEqual(report['eligible_count'], 1)
        self.assertEqual(report['returned_count'], len(result['items']))
        empty = self.client.get(url, params={'include_coverage': True, 'category': 'Dresses'}).json()['coverage']
        self.assertIsNone(empty['match_coverage'])
        self.assertEqual(empty['candidate_count'], 0)
