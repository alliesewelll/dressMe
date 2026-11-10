"""Read-only wardrobe ranking preview; does not call AI or save recommendations."""
import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from models import User, StyleProfile, ClothingItem
from schemas import WardrobeRankingResponse
from wardrobe_ranking import rank_wardrobe, coverage_report


def preview(db, user_id, category=None, limit=10, min_score=0, include_coverage=False):
    if db.get(User, user_id) is None:
        raise ValueError('User not found')
    profile = db.scalar(select(StyleProfile).where(StyleProfile.user_id == user_id))
    query = select(ClothingItem).where(ClothingItem.user_id == user_id)
    if category is not None:
        query = query.where(func.lower(func.trim(ClothingItem.category)) == category.strip().lower())
    items = db.scalars(query).all()
    ranked = rank_wardrobe(items, profile, limit=len(items))
    selected = [row for row in ranked if row['score'] >= min_score][:limit]
    result = WardrobeRankingResponse(user_id=user_id, items=selected).model_dump(exclude={'coverage'})
    result['filters'] = {'category': category.strip().lower() if category is not None else None,
                         'limit': limit, 'min_score': min_score}
    if include_coverage:
        result['coverage'] = coverage_report(ranked, min_score, limit)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user-id', type=int, required=True)
    parser.add_argument('--category')
    parser.add_argument('--limit', type=int, choices=range(1, 51), default=10)
    parser.add_argument('--min-score', type=int, choices=range(4), default=0)
    parser.add_argument('--coverage', action='store_true', help='Include full candidate-pool match coverage and score counts')
    args = parser.parse_args()
    if args.user_id < 1:
        parser.error('--user-id must be positive')
    if args.category is not None and not 1 <= len(args.category.strip()) <= 50:
        parser.error('--category must contain 1–50 characters')
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    url = os.environ.get('DATABASE_URL')
    if not url:
        parser.error('Set DATABASE_URL in the environment or root .env')
    engine = create_engine(url)
    try:
        with Session(engine) as db:
            result = preview(db, args.user_id, args.category, args.limit, args.min_score, args.coverage)
        print(json.dumps(result, indent=2, allow_nan=False))
    except ValueError as error:
        parser.exit(1, f'{error}\n')
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
