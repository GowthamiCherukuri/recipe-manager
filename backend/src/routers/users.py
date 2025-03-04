import os
from fastapi import APIRouter, HTTPException, Depends, Request
from pymongo.collection import Collection
from passlib.context import CryptContext
from jose import JWTError, jwt
from bson import ObjectId
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from models import User

def get_users_collection(request: Request) -> Collection:
    return request.app.db["users"]

router = APIRouter()

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../.env"))

def user_helper(user) -> dict:
    return {
        "_id": str(user["_id"]),
        "email": user["email"],
    }

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)) -> str:
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username


@router.post("/register", response_model=User)
async def register_user(user: User, users: Collection = Depends(get_users_collection)):
    existing_user = await users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(user.password)
    
    user_data = user.model_dump()
    user_data["password"] = hashed_password
    result = await users.insert_one(user_data)
    created_user = await users.find_one({"_id": result.inserted_id})
    return user_helper(created_user)


@router.post("/login")
async def login_user(user: User, users: Collection = Depends(get_users_collection)):
    db_user = await users.find_one({"email": user.email})
    
    if db_user is None or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": db_user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: str = Depends(get_current_user), users: Collection = Depends(get_users_collection)):
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own account")

    result = await users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
