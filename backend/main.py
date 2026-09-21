from fastapi import FastAPI
from database import engine, Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    ## return to this and fix missage maybe?
    return {"message": "Welcome to the DressMe API!"}