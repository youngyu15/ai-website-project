# app/deps.py (auth dependency — mock)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)

class User:
    def __init__(self, id: str, email: str):
        self.id = id
        self.email = email

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> User:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    # TODO: verify JWT and load user from DB
    return User(id="usr_123", email="demo@example.com")