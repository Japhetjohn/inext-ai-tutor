from fastapi import FastAPI, Depends, HTTPException, Request, Form, WebSocket, WebSocketDisconnect
# Import controllers
from controllers.landing_controller import router as landing_router

app = FastAPI()
app.include_router(landing_router)

# controllers/landing_controller.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def read_root():
    return {"message": "Hello, world!"}