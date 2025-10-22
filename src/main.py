from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.controllers.db import Base, engine
from src.rate_limiter import limiter
from src.routers.availabilities import router as router_availabilities
from src.routers.reservations import router as router_reservations
from src.routers.users import router as router_user

Base.metadata.create_all(bind=engine)

app = FastAPI(title="padel-api")

# Rate limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_user)
app.include_router(router_availabilities)
app.include_router(router_reservations)


@app.get("/")
async def home():
    return {"hello": "world"}
