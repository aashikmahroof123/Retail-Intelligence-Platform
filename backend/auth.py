
import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "60")
)

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is missing from backend/.env")

ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(username: str):
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": username,
        "exp": expires_at,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Please log in first",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        username = payload.get("sub")

        if not username:
            raise HTTPException(
                status_code=401,
                detail="Invalid login token",
            )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Login token is invalid or expired",
        )

    # Check that this administrator still exists in MySQL.
    from database import get_connection

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username FROM admins WHERE username = %s",
            (username,),
        )
        admin = cursor.fetchone()
        cursor.close()
    finally:
        connection.close()

    if not admin:
        raise HTTPException(
            status_code=401,
            detail="Administrator account not found",
        )

    return admin
