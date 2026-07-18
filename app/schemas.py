from pydantic import BaseModel
from datetime import date
from typing import Optional

class UserCreate(BaseModel):
    name : str
    email : str
    password : str
    role : str

class UserLogin(BaseModel):
    email : str
    password : str

class HCPCreate(BaseModel):
    name : str
    specialty : str
    hospital : str
    location : str

class InteractionCreate(BaseModel):
    hcp_id : int
    date : date
    location : str
    interaction_type : str
    products_discussed : str
    notes : str

class InteractionUpdate(BaseModel):
    hcp_id : Optional[int] = None
    date : Optional[date] = None
    location : Optional[str] = None
    interaction_type : Optional[str] = None
    products_discussed : Optional[str] = None
    notes : Optional[str] = None
    

