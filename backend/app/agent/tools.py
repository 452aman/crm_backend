"""Assistant tools. Built per request around the authenticated user, so a rep can never act as someone else.

Read tools run immediately. Write tools only *propose*: they store a PendingAction and the rep confirms it in the UI.
"""
from datetime import date, timedelta

from langchain_core.tools import StructuredTool
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import FollowUp, Interaction, InteractionType, PendingAction, Sentiment, User
from app.services import analytics, crm


class ToolKit:
    def __init__(self, db: Session, user: User) -> None:
        self.db, self.user = db, user
        self.proposed: list[int] = []   # PendingAction ids created during this turn

    # ---------------------------------------------------------------- reads
    def get_hcp_history(self, hcp_name: str, limit: int = 8) -> str:
        """Past interactions with one doctor (most recent first). Use for 'what happened with Dr X'."""
        matches = crm.find_hcps(self.db, hcp_name)
        if not matches:
            return f"No doctor matching '{hcp_name}' was found."
        h = matches[0]
        rows = self.db.scalars(crm.visible_interactions(self.user).where(Interaction.hcp_id == h.id)
                               .order_by(Interaction.occurred_on.desc()).limit(limit)).all()
        if not rows:
            return f"No interactions with {h.name} ({h.hospital}) yet."
        lines = [f"- #{i.id} {i.occurred_on} {i.type.value}, {i.sentiment.value}: {i.notes[:140]}" for i in rows]
        return f"{h.name}, {h.specialty}, {h.hospital} (Tier {h.tier.value}). Recent interactions:\n" + "\n".join(lines)

    def list_my_interactions(self, days: int = 14) -> str:
        """The rep's own interactions from the last N days."""
        since = date.today() - timedelta(days=days)
        rows = self.db.scalars(select(Interaction).where(Interaction.rep_id == self.user.id, Interaction.occurred_on >= since)
                               .order_by(Interaction.occurred_on.desc()).limit(25)).all()
        if not rows:
            return f"No interactions in the last {days} days."
        return "\n".join(f"- #{i.id} {i.occurred_on} {i.hcp.name} ({i.type.value}, {i.sentiment.value})" for i in rows)

    def find_hcps_needing_visit(self, limit: int = 8) -> str:
        """Important (Tier A/B) doctors who haven't been contacted recently, with suggested next actions."""
        items = analytics.at_risk(self.db, self.user, limit=limit)
        if not items:
            return f"Everyone important has been contacted within {get_settings().at_risk_days} days."
        return "\n".join(f"- {x['name']} (Tier {x['tier']}, {x['hospital']}): {x['suggestion']}" for x in items)

    def get_followups(self) -> str:
        """Open follow-up tasks, soonest first."""
        rows = self.db.scalars(select(FollowUp).where(FollowUp.rep_id == self.user.id, FollowUp.done.is_(False))
                               .order_by(FollowUp.due_on).limit(15)).all()
        if not rows:
            return "No open follow-ups."
        return "\n".join(f"- {f.due_on}{' (OVERDUE)' if f.due_on < date.today() else ''}: {f.title} with {f.hcp.name}" for f in rows)

    def product_mentions(self, days: int = 30) -> str:
        """How often each product came up in the rep's interactions."""
        since = date.today() - timedelta(days=days)
        rows = self.db.scalars(select(Interaction).where(Interaction.rep_id == self.user.id, Interaction.occurred_on >= since)).all()
        counts: dict[str, int] = {}
        for i in rows:
            for p in i.products:
                counts[p.name] = counts.get(p.name, 0) + 1
        if not counts:
            return "No product mentions in that period."
        return "\n".join(f"- {n}: {c}" for n, c in sorted(counts.items(), key=lambda x: -x[1]))

    def summarize_interaction(self, interaction_id: int) -> str:
        """Generate and store a one-line summary of an interaction."""
        it = self.db.get(Interaction, interaction_id)
        if not it or (it.rep_id != self.user.id and self.user.role.value != "manager"):
            return f"Interaction {interaction_id} not found."
        it.summary = crm.make_summary(it)
        self.db.commit()
        return it.summary

    # --------------------------------------------------------------- writes (proposals)
    def _propose(self, kind: str, payload: dict, preview: str) -> str:
        a = PendingAction(rep_id=self.user.id, kind=kind, payload=payload)
        self.db.add(a)
        self.db.commit()
        self.proposed.append(a.id)
        return f"PROPOSED (action {a.id}, awaiting the rep's confirmation, NOT saved yet): {preview}"

    def propose_log_interaction(self, hcp_name: str, type: str = "visit", notes: str = "", products: list[str] | None = None,
                                sentiment: str = "neutral", next_steps: str = "", follow_up_days: int | None = None, location: str = "") -> str:
        """Propose logging a new interaction with a doctor. The rep must confirm before it is saved."""
        matches = crm.find_hcps(self.db, hcp_name)
        if not matches:
            return f"No doctor matching '{hcp_name}' found, so nothing was proposed. Ask the rep to check the name."
        h = matches[0]
        try:
            t, s = InteractionType(type), Sentiment(sentiment)
        except ValueError:
            return f"Invalid type or sentiment. Types: {[x.value for x in InteractionType]}; sentiments: {[x.value for x in Sentiment]}."
        prods = crm.resolve_products(self.db, products or [])
        payload = {"hcp_id": h.id, "hcp_name": h.name, "type": t.value, "notes": notes, "location": location or h.hospital,
                   "sentiment": s.value, "next_steps": next_steps, "product_ids": [p.id for p in prods],
                   "product_names": [p.name for p in prods], "follow_up_days": follow_up_days}
        return self._propose("log_interaction", payload, f"{t.value} with {h.name}, {s.value}, products {payload['product_names'] or 'none'}.")

    def propose_edit_interaction(self, interaction_id: int, notes: str | None = None, sentiment: str | None = None,
                                 next_steps: str | None = None, products: list[str] | None = None) -> str:
        """Propose changes to one of the rep's existing interactions. The rep must confirm."""
        it = self.db.get(Interaction, interaction_id)
        if not it or it.rep_id != self.user.id:
            return f"Interaction {interaction_id} not found."
        payload = {"interaction_id": it.id, "notes": notes, "sentiment": sentiment, "next_steps": next_steps,
                   "product_ids": [p.id for p in crm.resolve_products(self.db, products)] if products is not None else None}
        return self._propose("edit_interaction", payload, f"edit interaction #{it.id} with {it.hcp.name}.")

    def propose_followup(self, hcp_name: str, title: str, due_in_days: int = 7) -> str:
        """Propose a follow-up task for a doctor. The rep must confirm."""
        matches = crm.find_hcps(self.db, hcp_name)
        if not matches:
            return f"No doctor matching '{hcp_name}' found."
        h = matches[0]
        return self._propose("create_followup", {"hcp_id": h.id, "hcp_name": h.name, "title": title, "due_in_days": due_in_days},
                             f"follow-up '{title}' for {h.name} in {due_in_days} days.")

    def tools(self) -> list[StructuredTool]:
        fns = [self.get_hcp_history, self.list_my_interactions, self.find_hcps_needing_visit, self.get_followups, self.product_mentions,
               self.summarize_interaction, self.propose_log_interaction, self.propose_edit_interaction, self.propose_followup]
        return [StructuredTool.from_function(f, name=f.__name__, description=f.__doc__) for f in fns]
