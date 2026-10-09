from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator
from datetime import date, datetime
from decimal import Decimal

class UserCreate(BaseModel):
    """Signup input; a future signup handler must hash the password before storage."""
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=50, pattern=r"^\S+$")
    email: EmailStr = Field(max_length=100)
    password: SecretStr = Field(min_length=8, max_length=128)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    email: EmailStr
    created_at: datetime


class StyleProfileSave(BaseModel):
    """Only supplied fields change; explicit null clears a preference."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    color_season: str | None = Field(default=None, min_length=1, max_length=50)
    body_type: str | None = Field(default=None, min_length=1, max_length=50)
    undertone: str | None = Field(default=None, min_length=1, max_length=50)
    preferred_styles: str | None = Field(default=None, min_length=1, max_length=2000)


class StyleProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: int
    user_id: int
    color_season: str | None
    body_type: str | None
    undertone: str | None
    preferred_styles: str | None
    created_at: datetime


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


class ClothingItemUpdate(ClothingItemCreate):
    """Reuse creation constraints, but allow the name to be omitted."""
    item_name: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("item_name")
    @classmethod
    def name_cannot_be_cleared(cls, value):
        if value is None:
            raise ValueError("Item name cannot be null")
        return value


class WardrobeSummary(BaseModel):
    user_id: int
    item_count: int
    priced_item_count: int
    total_recorded_spend: Decimal
    total_wears: int
    unworn_item_count: int


class ClothingItemResponse(ClothingItemCreate):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    user_id: int
    created_at: datetime
