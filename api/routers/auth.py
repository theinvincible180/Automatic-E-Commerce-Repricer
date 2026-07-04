from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from api.dependencies import get_db
from api.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def limit_password_length(cls, v):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be 72 bytes or fewer.")
        return v


@router.post("/register", status_code=201)
def register(data: RegisterIn):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = %s", (data.email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered.")

    cur.execute(
        "INSERT INTO users (email, hashed_password) VALUES (%s, %s) RETURNING id",
        (data.email, hash_password(data.password))
    )
    new_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_id, "message": "User registered successfully."}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2PasswordRequestForm expects form data (not JSON) with
    'username' and 'password' fields — this is what makes the
    Swagger UI 'Authorize' button work out of the box.
    We treat 'username' as the email.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, email, hashed_password FROM users WHERE email = %s",
        (form_data.username,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    # Include both id and email in the token payload
    token = create_access_token({"sub": user["email"], "user_id": user["id"]})
    return {"access_token": token, "token_type": "bearer"}