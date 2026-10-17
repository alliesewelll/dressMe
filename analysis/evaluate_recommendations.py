"""Read-only feedback evaluation. Run from the project root; outputs JSON, not PII."""
import argparse
import json
import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from evaluation import summarize


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--user-id', type=int, required=True)
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    engine = create_engine(os.environ['DATABASE_URL'])
    query = text('''SELECT r.recommendation_id, r.recommendation, f.feedback_id,
                          f.feedback, f.rating, f.purchased
                   FROM recommendations r LEFT JOIN feedback f
                   ON f.recommendation_id = r.recommendation_id AND f.user_id = r.user_id
                   WHERE r.user_id = :user_id''')
    with engine.connect() as connection:
        frame = pd.read_sql(query, connection, params={'user_id': args.user_id})
    print(json.dumps({'user_id': args.user_id, 'metrics': summarize(frame)}, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
