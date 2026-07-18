from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from app import auth, models
from app.schemas import UserCreate, UserLogin
from app.database import get_db

router = APIRouter()

@router.post("/signup", status_code=201)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.hash_password(user.password)
    new_user = models.User(name=user.name, email=user.email, password=hashed_password, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User Created"}

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not auth.verify_password(user.password, existing_user.password):
        raise HTTPException(status_code=401, detail="Wrong Password")
    token = auth.create_access_token({"user_id": existing_user.id})
    return {"access_token": token}
