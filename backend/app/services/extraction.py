"""Turn a rep's free-text note into a structured interaction draft (LLM, with a regex fallback)."""
import re
from datetime import date

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.llm import LLMProvider
from app.models import Interaction, InteractionType, Product, Sentiment
from app.services.crm import find_hcps, resolve_products


class Extracted(BaseModel):
    doctor_name: str | None = Field(default=None, description="Name of the healthcare professional, without 'Dr.'")
    type: InteractionType = InteractionType.visit
    location: str = ""
    products: list[str] = Field(default_factory=list, description="Product names mentioned")
    sentiment: Sentiment = Sentiment.neutral
    notes: str = Field(default="", description="Clean 1-3 sentence record of what happened")
    next_steps: str = ""
    follow_up_days: int | None = Field(default=None, description="Days until the follow-up, if one was mentioned")


SYSTEM = (
    "You extract a structured CRM record from a pharmaceutical field rep's note about a meeting with a doctor. "
    "Only use facts stated in the note; leave fields empty when unknown. Types: visit, call, email, conference, sample_drop. "
    "Sentiment is the doctor's attitude towards the rep's products: positive, neutral or negative."
)
_TYPE_WORDS = {"call": r"\b(call|phone|rang)\b", "email": r"\be-?mail", "conference": r"\bconference|webinar|symposium\b",
               "sample_drop": r"\bsamples?\b"}
_POS = r"\b(positive|keen|interested|happy|receptive|agreed|impressed|enthusiastic)\b"
_NEG = r"\b(negative|unhappy|rejected|not interested|concern|complain|objection|declined)\b"


def _fallback(text: str, product_names: list[str]) -> Extracted:
    m = re.search(r"\bDr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
    t = next((k for k, rx in _TYPE_WORDS.items() if re.search(rx, text, re.I)), "visit")
    sentiment = "negative" if re.search(_NEG, text, re.I) else "positive" if re.search(_POS, text, re.I) else "neutral"
    days = None
    fm = re.search(r"follow[- ]?up[^.]*?(\d+)\s*(day|week)", text, re.I) or re.search(r"in\s+(\d+)\s*(day|week)s?", text, re.I)
    if fm:
        days = int(fm.group(1)) * (7 if fm.group(2).lower().startswith("week") else 1)
    prods = [p for p in product_names if p.lower() in text.lower()]
    return Extracted(doctor_name=m.group(1) if m else None, type=t, products=prods, sentiment=sentiment, notes=text.strip()[:600], follow_up_days=days)


async def extract(db: Session, llm: LLMProvider, text: str) -> dict:
    names = list(db.scalars(select(Product.name)))
    used_llm = False
    if llm.available:
        try:
            ex = await llm.structured(Extracted, SYSTEM + f"\nKnown products: {', '.join(names)}.", text)
            used_llm = True
        except Exception:
            ex = _fallback(text, names)
    else:
        ex = _fallback(text, names)
    candidates = find_hcps(db, ex.doctor_name) if ex.doctor_name else []
    prods = resolve_products(db, ex.products)
    return {
        "used_llm": used_llm,
        "hcp_id": candidates[0].id if candidates else None,
        "hcp_candidates": [{"id": h.id, "name": h.name, "hospital": h.hospital} for h in candidates],
        "doctor_name": ex.doctor_name, "type": ex.type.value, "location": ex.location, "sentiment": ex.sentiment.value,
        "product_ids": [p.id for p in prods], "product_names": [p.name for p in prods], "notes": ex.notes,
        "next_steps": ex.next_steps, "follow_up_days": ex.follow_up_days, "occurred_on": date.today().isoformat(),
    }
