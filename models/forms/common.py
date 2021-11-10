from pydantic import BaseModel

class ErrorResponseForm(BaseModel):
    error: int
    detail: str
