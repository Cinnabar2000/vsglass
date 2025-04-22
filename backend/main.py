from fastapi import FastAPI, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import os

# Инициализация приложения
app = FastAPI()

# Настройка БД
DATABASE_URL = "postgresql://cinna:1104@localhost:5432/glassdb"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Определяем базовый путь
BASE_DIR = Path(__file__).parent

# Инициализация шаблонов с правильным путем
templates = Jinja2Templates(directory=str(BASE_DIR.parent / "frontend" / "templates"))

# Подключение статических файлов
static_dir = BASE_DIR.parent / "frontend" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request):
    return templates.TemplateResponse("orders.html", {"request": request})

@app.get("/cutting", response_class=HTMLResponse)
async def cutting_page(request: Request):
    return templates.TemplateResponse("cutting.html", {"request": request})