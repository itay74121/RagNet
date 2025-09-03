
from ..models.userModel import userModel
from ..security import sign_token


def signAToken(user: userModel) -> str:
    payload = {
        "user_id": user.user_id,
        "username": user.username
    }
    return sign_token(payload)




