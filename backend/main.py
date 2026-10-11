from fastapi import FastAPI, Depends, HTTPException, Query, Response
from sqlalchemy import select, func, case, update
from sqlalchemy.orm import Session

import models
import schemas
from styling import suggest_items

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


@app.get("/users/{user_id}/style-suggestions", response_model=schemas.StyleSuggestions)
def get_style_suggestions(user_id: int, db: Session = Depends(get_db)):
    profile = get_style_profile(user_id, db)
    return suggest_items(profile.color_season, profile.undertone, profile.body_type)


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


@app.post("/users/{user_id}/wardrobe/{item_id}/wear", response_model=schemas.ClothingItemResponse)
def record_wear(user_id: int, item_id: int, db: Session = Depends(get_db)):
    require_user(user_id, db)
    # Increment in the database so simultaneous wear requests don't lose updates.
    item = db.scalar(
        update(models.ClothingItem)
        .where(models.ClothingItem.user_id == user_id,
               models.ClothingItem.item_id == item_id,
               func.coalesce(models.ClothingItem.times_worn, 0) < 2147483647)
        .values(times_worn=func.coalesce(models.ClothingItem.times_worn, 0) + 1)
        .returning(models.ClothingItem)
    )
    if item is None:
        existing = db.scalar(select(models.ClothingItem.item_id).where(
            models.ClothingItem.user_id == user_id,
            models.ClothingItem.item_id == item_id,
        ))
        if existing is None:
            raise HTTPException(status_code=404, detail="Clothing item not found")
        raise HTTPException(status_code=409, detail="Wear count has reached its maximum")
    db.commit()
    db.refresh(item)
    return item


@app.delete("/users/{user_id}/wardrobe/{item_id}", status_code=204, response_class=Response)
def delete_clothing_item(user_id: int, item_id: int, db: Session = Depends(get_db)):
    require_user(user_id, db)
    item = db.scalar(select(models.ClothingItem).where(
        models.ClothingItem.user_id == user_id,
        models.ClothingItem.item_id == item_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Clothing item not found")
    # The relationship clears recommendation.item_id, preserving historical feedback.
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@app.get("/users/{user_id}/wardrobe/summary", response_model=schemas.WardrobeSummary)
def get_wardrobe_summary(user_id: int, db: Session = Depends(get_db)):
    require_user(user_id, db)
    item = models.ClothingItem
    totals = db.execute(select(
        func.count(item.item_id).label("item_count"),
        func.count(item.purchase_price).label("priced_item_count"),
        func.coalesce(func.sum(item.purchase_price), 0).label("total_recorded_spend"),
        func.coalesce(func.sum(item.times_worn), 0).label("total_wears"),
        func.coalesce(func.sum(case((item.times_worn == 0, 1), else_=0)), 0).label("unworn_item_count"),
    ).where(item.user_id == user_id)).mappings().one()
    return {"user_id": user_id, **totals}


@app.get("/users/{user_id}/wardrobe", response_model=list[schemas.ClothingItemResponse])
def list_wardrobe(
    user_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=100, description="Case-insensitive text in the item name"),
    category: str | None = Query(default=None, max_length=50, description="Exact category, ignoring case"),
    color: str | None = Query(default=None, max_length=50, description="Exact primary color, ignoring case"),
    db: Session = Depends(get_db),
):
    require_user(user_id, db)
    query = select(models.ClothingItem).where(models.ClothingItem.user_id == user_id)
    if search and search.strip():
        query = query.where(models.ClothingItem.item_name.icontains(search.strip(), autoescape=True))
    for column, value in [(models.ClothingItem.category, category),
                          (models.ClothingItem.primary_color, color)]:
        if value and value.strip():
            query = query.where(func.lower(column) == value.strip().lower())
    return db.scalars(
        query
        .order_by(models.ClothingItem.item_id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
