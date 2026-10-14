import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core import security
from app.db import get_db
from app.models import User
from app.schemas import RefreshIn, SignupIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


def _tokens(u: User) -> TokenOut:
    return TokenOut(access_token=security.access_token(u.id), refresh_token=security.refresh_token(u.id))


@router.post("/signup", response_model=UserOut, status_code=201)
@limiter.limit("10/minute")
def signup(request: Request, body: SignupIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(409, "Email already registered")
    u = User(name=body.name, email=body.email.lower(), hashed_password=security.hash_password(body.password), role=body.role)
    db.add(u)
    db.commit()
    return u


@router.post("/login", response_model=TokenOut)
@limiter.limit("20/minute")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.email == form.username.lower()))
    if not u or not security.verify_password(form.password, u.hashed_password):
        raise HTTPException(401, "Incorrect email or password")
    return _tokens(u)


@router.post("/refresh", response_model=TokenOut)
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    try:
        uid = security.decode(body.refresh_token, "refresh")
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid refresh token")
    u = db.get(User, uid)
    if not u:
        raise HTTPException(401, "User not found")
    return _tokens(u)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.get("/reps", response_model=list[UserOut])
def reps(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.scalars(select(User).order_by(User.name)).all()
