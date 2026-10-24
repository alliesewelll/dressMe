from fastapi import FastAPI, Depends, HTTPException, Query, Response, Request
from starlette.concurrency import run_in_threadpool
import ai_styling
from recommendation_context import feedback_context
from sqlalchemy import select, func, case, update
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from pathlib import Path

import models
import schemas
from styling import suggest_items

from database import engine, get_db

app = FastAPI()
app.mount("/app", StaticFiles(directory=Path(__file__).resolve().parent.parent / "frontend", html=True), name="frontend")

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"message": "Backend is running"}


def require_user(user_id: int, db: Session):
    if db.get(models.User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")


@app.get('/ai/status')
def ai_status():
    return {'configured': ai_styling.configured(), 'provider': 'OpenAI'}


@app.post('/users/{user_id}/ai-style-analysis')
async def ai_style_analysis(user_id: int, request: Request, db: Session = Depends(get_db)):
    require_user(user_id, db)
    if request.headers.get('x-photo-consent') != 'yes':
        raise HTTPException(400, 'Consent is required to send the photo and style context to OpenAI.')
    if not ai_styling.configured():
        raise HTTPException(503, 'Set OPENAI_API_KEY and STYLE_VISION_MODEL on the backend to enable AI analysis.')
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 10 * 1024 * 1024:
            raise HTTPException(413, 'Photo must be smaller than 10 MB.')
    profile = db.scalar(select(models.StyleProfile).where(models.StyleProfile.user_id == user_id))
    wardrobe = db.scalars(select(models.ClothingItem).where(models.ClothingItem.user_id == user_id)
                         .order_by(models.ClothingItem.item_id.desc()).limit(50)).all()
    context = {
        'preferences': {k: getattr(profile, k) for k in ['color_season', 'undertone', 'body_type', 'preferred_styles']} if profile else {},
        'wardrobe': [{k: getattr(item, k) for k in ['item_name', 'category', 'primary_color', 'times_worn']} for item in wardrobe],
        'feedback': feedback_context(db, user_id),
    }
    return await run_in_threadpool(ai_styling.analyze_image, bytes(raw), context)


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


@app.post('/users/{user_id}/recommendations', response_model=schemas.RecommendationResponse, status_code=201)
def save_recommendation(user_id: int, payload: schemas.RecommendationCreate, db: Session = Depends(get_db)):
    require_user(user_id, db)
    if payload.item_id is not None:
        item = db.get(models.ClothingItem, payload.item_id)
        if item is None or item.user_id != user_id:
            raise HTTPException(404, 'Clothing item not found')
    recommendation = models.Recommendation(user_id=user_id, **payload.model_dump())
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation


@app.get('/users/{user_id}/recommendations', response_model=list[schemas.RecommendationResponse])
def list_recommendations(user_id: int, limit: int = Query(50, ge=1, le=100),
                         offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    require_user(user_id, db)
    return db.scalars(select(models.Recommendation).where(models.Recommendation.user_id == user_id)
                      .order_by(models.Recommendation.recommendation_id.desc()).offset(offset).limit(limit)).all()


@app.put('/users/{user_id}/recommendations/{recommendation_id}/feedback', response_model=schemas.FeedbackResponse)
def save_feedback(user_id: int, recommendation_id: int, payload: schemas.FeedbackSave, db: Session = Depends(get_db)):
    require_user(user_id, db)
    # Lock the parent so simultaneous first submissions cannot create duplicates in PostgreSQL.
    recommendation = db.scalar(select(models.Recommendation).where(
        models.Recommendation.recommendation_id == recommendation_id,
        models.Recommendation.user_id == user_id).with_for_update())
    if recommendation is None:
        raise HTTPException(404, 'Recommendation not found')
    feedback = db.scalar(select(models.Feedback).where(
        models.Feedback.recommendation_id == recommendation_id, models.Feedback.user_id == user_id)
        .order_by(models.Feedback.feedback_id.desc()).limit(1))
    if feedback is None:
        feedback = models.Feedback(user_id=user_id, recommendation_id=recommendation_id)
        db.add(feedback)
    for key, value in payload.model_dump().items():
        setattr(feedback, key, value)
    db.commit()
    db.refresh(feedback)
    return feedback


@app.get('/users/{user_id}/recommendations/{recommendation_id}/feedback', response_model=schemas.FeedbackResponse)
def get_feedback(user_id: int, recommendation_id: int, db: Session = Depends(get_db)):
    require_user(user_id, db)
    recommendation = db.get(models.Recommendation, recommendation_id)
    if recommendation is None or recommendation.user_id != user_id:
        raise HTTPException(404, 'Recommendation not found')
    feedback = db.scalar(select(models.Feedback).where(models.Feedback.user_id == user_id,
        models.Feedback.recommendation_id == recommendation_id).order_by(models.Feedback.feedback_id.desc()).limit(1))
    if feedback is None:
        raise HTTPException(404, 'No feedback yet')
    return feedback


@app.get('/users/{user_id}/recommendation-evaluation', response_model=schemas.EvaluationResponse)
def recommendation_evaluation(user_id: int, db: Session = Depends(get_db)):
    import pandas as pd
    from evaluation import summarize
    require_user(user_id, db)
    rows = db.execute(select(
        models.Recommendation.recommendation_id, models.Recommendation.recommendation,
        models.Feedback.feedback_id, models.Feedback.feedback, models.Feedback.rating,
        models.Feedback.purchased,
    ).outerjoin(models.Feedback, (
        (models.Feedback.recommendation_id == models.Recommendation.recommendation_id)
        & (models.Feedback.user_id == models.Recommendation.user_id)
    )).where(models.Recommendation.user_id == user_id)).mappings().all()
    frame = pd.DataFrame(rows, columns=['recommendation_id', 'recommendation',
                                       'feedback_id', 'feedback', 'rating', 'purchased'])
    return {'user_id': user_id, 'metrics': summarize(frame)}


@app.get('/users/{user_id}/wardrobe-ranking', response_model=schemas.WardrobeRankingResponse)
def wardrobe_ranking(user_id: int, limit: int = Query(10, ge=1, le=50),
                     db: Session = Depends(get_db)):
    from wardrobe_ranking import rank_wardrobe
    require_user(user_id, db)
    profile = db.scalar(select(models.StyleProfile).where(models.StyleProfile.user_id == user_id))
    items = db.scalars(select(models.ClothingItem).where(models.ClothingItem.user_id == user_id)).all()
    return {'user_id': user_id, 'items': rank_wardrobe(items, profile, limit)}


@app.get('/users/{user_id}/feedback-features', response_model=schemas.FeedbackFeaturesResponse)
def feedback_features(user_id: int, db: Session = Depends(get_db)):
    from feedback_features import summarize_features
    require_user(user_id, db)
    reviews = feedback_context(db, user_id, limit=100)
    return {'user_id': user_id, 'reviewed_recommendations': len(reviews),
            'metrics': summarize_features(reviews)}
