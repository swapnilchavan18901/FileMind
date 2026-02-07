from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from src.db import prisma
from src.utils.password import hash_password, verify_password
from src.utils.jwt import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(data: RegisterRequest) -> dict:
    try:
        existing=await prisma.user.find_unique(where={"email":data.email});
        if existing :
            raise HTTPException(status_code= 400 , detail="user with this email already exists");
        
        user = await prisma.user.create(
            data={
                "email": data.email,
                "passwordHash": hash_password(data.password),
                "name": data.name,
            }
        )
        return {"message": "User registered successfully", "user": user}

    except Exception as e:
        raise HTTPException(status_code= 500 , detail=str(e))

    

@router.post("/login")
async def login(data: LoginRequest):
    user = await prisma.user.find_unique(
        where={"email": data.email}
    )
    if not user or not verify_password(data.password, user.passwordHash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.id})

    return {"access_token": token}