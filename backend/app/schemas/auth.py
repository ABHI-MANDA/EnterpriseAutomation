"""Authentication and User Schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class LoginRequest(BaseModel):
    email: str = Field(..., max_length=200)
    password: str = Field(..., max_length=200)
    otp: Optional[str] = ""

class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    department: str
    region: str
    branch: Optional[str] = ""
    expertise: Optional[str] = ""

class LoginResponse(BaseModel):
    token: str
    user: UserOut

class MFAEnrollResponse(BaseModel):
    secret: str
