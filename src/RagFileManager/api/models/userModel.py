from pydantic import BaseModel

class userModel(BaseModel):
    username: str 
    user_id: str