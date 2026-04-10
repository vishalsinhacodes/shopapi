from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth.hashing import hash_password
from auth.dependencies import get_current_user
from schemas import UserCreate, UserResponse, UserUpdate

import models

router = APIRouter(prefix="/users", tags=["Users"])

# Register
@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = models.User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

# Get my profile
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# Update my profile
@router.put("/me", response_model=UserResponse)
async def update_me(
    updates: UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    if updates.username:
        setattr(current_user, "username", updates.username)
        
    if updates.email:
        setattr(current_user, "email", updates.email)
        
    db.commit()
    db.refresh(current_user)
    
    return current_user 