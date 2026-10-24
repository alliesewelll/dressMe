"""Descriptive feature feedback, separated by decision to avoid treating liked
SKIP advice as affection for a garment. Not learned preference weights.
"""
import pandas as pd


def summarize_features(reviews):
    rows = []
    for review in reviews:
        item = review.get('item')
        if not item:
            continue
        for feature in ('color', 'category'):
            value = ' '.join((item.get(feature) or '').casefold().split())
            if value:
                rows.append({'feature': feature, 'value': value,
                             'decision': review['decision'],
                             'liked': review['reaction'] == 'LIKE',
                             'rating': review['rating']})
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    result = []
    for (feature, value, decision), group in frame.groupby(['feature', 'value', 'decision'], sort=True):
        ratings = group.rating.dropna()
        result.append({'feature': feature, 'value': value, 'decision': decision,
                       'review_count': len(group), 'like_rate': float(group.liked.mean()),
                       'rating_count': len(ratings),
                       'average_rating': float(ratings.mean()) if len(ratings) else None})
    return result
