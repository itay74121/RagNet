from pydantic import BaseModel
from userModel import userModel

class queryModel(BaseModel):
    query:str
    user: userModel

