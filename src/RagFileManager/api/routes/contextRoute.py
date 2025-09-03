from fastapi import APIRouter, HTTPException, status, Depends
from fastapi import Cookie, Header
from ..controller.rag import RagQuery
from ..security import verify_token

contextRouter = APIRouter()


@contextRouter.get("/query")
def query_context(q: str, top_k: int = 5, auth_token: str = Cookie(None), authorization: str = Header(None)):
    # Require authentication via signed JWT in cookie
    if not auth_token and not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth token")
    try:
        verify_token(auth_token or authorization)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
    rag = RagQuery()
    return rag.query(q, top_k=top_k)


