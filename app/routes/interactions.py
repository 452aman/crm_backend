from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, auth
from app.schemas import InteractionCreate, InteractionUpdate

router = APIRouter()

@router.post("/interactions", status_code=201)
def create_interaction(interaction: InteractionCreate, token: str, db: Session = Depends(get_db)):
    payload = auth.verify_token(token)
    user_id = payload.get("user_id")
    new_interaction = models.Interaction(
        rep_id=user_id,
        hcp_id=interaction.hcp_id,
        date=interaction.date,
        location=interaction.location,
        interaction_type=interaction.interaction_type,
        products_discussed=interaction.products_discussed,
        notes=interaction.notes
    )
    db.add(new_interaction)
    db.commit()
    db.refresh(new_interaction)
    return {"message": "Interaction logged successfully"}

@router.get("/interactions")
def get_interactions(token: str, db: Session = Depends(get_db)):
    payload = auth.verify_token(token)
    user_id = payload.get("user_id")
    interactions = db.query(models.Interaction).filter(models.Interaction.rep_id == user_id).all()
    return interactions

@router.get("/interactions/{id}")
def get_interaction(id: int, token: str, db: Session = Depends(get_db)):
    payload = auth.verify_token(token)
    user_id = payload.get("user_id")
    interaction = db.query(models.Interaction).filter(
        models.Interaction.id == id,
        models.Interaction.rep_id == user_id
    ).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction

@router.put("/interactions/{id}")
def update_interaction(id: int, token: str, updated: InteractionUpdate, db: Session = Depends(get_db)):
    payload = auth.verify_token(token)
    user_id = payload.get("user_id")
    interaction = db.query(models.Interaction).filter(
        models.Interaction.id == id,
        models.Interaction.rep_id == user_id
    ).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    if updated.hcp_id is not None:
        interaction.hcp_id = updated.hcp_id
    if updated.date is not None:
        interaction.date = updated.date
    if updated.location is not None:
        interaction.location = updated.location
    if updated.interaction_type is not None:
        interaction.interaction_type = updated.interaction_type
    if updated.products_discussed is not None:
        interaction.products_discussed = updated.products_discussed
    if updated.notes is not None:
        interaction.notes = updated.notes
    db.commit()
    return {"message": "Interaction updated successfully"}

@router.delete("/interactions/{id}")
def delete_interaction(id: int, token: str, db: Session = Depends(get_db)):
    payload = auth.verify_token(token)
    user_id = payload.get("user_id")
    interaction = db.query(models.Interaction).filter(
        models.Interaction.id == id,
        models.Interaction.rep_id == user_id
    ).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    db.delete(interaction)
    db.commit()
    return {"message": "Interaction deleted successfully"}
