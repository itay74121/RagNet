from pydantic import BaseModel
from .userModel import userModel

class authModel(BaseModel):
    username: str
    password: str
    user_id: userModel
