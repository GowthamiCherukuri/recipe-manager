from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    email: str
    password: str

class GenerateItem(BaseModel):
    title: str
    ingredients: List[str]
    steps: List[str]
    dietary_preference: Optional[str] = None

class Recipe(BaseModel):
    title: str
    ingredients: List[str]
    steps: List[str]
    dietary_preference: Optional[str] = None
    favorite: Optional[bool] = False