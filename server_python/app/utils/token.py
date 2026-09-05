import jwt

from app.config.settings import ACCESS_TOKEN_SECRET


async def sign_token(data: dict, expires_in: str = "7d") -> str:
    import datetime

    seconds_map = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    unit = expires_in[-1]
    amount = int(expires_in[:-1])
    delta = datetime.timedelta(seconds=amount * seconds_map.get(unit, 86400))
    payload = {**data, "exp": datetime.datetime.utcnow() + delta}
    return jwt.encode(payload, ACCESS_TOKEN_SECRET, algorithm="HS256")
