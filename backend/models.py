from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
	pass


class User(Base):
	__tablename__ = "users"

	user_id: Mapped[int] = mapped_column(primary_key=True)
	username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
	email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
	password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())

	style_profile: Mapped["StyleProfile"] = relationship(
		back_populates="user", uselist=False, cascade="all, delete-orphan"
	)
	clothing_items: Mapped[list["ClothingItem"]] = relationship(
		back_populates="user", cascade="all, delete-orphan"
	)
	recommendations: Mapped[list["Recommendation"]] = relationship(
		back_populates="user", cascade="all, delete-orphan"
	)
	feedback: Mapped[list["Feedback"]] = relationship(
		back_populates="user", cascade="all, delete-orphan"
	)


class StyleProfile(Base):
	__tablename__ = "style_profiles"

	profile_id: Mapped[int] = mapped_column(primary_key=True)
	user_id: Mapped[int] = mapped_column(
		ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False
	)
	color_season: Mapped[str | None] = mapped_column(String(50))
	body_type: Mapped[str | None] = mapped_column(String(50))
	undertone: Mapped[str | None] = mapped_column(String(50))
	preferred_styles: Mapped[str | None] = mapped_column(Text)
	created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())

	user: Mapped[User] = relationship(back_populates="style_profile")


class ClothingItem(Base):
	__tablename__ = "clothing_items"

	item_id: Mapped[int] = mapped_column(primary_key=True)
	user_id: Mapped[int] = mapped_column(
		ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
	)
	item_name: Mapped[str] = mapped_column(String(100), nullable=False)
	category: Mapped[str | None] = mapped_column(String(50))
	subcategory: Mapped[str | None] = mapped_column(String(50))
	brand: Mapped[str | None] = mapped_column(String(100))
	primary_color: Mapped[str | None] = mapped_column(String(50))
	pattern: Mapped[str | None] = mapped_column(String(50))
	material: Mapped[str | None] = mapped_column(String(100))
	item_size: Mapped[str | None] = mapped_column(String(20))
	purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
	times_worn: Mapped[int] = mapped_column(default=0, nullable=False)
	purchase_date: Mapped[date | None] = mapped_column(Date)
	image_url: Mapped[str | None] = mapped_column(Text)
	created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())

	user: Mapped[User] = relationship(back_populates="clothing_items")
	recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="item")


class Recommendation(Base):
	__tablename__ = "recommendations"
	__table_args__ = (
		CheckConstraint("recommendation IN ('BUY', 'MAYBE', 'SKIP')"),
	)

	recommendation_id: Mapped[int] = mapped_column(primary_key=True)
	user_id: Mapped[int] = mapped_column(
		ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
	)
	item_id: Mapped[int] = mapped_column(
		ForeignKey("clothing_items.item_id", ondelete="SET NULL"), nullable=False
	)
	recommendation: Mapped[str] = mapped_column(String(255), nullable=False)
	confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
	color_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
	body_type_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
	preference_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
	recommendation_reason: Mapped[str | None] = mapped_column(Text)
	created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())

	user: Mapped[User] = relationship(back_populates="recommendations")
	item: Mapped[ClothingItem] = relationship(back_populates="recommendations")
	feedback: Mapped[list["Feedback"]] = relationship(
		back_populates="recommendation", cascade="all, delete-orphan"
	)


class Feedback(Base):
	__tablename__ = "feedback"
	__table_args__ = (
		CheckConstraint("rating BETWEEN 1 AND 5"),
		CheckConstraint("feedback IN ('LIKE', 'DISLIKE', 'NEUTRAL')"),
	)

	feedback_id: Mapped[int] = mapped_column(primary_key=True)
	user_id: Mapped[int] = mapped_column(
		ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
	)
	recommendation_id: Mapped[int] = mapped_column(
		ForeignKey("recommendations.recommendation_id", ondelete="CASCADE"), nullable=False
	)
	purchased: Mapped[bool | None] = mapped_column(Boolean)
	rating: Mapped[int | None] = mapped_column()
	times_worn: Mapped[int] = mapped_column(default=0, nullable=False)
	feedback: Mapped[str] = mapped_column(String(255), nullable=False)
	comments: Mapped[str | None] = mapped_column(Text)
	created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp())

	user: Mapped[User] = relationship(back_populates="feedback")
	recommendation: Mapped[Recommendation] = relationship(back_populates="feedback")