import os
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 1440))

# tokenUrl tells Swagger UI where to send username/password to get a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """
    Hashes a password with bcrypt directly (no passlib).
    bcrypt.gensalt() creates a random salt each time, so the
    same password hashed twice produces two different hashes.
    """
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Compares a plain-text password against a stored bcrypt hash.
    bcrypt.checkpw extracts the salt from the hash itself, so
    no separate salt storage is needed.
    """
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict) -> str:
    """
    Builds a signed JWT containing the user's email (sub claim),
    user_id, and an expiry time. The signature means the token
    can't be tampered with without knowing SECRET_KEY.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def decode_token(token: str) -> dict:
    """
    Decodes a token and returns {'email': ..., 'user_id': ...},
    or raises 401 if invalid/expired/missing claims.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user_id = payload.get("user_id")
        if email is None or user_id is None:
            raise credentials_exception
        return {"email": email, "user_id": user_id}
    except JWTError:
        raise credentials_exception


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency to protect routes. Returns {'email': ..., 'user_id': ...}.
    Add `user: dict = Depends(get_current_user)` as a parameter on any
    endpoint and FastAPI will require a valid Bearer token before the
    route body even runs.
    """
    return decode_token(token)