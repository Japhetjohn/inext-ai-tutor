
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from models.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def landing_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("landing/landing.html", {"request": request})

@router.get("/about")
async def about_page(request: Request):
    return templates.TemplateResponse("landing/about.html", {"request": request})
