from fastapi import  APIRouter
from api.GetPostApp import myrouter

rout1 = APIRouter()
rout1.include_router(myrouter, prefix="/Coffe")
