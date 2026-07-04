from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config import get_cors_origins

app = FastAPI(title="ColdRead API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),  # explicit origins via CORS_ORIGINS env; never "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
