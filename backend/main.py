from fastapi import FastAPI, Request, Depends
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker, Session  # Добавлен импорт Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI()

# Подключение к БД
DATABASE_URL = "postgresql://cinna:1104@localhost:5432/glassdb"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Получаем метаданные и подключаем таблицу customers
metadata = MetaData()
customers = Table(
    'customers',
    metadata,
    autoload_with=engine
)

# Настройка шаблонов
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR.parent / "frontend" / "templates"))

# Подключение статических файлов
static_dir = BASE_DIR.parent / "frontend" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    # Получаем всех клиентов из БД
    query = select(customers)
    result = db.execute(query)
    customers_list = result.fetchall()
    
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "customers": customers_list}
    )