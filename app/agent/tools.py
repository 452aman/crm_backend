from langchain_core.tools import tool
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from datetime import date

def get_db():
    return SessionLocal()

@tool
def log_interaction(hcp_name: str, location: str, interaction_type: str, products_discussed: str, notes: str, rep_id: int) -> str:
    """Log a new interaction with a doctor. Use when user wants to record a visit, call or meeting."""
    db = get_db()
    try:
        hcp = db.query(models.HCP).filter(models.HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            return f"Doctor '{hcp_name}' not found. Please add the doctor first."
        new_interaction = models.Interaction(
            rep_id=rep_id,
            hcp_id=hcp.id,
            date=date.today(),
            location=location,
            interaction_type=interaction_type,
            products_discussed=products_discussed,
            notes=notes
        )
        db.add(new_interaction)
        db.commit()
        db.refresh(new_interaction)
        return f"Interaction with Dr. {hcp.name} logged successfully. Interaction ID: {new_interaction.id}"
    finally:
        db.close()

@tool
def edit_interaction(interaction_id: int, notes: str, products_discussed: str, rep_id: int) -> str:
    """Use when user wants to update or modify an existing interaction."""
    db = get_db()
    try:
        interaction = db.query(models.Interaction).filter(
            models.Interaction.id == interaction_id,
            models.Interaction.rep_id == rep_id
        ).first()
        if not interaction:
            return f"Interaction {interaction_id} not found."
        interaction.notes = notes
        interaction.products_discussed = products_discussed
        db.commit()
        return f"Interaction {interaction_id} updated successfully."
    finally:
        db.close()

@tool
def get_hcp_history(hcp_name: str, rep_id: int) -> str:
    """Get all past interactions with a specific doctor. Use when user asks about history with a particular doctor."""
    db = get_db()
    try:
        hcp = db.query(models.HCP).filter(models.HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            return f"Doctor '{hcp_name}' not found."
        interactions = db.query(models.Interaction).filter(
            models.Interaction.hcp_id == hcp.id,
            models.Interaction.rep_id == rep_id
        ).all()
        if not interactions:
            return f"No interactions found with Dr. {hcp.name}."
        result = f"Interactions with Dr. {hcp.name}:\n"
        for i in interactions:
            result += f"- ID {i.id} | {i.date} | {i.interaction_type} | {i.location} | Notes: {i.notes}\n"
        return result
    finally:
        db.close()


@tool
def summarize_interaction(interaction_id: int, rep_id: int) -> str:
    """Summarize an interaction. Use when user wants a summary of a specific interaction."""
    db = get_db()
    try:
        interaction = db.query(models.Interaction).filter(
            models.Interaction.id == interaction_id,
            models.Interaction.rep_id == rep_id
        ).first()
        if not interaction:
            return f"Interaction {interaction_id} not found."
        summary = (
            f"On {interaction.date}, met HCP at {interaction.location} "
            f"via {interaction.interaction_type}. "
            f"Discussed: {interaction.products_discussed}. "
            f"Notes: {interaction.notes}"
        )
        interaction.summary = summary
        db.commit()
        return summary
    finally:
        db.close()

@tool
def get_all_interactions(rep_id: int) -> str:
    """Get all interactions logged by the current rep. Use when user wants to see all their interactions."""
    db = get_db()
    try:
        interactions = db.query(models.Interaction).filter(
            models.Interaction.rep_id == rep_id
        ).all()
        if not interactions:
            return "No interactions found."
        result = "Your interactions:\n"
        for i in interactions:
            hcp = db.query(models.HCP).filter(models.HCP.id == i.hcp_id).first()
            hcp_name = hcp.name if hcp else "Unknown"
            result += f"- ID {i.id} | {hcp_name} | {i.date} | {i.interaction_type} | {i.location}\n"
        return result
    finally:
        db.close()

