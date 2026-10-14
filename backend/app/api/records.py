"""HCPs, products, interactions and follow-ups."""
import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import current_user
from app.db import get_db
from app.llm import get_llm
from app.models import HCP, FollowUp, Interaction, InteractionType, Product, Role, Sentiment, Tier, User
from app.schemas import (FollowUpIn, FollowUpOut, FollowUpPatch, HCPIn, HCPOut, HCPPatch, InteractionIn, InteractionOut,
                         InteractionPatch, Page, ParseIn, ProductOut)
from app.services import crm, extraction

router = APIRouter(tags=["records"])


# ------------------------------------------------------------------ HCPs
def _hcp_stats(db: Session, user: User, ids: list[int]) -> dict[int, tuple[date | None, int]]:
    if not ids:
        return {}
    vis = crm.visible_interactions(user).subquery()
    rows = db.execute(select(vis.c.hcp_id, func.max(vis.c.occurred_on), func.count()).where(vis.c.hcp_id.in_(ids)).group_by(vis.c.hcp_id)).all()
    return {r[0]: (r[1] if isinstance(r[1], date) else date.fromisoformat(str(r[1])), r[2]) for r in rows}


def _hcp_out(h: HCP, stats: dict) -> HCPOut:
    last, n = stats.get(h.id, (None, 0))
    out = HCPOut.model_validate(h)
    out.last_contact, out.interaction_count = last, n
    return out


@router.get("/hcps", response_model=Page[HCPOut])
def list_hcps(q: str | None = None, tier: Tier | None = None, specialty: str | None = None, mine: bool = False,
              page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
              db: Session = Depends(get_db), user: User = Depends(current_user)):
    stmt = select(HCP)
    if q:
        stmt = stmt.where(or_(HCP.name.ilike(f"%{q}%"), HCP.hospital.ilike(f"%{q}%"), HCP.city.ilike(f"%{q}%")))
    if tier:
        stmt = stmt.where(HCP.tier == tier)
    if specialty:
        stmt = stmt.where(HCP.specialty == specialty)
    if mine:
        stmt = stmt.where(HCP.assigned_rep_id == user.id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(HCP.tier, HCP.name).offset((page - 1) * size).limit(size)).all()
    stats = _hcp_stats(db, user, [h.id for h in rows])
    return Page(items=[_hcp_out(h, stats) for h in rows], total=total, page=page, size=size)


@router.get("/hcps/specialties", response_model=list[str])
def specialties(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return list(db.scalars(select(HCP.specialty).distinct().order_by(HCP.specialty)))


@router.post("/hcps", response_model=HCPOut, status_code=201)
def create_hcp(body: HCPIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    h = HCP(**body.model_dump(), )
    if h.assigned_rep_id is None and user.role == Role.rep:
        h.assigned_rep_id = user.id
    db.add(h)
    db.commit()
    return _hcp_out(h, {})


@router.get("/hcps/{hcp_id}")
def hcp_detail(hcp_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    h = db.get(HCP, hcp_id)
    if not h:
        raise HTTPException(404, "HCP not found")
    its = db.scalars(crm.visible_interactions(user).where(Interaction.hcp_id == hcp_id).options(joinedload(Interaction.products), joinedload(Interaction.rep), joinedload(Interaction.hcp))
                     .order_by(Interaction.occurred_on.desc())).unique().all()
    fu = db.scalars(select(FollowUp).where(FollowUp.hcp_id == hcp_id, FollowUp.done.is_(False)).order_by(FollowUp.due_on)).all()
    sent = {s.value: sum(1 for i in its if i.sentiment == s) for s in Sentiment}
    prods: dict[str, int] = {}
    for i in its:
        for p in i.products:
            prods[p.name] = prods.get(p.name, 0) + 1
    return {"hcp": _hcp_out(h, _hcp_stats(db, user, [h.id])), "timeline": [InteractionOut.model_validate(i) for i in its],
            "sentiment": sent, "products": [{"name": k, "count": v} for k, v in sorted(prods.items(), key=lambda x: -x[1])],
            "followups": [_fu_out(f) for f in fu]}


@router.patch("/hcps/{hcp_id}", response_model=HCPOut)
def patch_hcp(hcp_id: int, body: HCPPatch, db: Session = Depends(get_db), user: User = Depends(current_user)):
    h = db.get(HCP, hcp_id)
    if not h:
        raise HTTPException(404, "HCP not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(h, k, v)
    db.commit()
    return _hcp_out(h, _hcp_stats(db, user, [h.id]))


@router.get("/products", response_model=list[ProductOut])
def products(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.scalars(select(Product).order_by(Product.name)).all()


# ----------------------------------------------------------- interactions
def _filtered(user: User, hcp_id, type, sentiment, rep_id, start, end, q):
    stmt = crm.visible_interactions(user)
    if hcp_id:
        stmt = stmt.where(Interaction.hcp_id == hcp_id)
    if type:
        stmt = stmt.where(Interaction.type == type)
    if sentiment:
        stmt = stmt.where(Interaction.sentiment == sentiment)
    if rep_id and user.role == Role.manager:
        stmt = stmt.where(Interaction.rep_id == rep_id)
    if start:
        stmt = stmt.where(Interaction.occurred_on >= start)
    if end:
        stmt = stmt.where(Interaction.occurred_on <= end)
    if q:
        stmt = stmt.where(or_(Interaction.notes.ilike(f"%{q}%"), Interaction.next_steps.ilike(f"%{q}%")))
    return stmt


_LOAD = (joinedload(Interaction.hcp), joinedload(Interaction.rep), joinedload(Interaction.products))


@router.get("/interactions", response_model=Page[InteractionOut])
def list_interactions(hcp_id: int | None = None, type: InteractionType | None = None, sentiment: Sentiment | None = None,
                      rep_id: int | None = None, start: date | None = None, end: date | None = None, q: str | None = None,
                      page: int = Query(1, ge=1), size: int = Query(15, ge=1, le=100),
                      db: Session = Depends(get_db), user: User = Depends(current_user)):
    stmt = _filtered(user, hcp_id, type, sentiment, rep_id, start, end, q)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.options(*_LOAD).order_by(Interaction.occurred_on.desc(), Interaction.id.desc())
                      .offset((page - 1) * size).limit(size)).unique().all()
    return Page(items=rows, total=total, page=page, size=size)


@router.get("/interactions/export.csv")
def export_csv(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(crm.visible_interactions(user).options(*_LOAD).order_by(Interaction.occurred_on.desc())).unique().all()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "rep", "doctor", "hospital", "type", "sentiment", "products", "notes", "next_steps"])
    for i in rows:
        w.writerow([i.occurred_on, i.rep.name, i.hcp.name, i.hcp.hospital, i.type.value, i.sentiment.value,
                    "; ".join(p.name for p in i.products), i.notes, i.next_steps])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=interactions.csv"})


@router.post("/interactions/parse")
async def parse_note(body: ParseIn, db: Session = Depends(get_db), _: User = Depends(current_user)):
    """Quick log: free text in, structured draft out. Nothing is saved; the rep reviews and confirms."""
    return await extraction.extract(db, get_llm(), body.text)


@router.post("/interactions", response_model=InteractionOut, status_code=201)
def create_interaction(body: InteractionIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not db.get(HCP, body.hcp_id):
        raise HTTPException(404, "HCP not found")
    it = crm.create_interaction(db, user, hcp_id=body.hcp_id, type=body.type, occurred_on=body.occurred_on, location=body.location,
                                notes=body.notes, sentiment=body.sentiment, next_steps=body.next_steps, product_ids=body.product_ids,
                                source=body.source, follow_up_days=body.follow_up_days)
    db.flush()
    db.refresh(it)
    it.summary = crm.make_summary(it)
    db.commit()
    return it


def _own(db: Session, user: User, iid: int) -> Interaction:
    it = db.get(Interaction, iid)
    if not it or (it.rep_id != user.id and user.role != Role.manager):
        raise HTTPException(404, "Interaction not found")
    return it


@router.get("/interactions/{iid}", response_model=InteractionOut)
def get_interaction(iid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _own(db, user, iid)


@router.patch("/interactions/{iid}", response_model=InteractionOut)
def patch_interaction(iid: int, body: InteractionPatch, db: Session = Depends(get_db), user: User = Depends(current_user)):
    it = _own(db, user, iid)
    if it.rep_id != user.id:
        raise HTTPException(403, "Only the rep who logged this can edit it")
    data = body.model_dump(exclude_unset=True)
    pids = data.pop("product_ids", None)
    for k, v in data.items():
        setattr(it, k, v)
    if pids is not None:
        it.products = list(db.scalars(select(Product).where(Product.id.in_(pids))))
    it.summary = crm.make_summary(it)
    db.commit()
    return it


@router.delete("/interactions/{iid}", status_code=204)
def delete_interaction(iid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    it = _own(db, user, iid)
    if it.rep_id != user.id:
        raise HTTPException(403, "Only the rep who logged this can delete it")
    db.delete(it)
    db.commit()


# -------------------------------------------------------------- follow-ups
def _fu_out(f: FollowUp) -> FollowUpOut:
    out = FollowUpOut.model_validate(f)
    out.overdue = (not f.done) and f.due_on < date.today()
    return out


@router.get("/followups", response_model=list[FollowUpOut])
def followups(include_done: bool = False, db: Session = Depends(get_db), user: User = Depends(current_user)):
    stmt = select(FollowUp).where(FollowUp.rep_id == user.id).options(joinedload(FollowUp.hcp))
    if not include_done:
        stmt = stmt.where(FollowUp.done.is_(False))
    return [_fu_out(f) for f in db.scalars(stmt.order_by(FollowUp.due_on)).unique()]


@router.post("/followups", response_model=FollowUpOut, status_code=201)
def create_followup(body: FollowUpIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not db.get(HCP, body.hcp_id):
        raise HTTPException(404, "HCP not found")
    f = FollowUp(rep_id=user.id, **body.model_dump())
    db.add(f)
    db.commit()
    return _fu_out(f)


@router.patch("/followups/{fid}", response_model=FollowUpOut)
def patch_followup(fid: int, body: FollowUpPatch, db: Session = Depends(get_db), user: User = Depends(current_user)):
    f = db.get(FollowUp, fid)
    if not f or f.rep_id != user.id:
        raise HTTPException(404, "Follow-up not found")
    f.done = body.done
    db.commit()
    return _fu_out(f)
