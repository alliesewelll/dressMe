from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

import models
import schemas

from database import engine, get_db

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    ## return to this and fix missage maybe?
    return {"message": "Backend is running"}