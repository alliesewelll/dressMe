from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import date, datetime
from decimal import Decimal

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    
class UserResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class ClothingItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    item_name: str = Field(min_length=1, max_length=100)
    category: str | None = Field(default=None, max_length=50)
    subcategory: str | None = Field(default=None, max_length=50)
    brand: str | None = Field(default=None, max_length=100)
    primary_color: str | None = Field(default=None, max_length=50)
    pattern: str | None = Field(default=None, max_length=50)
    material: str | None = Field(default=None, max_length=100)
    item_size: str | None = Field(default=None, max_length=20)
    purchase_price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    times_worn: int = Field(default=0, ge=0, le=2147483647)
    purchase_date: date | None = None
    image_url: str | None = None


class ClothingItemResponse(ClothingItemCreate):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    user_id: int
    created_at: datetime
