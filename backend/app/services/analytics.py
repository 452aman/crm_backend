from collections import Counter, defaultdict
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import HCP, FollowUp, Interaction, Role, Sentiment, Tier, User


def _scope_rep(user: User, rep_id: int | None) -> int | None:
    """Reps are always limited to themselves; managers may narrow to one rep or see everyone."""
    return user.id if user.role == Role.rep else rep_id


def at_risk(db: Session, user: User, rep_id: int | None = None, limit: int = 12) -> list[dict]:
    """Tier A/B doctors with no contact in `at_risk_days` (or ever), most important and most overdue first."""
    scope = _scope_rep(user, rep_id)
    days = get_settings().at_risk_days
    today = date.today()
    stmt = select(HCP).where(HCP.tier.in_([Tier.A, Tier.B]))
    if scope:
        stmt = stmt.where(HCP.assigned_rep_id == scope)
    out = []
    for h in db.scalars(stmt):
        last = db.scalars(select(Interaction).where(Interaction.hcp_id == h.id).order_by(Interaction.occurred_on.desc()).limit(1)).first()
        since = (today - last.occurred_on).days if last else None
        if since is not None and since <= days:
            continue
        reason = "never contacted" if last is None else f"{since} days since last contact"
        tip = f"Prioritise a visit: Tier {h.tier.value}, {reason}."
        if last and last.sentiment == Sentiment.negative:
            tip += " Last interaction was negative, so address their concerns."
        out.append({"hcp_id": h.id, "name": h.name, "specialty": h.specialty, "hospital": h.hospital, "tier": h.tier.value,
                    "days_since": since, "last_sentiment": last.sentiment.value if last else None, "suggestion": tip})
    out.sort(key=lambda x: (x["tier"], -(x["days_since"] if x["days_since"] is not None else 10_000)))
    return out[:limit]


def overview(db: Session, user: User, days: int = 30, rep_id: int | None = None) -> dict:
    scope = _scope_rep(user, rep_id)
    since = date.today() - timedelta(days=days)
    stmt = select(Interaction).where(Interaction.occurred_on >= since)
    if scope:
        stmt = stmt.where(Interaction.rep_id == scope)
    rows = db.scalars(stmt).all()
    by_day: Counter = Counter(i.occurred_on for i in rows)
    if days <= 31:
        series = [{"label": (since + timedelta(d)).strftime("%d %b"), "count": by_day.get(since + timedelta(d), 0)} for d in range(days + 1)]
    else:  # weekly buckets keep long ranges readable
        weeks: Counter = Counter((i.occurred_on - since).days // 7 for i in rows)
        series = [{"label": (since + timedelta(w * 7)).strftime("%d %b"), "count": weeks.get(w, 0)} for w in range(days // 7 + 1)]
    products: Counter = Counter(p.name for i in rows for p in i.products)
    fu = select(FollowUp).where(FollowUp.done.is_(False))
    if scope:
        fu = fu.where(FollowUp.rep_id == scope)
    open_fu = db.scalars(fu).all()
    hcp_stmt = select(HCP).where(HCP.tier == Tier.A)
    if scope:
        hcp_stmt = hcp_stmt.where(HCP.assigned_rep_id == scope)
    tier_a = db.scalars(hcp_stmt).all()
    contacted = {i.hcp_id for i in rows}
    pos = sum(1 for i in rows if i.sentiment == Sentiment.positive)
    return {
        "days": days, "interactions": len(rows), "unique_hcps": len(contacted),
        "positive_rate": round(pos / len(rows), 3) if rows else None,
        "open_followups": len(open_fu), "overdue_followups": sum(1 for f in open_fu if f.due_on < date.today()),
        "tier_a_coverage": round(sum(1 for h in tier_a if h.id in contacted) / len(tier_a), 3) if tier_a else None,
        "by_type": dict(Counter(i.type.value for i in rows)), "by_sentiment": dict(Counter(i.sentiment.value for i in rows)),
        "series": series, "top_products": [{"name": n, "count": c} for n, c in products.most_common(6)],
    }


def team(db: Session, days: int = 30) -> list[dict]:
    since = date.today() - timedelta(days=days)
    reps = db.scalars(select(User).where(User.role == Role.rep)).all()
    rows = db.scalars(select(Interaction).where(Interaction.occurred_on >= since)).all()
    per: dict[int, list[Interaction]] = defaultdict(list)
    for i in rows:
        per[i.rep_id].append(i)
    out = []
    for r in reps:
        its = per.get(r.id, [])
        out.append({"rep_id": r.id, "name": r.name, "interactions": len(its), "unique_hcps": len({i.hcp_id for i in its}),
                    "positive_rate": round(sum(1 for i in its if i.sentiment == Sentiment.positive) / len(its), 3) if its else None,
                    "overdue_followups": len(db.scalars(select(FollowUp).where(FollowUp.rep_id == r.id, FollowUp.done.is_(False), FollowUp.due_on < date.today())).all()),
                    "at_risk_hcps": len(at_risk(db, r, limit=500))})
    return sorted(out, key=lambda x: -x["interactions"])
