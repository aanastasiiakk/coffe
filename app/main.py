import uvicorn
from fastapi import FastAPI
from core.app_lifecycle import lifespan

app = FastAPI(lifespan=lifespan)
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
    #добавить routes