from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

SECRET_KEY = "fed0a7111d1f8296b47126104736bcc671dd670d11e75a2d67ecdefbcda7c3c4"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(SQLModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserData(User, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str

class UserInDB(UserData):
    hashed_password: str

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

pwd_context = CryptContext(schemes=["bcrypt"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    with Session(engine) as session:
        statement = select(UserData).where(UserData.username == username)
        results = session.exec(statement)
        if len(results) != 1:
            return None
        else:
            return UserInDB(results.first())

# to authenticate a user, they must have an entry in user database, and a valid password    
def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# if login details are valid, the website needs to return an access token, and specify the expiration time
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # decode jwt token
        username = payload.get("sub")
        if username is None:
            raise credentials_exception # if no username found in token
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception # if token itself is invalid
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception # if user isn't in database
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = authenticate_user(form_data.username, form_data.password) # check if valid user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer") # create access token if valid user


@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user

@app.get("/users/me/items/")
async def read_user_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]

@app.post("/register")
async def sign_up_user(
    username: str, password: str, email: str, full_name: str
):
    with Session(engine) as session:
        user_entry = UserData(username=username, email=email, full_name=full_name, disabled=False, hashed_password=get_password_hash(password))
        session.add(user_entry)
        session.commit()