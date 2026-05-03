from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str


class StatusResponse(BaseModel):
    status: str
    message: str
