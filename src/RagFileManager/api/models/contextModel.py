from datetime import datetime
from pydantic import BaseModel



class contextModel(BaseModel):
    id: int
    value: str
    vector_embedding: list[float]
    created_at: datetime
    length: int
    used_count: int
    user_id: int # 
    source_id: int # file_id