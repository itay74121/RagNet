import fastapi
from .authRoute import authRouter
try:
    from .contextRoute import contextRouter
except Exception:
    contextRouter = None

router = fastapi.APIRouter()


router.include_router(authRouter, prefix="/api/v1/auth", tags=["auth"])
if contextRouter is not None:
    router.include_router(contextRouter, prefix="/api/v1/context", tags=["context"])
