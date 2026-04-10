from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from auth.jwt import decode_access_token

import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(models.User).filter(models.User.username == str(username)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

def get_admin_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if current_user.is_admin is not True:
        raise HTTPException(status_code=403, detail="Admins only")
    
    return current_user