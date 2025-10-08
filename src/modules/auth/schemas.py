from fastapi import Form
from typing import Optional
from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"


class ChangePasswordRequest(BaseModel):
    email: str


class ChangePassword(BaseModel):
    token: str
    password: str


class SimpleLoginForm(BaseModel):
    username: str
    password: str

    @classmethod
    def as_form(
        cls,
        username: str = Form(...),
        password: str = Form(...),
    ):
        return cls(username=username, password=password)
