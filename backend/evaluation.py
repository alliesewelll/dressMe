"""Shared descriptive feedback metrics for the API and analysis CLI."""

def summarize(frame):
    # Older seed/import data may have multiple feedback rows. Count one latest response per recommendation.
    latest = frame.sort_values('feedback_id', na_position='first').drop_duplicates('recommendation_id', keep='last')
    result = []
    for label, group in latest.groupby('recommendation'):
        responded = group[group.feedback_id.notna()]
        purchases = responded.purchased.dropna()
        ratings = responded.rating.dropna()
        result.append({'recommendation': label, 'recommendation_count': len(group),
                       'feedback_count': len(responded),
                       'feedback_coverage': len(responded)/len(group),
                       'like_rate': float((responded.feedback == 'LIKE').mean()) if len(responded) else None,
                       'purchase_response_count': len(purchases),
                       'purchase_rate': float(purchases.astype(bool).mean()) if len(purchases) else None,
                       'rating_count': len(ratings),
                       'average_rating': float(ratings.mean()) if len(ratings) else None})
    return result

