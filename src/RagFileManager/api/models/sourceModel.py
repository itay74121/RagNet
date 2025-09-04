from datetime import datetime
from pydantic import BaseModel



class sourceModel(BaseModel):
    id: int
    name: str
    created_at: datetime
    length: int
    type: str
    user_id: int 