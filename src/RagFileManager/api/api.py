from fastapi import FastAPI
from .routes import mainRouter
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.include_router(mainRouter)