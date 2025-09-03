from fastapi import APIRouter, Response
from ..models.authModel import authModel
from ..controller.auth import signAToken

authRouter = APIRouter()


@authRouter.post("/login")
def login(payload: authModel, response: Response):
    # Minimal authentication flow placeholder. In real scenario verify username/password.
    user = {
        "username": payload.username,
        "user_id": payload.user_id if isinstance(payload.user_id, str) else getattr(payload.user_id, "user_id", "unknown")
    }
    # Create a token
    token = signAToken(type("User", (), user))
    # Set token as httpOnly cookie
    response.set_cookie(key="auth_token", value=token, httponly=True, secure=False)
    response.headers['authorization'] = token
    response.status_code = 201
    return response