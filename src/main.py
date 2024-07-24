from fastapi import FastAPI

from src.controllers.db import Base, engine
from src.routers.availabilities import router as router_availabilities
from src.routers.reservations import router as router_reservations
from src.routers.users import router as router_user

Base.metadata.create_all(bind=engine)

app = FastAPI(title="padel-api")

app.include_router(router_user)
app.include_router(router_availabilities)
app.include_router(router_reservations)


@app.get("/")
async def home():
    return {"hello": "world"}
