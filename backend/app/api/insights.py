"""Analytics and the AI assistant."""
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.graph import run_agent
from app.agent.tools import ToolKit
from app.api.deps import current_user, manager_only
from app.db import SessionLocal, get_db
from app.llm import get_llm
from app.models import ChatMessage, PendingAction, User
from app.schemas import ActionOut, ChatIn
from app.services import actions, analytics

router = APIRouter(tags=["insights"])


@router.get("/analytics/overview")
def overview(days: int = Query(30, ge=7, le=180), rep_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return analytics.overview(db, user, days, rep_id)


@router.get("/analytics/at-risk")
def at_risk(rep_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return analytics.at_risk(db, user, rep_id)


@router.get("/analytics/team")
def team(days: int = Query(30, ge=7, le=180), db: Session = Depends(get_db), _: User = Depends(manager_only)):
    return analytics.team(db, days)


# ---------------------------------------------------------------- assistant
def _sse(ev: dict) -> str:
    return f"data: {json.dumps(ev)}\n\n"


@router.get("/chat/history")
def history(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(ChatMessage).where(ChatMessage.rep_id == user.id).order_by(ChatMessage.id.desc()).limit(40)).all()[::-1]
    out = []
    for m in rows:
        acts = [ActionOut.model_validate(db.get(PendingAction, i)) for i in m.actions if db.get(PendingAction, i)]
        out.append({"id": m.id, "role": m.role, "content": m.content, "trace": m.trace, "actions": [a.model_dump() for a in acts]})
    return out


@router.delete("/chat/history", status_code=204)
def clear_history(db: Session = Depends(get_db), user: User = Depends(current_user)):
    for m in db.scalars(select(ChatMessage).where(ChatMessage.rep_id == user.id)):
        db.delete(m)
    db.commit()


@router.post("/chat")
async def chat(body: ChatIn, user: User = Depends(current_user)):
    llm = get_llm()
    if not llm.available:
        raise HTTPException(503, "The assistant needs GROQ_API_KEY. The rest of the CRM works without it.")
    uid = user.id

    async def gen():
        with SessionLocal() as db:
            me = db.get(User, uid)
            past = [{"role": m.role, "content": m.content} for m in db.scalars(
                select(ChatMessage).where(ChatMessage.rep_id == uid).order_by(ChatMessage.id.desc()).limit(8)).all()[::-1]]
            db.add(ChatMessage(rep_id=uid, role="user", content=body.message))
            db.commit()
            kit = ToolKit(db, me)
            answer, trace = "", []
            async for ev in run_agent(llm, kit, me, past, body.message):
                if ev["type"] == "token":
                    answer += ev["text"]
                elif ev["type"] in ("tool_call", "tool_result"):
                    trace.append(ev)
                yield _sse(ev)
            acts = [ActionOut.model_validate(db.get(PendingAction, i)).model_dump() for i in kit.proposed]
            if acts:
                yield _sse({"type": "actions", "actions": acts})
            db.add(ChatMessage(rep_id=uid, role="assistant", content=answer or "(no answer)", trace=trace, actions=list(kit.proposed)))
            db.commit()
            yield _sse({"type": "done"})

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _action(db: Session, user: User, aid: int) -> PendingAction:
    a = db.get(PendingAction, aid)
    if not a or a.rep_id != user.id:
        raise HTTPException(404, "Action not found")
    return a


@router.post("/chat/actions/{aid}/confirm", response_model=ActionOut)
def confirm(aid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    a = _action(db, user, aid)
    try:
        actions.execute(db, user, a)
    except actions.ActionError as e:
        raise HTTPException(409, str(e))
    db.commit()
    return a


@router.post("/chat/actions/{aid}/cancel", response_model=ActionOut)
def cancel(aid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    a = _action(db, user, aid)
    if a.status != "pending":
        raise HTTPException(409, f"Action already {a.status}")
    a.status = "cancelled"
    db.commit()
    return a
