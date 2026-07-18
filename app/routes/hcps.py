from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, auth
from app.schemas import HCPCreate

router = APIRouter()

@router.post("/hcps", status_code=201)
def create_hcp(token: str, hcp: HCPCreate, db: Session = Depends(get_db)):
    auth.verify_token(token)
    new_hcp = models.HCP(name=hcp.name, specialty=hcp.specialty, hospital=hcp.hospital, location=hcp.location)
    db.add(new_hcp)
    db.commit()
    db.refresh(new_hcp)
    return {"message": "HCP added"}

@router.get("/hcps")
def get_hcps(token: str, db: Session = Depends(get_db)):
    auth.verify_token(token)
    hcps = db.query(models.HCP).all()
    return hcps

@router.get("/hcps/{id}")
def get_hcp(id: int, token: str, db: Session = Depends(get_db)):
    auth.verify_token(token)
    hcp = db.query(models.HCP).filter(models.HCP.id == id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return hcp
