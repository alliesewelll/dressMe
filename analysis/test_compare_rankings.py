import unittest
from compare_rankings import compare


def snapshot(ids, user=1):
    return {'user_id': user, 'method': 'test', 'items': [{'item_id': i} for i in ids]}


class ComparisonTests(unittest.TestCase):
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
