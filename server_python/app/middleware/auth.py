import jwt
from fastapi import Header, HTTPException

from app.config.settings import ACCESS_TOKEN_SECRET
from app.utils.blacklist import blacklist


async def get_current_user(authorization: str = Header(default=None)):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail={"error": True, "success": False, "message": "Token không tồn tại"},
        )
    parts = authorization.split(" ")
    if len(parts) < 2:
        raise HTTPException(
            status_code=401,
            detail={"error": True, "success": False, "message": "Token không tồn tại"},
        )
    token = parts[1]
    if token in blacklist:
        raise HTTPException(
            status_code=401,
            detail={"error": True, "success": False, "message": "Token đã hết hạn hoặc không hợp lệ."},
        )
    try:
        decoded = jwt.decode(token, ACCESS_TOKEN_SECRET, algorithms=["HS256"])
        return decoded
    except jwt.PyJWTError as err:
        raise HTTPException(
            status_code=403,
            detail={"error": True, "success": False, "message": "Token không chính xác!"},
        ) from err
