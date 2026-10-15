import unittest
import pandas as pd
from evaluate_recommendations import summarize

class EvaluationTests(unittest.TestCase):
    def test_unknown_outcomes_and_duplicate_reviews(self):
        rows=[(1,'BUY',1,'LIKE',5,True),(1,'BUY',2,'DISLIKE',2,False),
              (2,'BUY',3,'LIKE',None,None),(3,'BUY',None,None,None,None)]
        frame=pd.DataFrame(rows,columns=['recommendation_id','recommendation','feedback_id','feedback','rating','purchased'])
        report=summarize(frame)[0]
        self.assertEqual(report['recommendation_count'],3)
        self.assertEqual(report['feedback_count'],2)
        self.assertEqual(report['purchase_response_count'],1)
        self.assertEqual(report['purchase_rate'],0)
        self.assertEqual(report['average_rating'],2)
        self.assertEqual(report['like_rate'],0.5)
    def test_empty_data(self):
        frame=pd.DataFrame(columns=['recommendation_id','recommendation','feedback_id','feedback','rating','purchased'])
        self.assertEqual(summarize(frame),[])
