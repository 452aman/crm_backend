"""Execute (or cancel) a write that the assistant proposed. This is the only place the assistant's writes take effect."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import FollowUp, Interaction, InteractionType, PendingAction, Product, Sentiment, User
from app.services import crm


class ActionError(Exception):
    pass


def execute(db: Session, user: User, action: PendingAction) -> dict:
    if action.rep_id != user.id:
        raise ActionError("Not your action")
    if action.status != "pending":
        raise ActionError(f"Action already {action.status}")
    p = action.payload
    if action.kind == "log_interaction":
        it = crm.create_interaction(
            db, user, hcp_id=p["hcp_id"], type=InteractionType(p["type"]), notes=p.get("notes", ""), location=p.get("location", ""),
            sentiment=Sentiment(p.get("sentiment", "neutral")), next_steps=p.get("next_steps", ""), product_ids=p.get("product_ids"),
            source="assistant", follow_up_days=p.get("follow_up_days"))
        db.refresh(it)
        it.summary = crm.make_summary(it)
        result = {"interaction_id": it.id, "message": f"Logged interaction #{it.id} with {it.hcp.name}."}
    elif action.kind == "edit_interaction":
        it = db.get(Interaction, p["interaction_id"])
        if not it or it.rep_id != user.id:
            raise ActionError("Interaction not found")
        for field in ("notes", "next_steps"):
            if p.get(field) is not None:
                setattr(it, field, p[field])
        if p.get("sentiment"):
            it.sentiment = Sentiment(p["sentiment"])
        if p.get("product_ids") is not None:
            it.products = list(db.scalars(select(Product).where(Product.id.in_(p["product_ids"]))))
        it.summary = crm.make_summary(it)
        result = {"interaction_id": it.id, "message": f"Updated interaction #{it.id}."}
    elif action.kind == "create_followup":
        fu = FollowUp(rep_id=user.id, hcp_id=p["hcp_id"], title=p["title"], due_on=date.today() + timedelta(days=p["due_in_days"]))
        db.add(fu)
        db.flush()
        result = {"followup_id": fu.id, "message": f"Follow-up '{fu.title}' scheduled for {fu.due_on:%d %b}."}
    else:
        raise ActionError(f"Unknown action kind {action.kind}")
    action.status, action.result = "confirmed", result
    return result
