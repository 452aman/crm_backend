"""Shared domain operations used by both the REST API and the AI assistant (one code path, one set of rules)."""
import difflib
import re
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HCP, FollowUp, Interaction, InteractionType, Product, Role, Sentiment, User


def _clean(name: str) -> str:
    return re.sub(r"\b(dr|doctor|prof)\.?\s+", "", name.lower()).strip()


def find_hcps(db: Session, name: str, limit: int = 3) -> list[HCP]:
    """Fuzzy-match a doctor by name ('Dr. Sharma', 'priya sharma', 'Sharma')."""
    target = _clean(name)
    if not target:
        return []
    hcps = db.scalars(select(HCP)).all()
    scored = []
    for h in hcps:
        full = _clean(h.name)
        if target == full:
            score = 1.0
        elif target in full or any(target == part for part in full.split()):
            score = 0.9
        else:
            score = difflib.SequenceMatcher(None, target, full).ratio()
        scored.append((score, h))
    scored = sorted((x for x in scored if x[0] >= 0.6), key=lambda x: -x[0])
    return [h for _, h in scored[:limit]]


def resolve_products(db: Session, names: list[str]) -> list[Product]:
    catalog = db.scalars(select(Product)).all()
    out: dict[int, Product] = {}
    for n in names:
        n = n.strip().lower()
        best = max(catalog, key=lambda p: difflib.SequenceMatcher(None, n, p.name.lower()).ratio(), default=None)
        if best and (n in best.name.lower() or best.name.lower() in n or difflib.SequenceMatcher(None, n, best.name.lower()).ratio() >= 0.75):
            out[best.id] = best
    return list(out.values())


def visible_interactions(user: User):
    """Reps see only their own interactions; managers see the whole team."""
    stmt = select(Interaction)
    return stmt if user.role == Role.manager else stmt.where(Interaction.rep_id == user.id)


def create_interaction(db: Session, rep: User, *, hcp_id: int, type: InteractionType, occurred_on: date | None = None,
                       location: str = "", notes: str = "", sentiment: Sentiment = Sentiment.neutral, next_steps: str = "",
                       product_ids: list[int] | None = None, source: str = "form", follow_up_days: int | None = None) -> Interaction:
    it = Interaction(rep_id=rep.id, hcp_id=hcp_id, occurred_on=occurred_on or date.today(), type=type, location=location,
                     notes=notes, sentiment=sentiment, next_steps=next_steps, source=source)
    if product_ids:
        it.products = list(db.scalars(select(Product).where(Product.id.in_(product_ids))))
    db.add(it)
    db.flush()
    if follow_up_days:
        title = (next_steps or "Follow up")[:200]
        db.add(FollowUp(rep_id=rep.id, hcp_id=hcp_id, interaction_id=it.id, title=title, due_on=it.occurred_on + timedelta(days=follow_up_days)))
    return it


def make_summary(it: Interaction) -> str:
    prods = ", ".join(p.name for p in it.products) or "no products"
    s = f"{it.type.value.replace('_', ' ').title()} with {it.hcp.name} on {it.occurred_on:%d %b %Y} ({it.sentiment.value} sentiment). Discussed {prods}."
    if it.next_steps:
        s += f" Next: {it.next_steps}"
    return s
