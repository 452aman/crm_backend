from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, ForeignKey
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    role = Column(String)

class HCP(Base):
    __tablename__ = "hcp"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    specialty = Column(String)
    hospital = Column(String)
    location = Column(String)

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True)
    rep_id = Column(Integer, ForeignKey("users.id"))
    hcp_id = Column(Integer, ForeignKey("hcp.id"))
    date = Column(Date, default=datetime.today)
    location = Column(String)
    interaction_type = Column(String)
    products_discussed = Column(String)
    notes = Column(String)
    summary = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

