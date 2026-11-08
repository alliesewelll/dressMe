import unittest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from preview_ranking import preview, coverage_report
from models import Base, User, StyleProfile, ClothingItem, Recommendation


class PreviewTests(unittest.TestCase):
    def test_scoped_filtered_ranking_and_no_writes(self):
        engine = create_engine('sqlite://')
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            db.add_all([User(user_id=i, username=str(i), email=f'{i}@example.com', password_hash='test') for i in [1, 2]])
            db.add(StyleProfile(user_id=1, undertone='warm', preferred_styles='knit'))
            db.add_all([ClothingItem(user_id=1, item_name='Knit top', category='Tops', primary_color='cream'),
                        ClothingItem(user_id=1, item_name='Coat', category='Outerwear', primary_color='cream'),
                        ClothingItem(user_id=2, item_name='Other knit', category='Tops', primary_color='cream')])
            db.commit()
            result = preview(db, 1, ' tops ', 1, 3)
            self.assertEqual([row['item_name'] for row in result['items']], ['Knit top'])
            self.assertEqual(result['items'][0]['breakdown']['color_points'], 2)
            self.assertEqual(result['method'], 'palette-keywords-v2')
            self.assertNotIn('coverage', result)
            report = preview(db, 1, limit=1, min_score=3, include_coverage=True)['coverage']
            self.assertEqual(report['candidate_count'], 2)
            self.assertEqual(report['eligible_count'], 1)
            self.assertEqual(report['returned_count'], 1)
            self.assertEqual(report['match_coverage'], 1.0)
            filtered = preview(db, 1, category='Tops', include_coverage=True)['coverage']
            self.assertEqual(filtered['candidate_count'], 1)
            self.assertEqual(preview(db, 1, 'Dresses')['items'], [])
            self.assertEqual(db.scalar(select(func.count()).select_from(Recommendation)), 0)
            with self.assertRaisesRegex(ValueError, 'User not found'):
                preview(db, 99)
        engine.dispose()

    def test_coverage_denominator_and_empty_pool(self):
        report = coverage_report([{'score': score} for score in [3, 2, 0, 0]], 2, 1)
        self.assertEqual(report['match_coverage'], 0.5)
        self.assertEqual(report['score_distribution'], {'0': 2, '1': 0, '2': 1, '3': 1})
        self.assertEqual(report['eligible_count'], 2)
        self.assertEqual(report['returned_count'], 1)
        empty = coverage_report([], 1, 5)
        self.assertIsNone(empty['match_coverage'])
        self.assertEqual(empty['returned_count'], 0)
        self.assertEqual(coverage_report([{'score': 0}], 1, 5)['match_coverage'], 0)
