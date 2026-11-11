import unittest
from compare_rankings import compare


def snapshot(ids, user=1):
    return {'user_id': user, 'method': 'test', 'items': [{'item_id': i} for i in ids]}


class ComparisonTests(unittest.TestCase):
    def test_input_consistency_and_legacy_support(self):
        before, after = snapshot([1]), snapshot([1])
        self.assertEqual(compare(before, after)['input_matches'], {'wardrobe': None, 'profile': None})
        before['input_fingerprints'] = {'version': 1, 'wardrobe': 'a' * 64, 'profile': 'b' * 64}
        self.assertIsNone(compare(before, after)['input_matches']['wardrobe'])
        after['input_fingerprints'] = dict(before['input_fingerprints'])
        self.assertEqual(compare(before, after)['input_matches'], {'wardrobe': True, 'profile': True})
        for field in ('wardrobe', 'profile'):
            after['input_fingerprints'][field] = 'c' * 64
            self.assertFalse(compare(before, after)['input_matches'][field])
            self.assertTrue(any(f'{field.capitalize()} inputs differ' in warning
                                for warning in compare(before, after)['warnings']))
        after['input_fingerprints']['version'] = 2
        self.assertIsNone(compare(before, after)['input_matches']['wardrobe'])
        before['input_fingerprints']['version'] = 2
        self.assertIsNone(compare(before, after)['input_matches']['wardrobe'])

    def test_malformed_fingerprints(self):
        for invalid in [None, {}, {'version': True, 'wardrobe': 'a' * 64, 'profile': 'b' * 64},
                        {'version': 1, 'wardrobe': 'bad', 'profile': 'b' * 64}]:
            after = snapshot([1])
            after['input_fingerprints'] = invalid
            with self.assertRaises(ValueError):
                compare(snapshot([1]), after)

    def test_entries_exits_and_rank_movement(self):
        result = compare(snapshot([1, 2, 3]), snapshot([3, 2, 4]))
        self.assertEqual(result['overlap_jaccard'], .5)
        self.assertEqual(result['entered_item_ids'], [4])
        self.assertEqual(result['exited_item_ids'], [1])
        self.assertEqual(result['rank_changes'], [{'item_id': 3, 'before_rank': 3, 'after_rank': 1, 'positions_gained': 2}])

    def test_empty_and_identical(self):
        self.assertIsNone(compare(snapshot([]), snapshot([]))['overlap_jaccard'])
        self.assertEqual(compare(snapshot([]), snapshot([1]))['overlap_jaccard'], 0)
        result = compare(snapshot([1, 2]), snapshot([1, 2]))
        self.assertEqual(result['overlap_jaccard'], 1)
        self.assertEqual(result['rank_changes'], [])

    def test_invalid_snapshots(self):
        for invalid in [None, {}, snapshot([1, 1]), snapshot([True]), {'user_id': 1, 'items': 'bad'}]:
            with self.assertRaises(ValueError):
                compare(snapshot([1]), invalid)
        with self.assertRaisesRegex(ValueError, 'same user'):
            compare(snapshot([1]), snapshot([1], user=2))

    def test_filter_changes_and_legacy_snapshots(self):
        before, after = snapshot([1]), snapshot([1])
        self.assertIsNone(compare(before, after)['filters_match'])
        before['filters'] = {'category': ' Tops ', 'limit': 5, 'min_score': 1}
        after['filters'] = {'category': 'tops', 'limit': 5, 'min_score': 1}
        self.assertTrue(compare(before, after)['filters_match'])
        after['filters']['limit'] = 10
        result = compare(before, after)
        self.assertFalse(result['filters_match'])
        self.assertEqual(result['filter_changes'], [{'field': 'limit', 'before': 5, 'after': 10}])
        self.assertIn('Filters differ', result['warnings'][0])
        after['filters']['min_score'] = True
        with self.assertRaises(ValueError):
            compare(before, after)
