import os
from typing import Any, Dict

# Optional import of PyJWT. If not installed, jwt will be None and usage will raise a clear error.
try:
    import jwt  # PyJWT  # type: ignore
except Exception:
    jwt = None

JWT_ALG = "HS256"
JWT_SECRET = os.environ.get("JWT_SECRET", "default-secret")


def sign_token(payload: dict, algorithm: str = JWT_ALG, secret: str | None = None) -> str:
    if jwt is None:
        raise RuntimeError("PyJWT is not installed. Please install PyJWT to sign tokens.")
    if secret is None:
        secret = JWT_SECRET
    token = jwt.encode(payload, secret, algorithm=algorithm)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def verify_token(token: str, secret: str | None = None) -> Dict[str, Any]:
    if jwt is None:
        raise RuntimeError("PyJWT is not installed. Please install PyJWT to verify tokens.")
    if secret is None:
        secret = JWT_SECRET
    try:
        data = jwt.decode(token, secret, algorithms=[JWT_ALG], options={"verify_exp": False})
        return data
    except Exception as e:
        # Re-raise to let caller handle (e.g., unauthorized responses)
        raise e


