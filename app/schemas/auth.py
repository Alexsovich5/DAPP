from pydantic import BaseModel, EmailStr
from typing import Optional, List


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: "User"


class TokenData(BaseModel):
    email: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    dietary_preferences: Optional[List[str]] = None
    cuisine_preferences: Optional[List[str]] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    looking_for: Optional[str] = None


class User(UserBase):
    id: int
    is_active: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    is_profile_complete: bool = False
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    dietary_preferences: Optional[List[str]] = None
    location: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None
    dietary_preferences: Optional[List[str]] = None
