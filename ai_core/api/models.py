from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class IngestResponse(BaseModel):
    status: str
    id: str

class SummarizeRequest(BaseModel):
    chat_id: int
    limit: int = 20

class SummarizeResponse(BaseModel):
    summary: str

class AskRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = None

class AskResponse(BaseModel):
    answer: str
    sources: List[str]
