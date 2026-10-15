"""Build bounded, user-scoped evidence for personalized model suggestions."""
from sqlalchemy import select, func, and_
from models import Feedback, Recommendation, ClothingItem


def feedback_context(db, user_id, limit=20):
    # Legacy data can contain multiple reviews; use only the latest per decision.
    latest = (select(Feedback.recommendation_id,
                     func.max(Feedback.feedback_id).label('latest_id'))
              .where(Feedback.user_id == user_id)
              .group_by(Feedback.recommendation_id).subquery())
    rows = db.execute(
        select(Feedback, Recommendation, ClothingItem)
        .join(latest, Feedback.feedback_id == latest.c.latest_id)
        .join(Recommendation, and_(Feedback.recommendation_id == Recommendation.recommendation_id,
                                  Recommendation.user_id == user_id))
        .outerjoin(ClothingItem, and_(Recommendation.item_id == ClothingItem.item_id,
                                     ClothingItem.user_id == user_id))
        .order_by(Feedback.feedback_id.desc()).limit(limit)
    ).all()
    return [
        {'reaction': review.feedback, 'rating': review.rating, 'purchased': review.purchased,
         'comments': review.comments[:2000] if review.comments else None,
         'decision': recommendation.recommendation,
         'reason': recommendation.recommendation_reason[:2000] if recommendation.recommendation_reason else None,
         'item': {'name': item.item_name, 'category': item.category, 'color': item.primary_color,
                  'brand': item.brand} if item else None}
        for review, recommendation, item in rows
    ]
