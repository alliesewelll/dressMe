from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import select
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


def require_user(user_id: int, db: Session):
    if db.get(models.User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")


@app.post("/users/{user_id}/wardrobe", response_model=schemas.ClothingItemResponse, status_code=201)
def add_clothing_item(user_id: int, item: schemas.ClothingItemCreate, db: Session = Depends(get_db)):
    require_user(user_id, db)
    clothing_item = models.ClothingItem(user_id=user_id, **item.model_dump())
    db.add(clothing_item)
    db.commit()
    db.refresh(clothing_item)
    return clothing_item


@app.get("/users/{user_id}/wardrobe", response_model=list[schemas.ClothingItemResponse])
def list_wardrobe(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    require_user(user_id, db)
    return db.scalars(
        select(models.ClothingItem)
        .where(models.ClothingItem.user_id == user_id)
        .order_by(models.ClothingItem.item_id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
