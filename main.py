from fastapi import FastAPI
from auth import router as auth_router
from crud import router as crud_router
import models
from database import engine

app = FastAPI(title="Library App")

app.include_router(auth_router)
app.include_router(crud_router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.run_sync(models.Base.metadata.create_all)