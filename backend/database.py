## postgreSQL connection

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd

engine = create_engine('postgresql://username:password@localhost/dbname')
Base = declarative_base()
Session = sessionmaker(bind=engine)

df = pd.read_sql(
    "SELECT * FROM recommendations",
    engine
)

print(df.head())