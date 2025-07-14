import uvicorn
from fastapi import FastAPI
from core.app_lifecycle import lifespan
from routers.rout import rout1


app = FastAPI(lifespan=lifespan)
app.include_router(rout1, prefix="/v1")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
    #добавить routes

