from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import InteractionType, Role, Sentiment, Tier

T = TypeVar("T")


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int


class SignupIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.rep


class RefreshIn(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(ORM):
    id: int
    name: str
    email: EmailStr
    role: Role


class UserBrief(ORM):
    id: int
    name: str


class HCPIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    specialty: str = Field(min_length=2, max_length=80)
    hospital: str = Field(min_length=2, max_length=160)
    city: str = Field(min_length=2, max_length=80)
    tier: Tier = Tier.C
    assigned_rep_id: int | None = None


class HCPPatch(BaseModel):
    specialty: str | None = None
    hospital: str | None = None
    city: str | None = None
    tier: Tier | None = None
    assigned_rep_id: int | None = None


class HCPOut(ORM):
    id: int
    name: str
    specialty: str
    hospital: str
    city: str
    tier: Tier
    assigned_rep_id: int | None
    last_contact: date | None = None
    interaction_count: int = 0


class ProductOut(ORM):
    id: int
    name: str
    category: str


class InteractionIn(BaseModel):
    hcp_id: int
    type: InteractionType = InteractionType.visit
    occurred_on: date | None = None
    location: str = ""
    notes: str = Field(default="", max_length=4000)
    sentiment: Sentiment = Sentiment.neutral
    next_steps: str = Field(default="", max_length=1000)
    product_ids: list[int] = []
    follow_up_days: int | None = Field(default=None, ge=1, le=365)
    source: str = "form"


class InteractionPatch(BaseModel):
    type: InteractionType | None = None
    location: str | None = None
    notes: str | None = None
    sentiment: Sentiment | None = None
    next_steps: str | None = None
    product_ids: list[int] | None = None


class InteractionOut(ORM):
    id: int
    occurred_on: date
    type: InteractionType
    location: str
    notes: str
    summary: str
    sentiment: Sentiment
    next_steps: str
    source: str
    hcp: HCPOut
    rep: UserBrief
    products: list[ProductOut]
    created_at: datetime


class ParseIn(BaseModel):
    text: str = Field(min_length=10, max_length=3000)


class FollowUpIn(BaseModel):
    hcp_id: int
    title: str = Field(min_length=2, max_length=200)
    due_on: date


class FollowUpPatch(BaseModel):
    done: bool


class FollowUpOut(ORM):
    id: int
    title: str
    due_on: date
    done: bool
    hcp: HCPOut
    overdue: bool = False


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ActionOut(ORM):
    id: int
    kind: str
    payload: dict
    status: str
    result: dict
