import enum
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Integer, String, Table, Column, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    rep = "rep"
    manager = "manager"


class InteractionType(str, enum.Enum):
    visit = "visit"
    call = "call"
    email = "email"
    conference = "conference"
    sample_drop = "sample_drop"


class Sentiment(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class Tier(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.rep)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class HCP(Base):
    """A healthcare professional (doctor) that reps visit."""
    __tablename__ = "hcps"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    specialty: Mapped[str] = mapped_column(String(80), index=True)
    hospital: Mapped[str] = mapped_column(String(160))
    city: Mapped[str] = mapped_column(String(80), index=True)
    tier: Mapped[Tier] = mapped_column(Enum(Tier), default=Tier.C, index=True)
    assigned_rep_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    assigned_rep: Mapped[User | None] = relationship()


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    category: Mapped[str] = mapped_column(String(80))


interaction_products = Table(
    "interaction_products", Base.metadata,
    Column("interaction_id", ForeignKey("interactions.id", ondelete="CASCADE"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True),
)


class Interaction(Base):
    __tablename__ = "interactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    rep_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    hcp_id: Mapped[int] = mapped_column(ForeignKey("hcps.id"), index=True)
    occurred_on: Mapped[date] = mapped_column(Date, index=True)
    type: Mapped[InteractionType] = mapped_column(Enum(InteractionType))
    location: Mapped[str] = mapped_column(String(160), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    sentiment: Mapped[Sentiment] = mapped_column(Enum(Sentiment), default=Sentiment.neutral, index=True)
    next_steps: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(20), default="form")  # form | quick_log | assistant
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    rep: Mapped[User] = relationship()
    hcp: Mapped[HCP] = relationship()
    products: Mapped[list[Product]] = relationship(secondary=interaction_products)


class FollowUp(Base):
    __tablename__ = "followups"
    id: Mapped[int] = mapped_column(primary_key=True)
    rep_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    hcp_id: Mapped[int] = mapped_column(ForeignKey("hcps.id"), index=True)
    interaction_id: Mapped[int | None] = mapped_column(ForeignKey("interactions.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    due_on: Mapped[date] = mapped_column(Date, index=True)
    done: Mapped[bool] = mapped_column(default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    hcp: Mapped[HCP] = relationship()


class PendingAction(Base):
    """A write the AI assistant proposed. Nothing is saved until the rep confirms it."""
    __tablename__ = "pending_actions"
    id: Mapped[int] = mapped_column(primary_key=True)
    rep_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))     # log_interaction | edit_interaction | create_followup
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(12), default="pending", index=True)  # pending|confirmed|cancelled
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    rep_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    trace: Mapped[list] = mapped_column(JSON, default=list)       # tool calls shown in the UI
    actions: Mapped[list] = mapped_column(JSON, default=list)     # pending action ids proposed in this turn
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
