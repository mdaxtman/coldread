from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(title="ColdRead API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten via env var in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
