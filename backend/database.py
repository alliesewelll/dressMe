from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base

## replace these with actual credentials soon
DATABASE_URL = "postgresql://username:password@localhost/dbname"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)