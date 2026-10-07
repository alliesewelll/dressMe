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
    return {"message": "Backend is running"}


def require_user(user_id: int, db: Session):
    if db.get(models.User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")


@app.get("/users/{user_id}/style-profile", response_model=schemas.StyleProfileResponse)
def get_style_profile(user_id: int, db: Session = Depends(get_db)):
    require_user(user_id, db)
    profile = db.scalar(select(models.StyleProfile).where(models.StyleProfile.user_id == user_id))
    if profile is None:
        raise HTTPException(status_code=404, detail="Style profile not found")
    return profile


@app.patch("/users/{user_id}/style-profile", response_model=schemas.StyleProfileResponse)
def save_style_profile(user_id: int, preferences: schemas.StyleProfileSave, db: Session = Depends(get_db)):
    # Serialize saves for this user in PostgreSQL, including the first profile creation.
    user = db.scalar(select(models.User).where(models.User.user_id == user_id).with_for_update())
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    changes = preferences.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Provide at least one preference")
    profile = db.scalar(select(models.StyleProfile).where(models.StyleProfile.user_id == user_id))
    if profile is None:
        profile = models.StyleProfile(user_id=user_id)
        db.add(profile)
    for field, value in changes.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@app.post("/users/{user_id}/wardrobe", response_model=schemas.ClothingItemResponse, status_code=201)
def add_clothing_item(user_id: int, item: schemas.ClothingItemCreate, db: Session = Depends(get_db)):
    require_user(user_id, db)
    clothing_item = models.ClothingItem(user_id=user_id, **item.model_dump())
    db.add(clothing_item)
    db.commit()
    db.refresh(clothing_item)
    return clothing_item


@app.patch("/users/{user_id}/wardrobe/{item_id}", response_model=schemas.ClothingItemResponse)
def update_clothing_item(
    user_id: int,
    item_id: int,
    changes: schemas.ClothingItemUpdate,
    db: Session = Depends(get_db),
):
    require_user(user_id, db)
    item = db.scalar(select(models.ClothingItem).where(
        models.ClothingItem.user_id == user_id,
        models.ClothingItem.item_id == item_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Clothing item not found")
    updates = changes.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="Provide at least one clothing detail")
    for field, value in updates.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


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
