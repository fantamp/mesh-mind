from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any, Union

class IngestResponse(BaseModel):
    status: str
    id: str

class SummarizeRequest(BaseModel):
    chat_id: Union[str, int]
    limit: int = 20
    scope: str = "messages" # "messages" or "documents"
    tags: Optional[List[str]] = None
    since_datetime: Optional[str] = None  # ISO формат datetime для фильтрации сообщений
    
    @field_validator('chat_id', mode='before')
    @classmethod
    def convert_chat_id_to_str(cls, v):
        if isinstance(v, int):
            return str(v)
        return v

class SummarizeResponse(BaseModel):
    summary: str

class AskRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None

class AskResponse(BaseModel):
    answer: str
    sources: List[str]
