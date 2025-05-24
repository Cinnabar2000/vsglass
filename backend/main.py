from fastapi import FastAPI, Request, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, desc, func, insert, update
from sqlalchemy.orm import Session
from pathlib import Path
from math import ceil
from decimal import Decimal
from typing import List

from backend.database import get_db, orders, detail, glass_type, glass_remnants, customers, Detail, GlassType
from backend.cutting_logic import GlassCutter
from .routers import cutting  # Подключение API-маршрутов раскроя

# Инициализация приложения
app = FastAPI()
app.include_router(cutting.router)

# Настройка шаблонов и статики
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR.parent / "frontend" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR.parent / "frontend" / "static")), name="static")

# Сериализация Decimal
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/orders", response_class=HTMLResponse)
async def show_orders(request: Request, page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    per_page = 10
    offset = (page - 1) * per_page

    query = (
        select(
            orders.c.order_id,
            orders.c.order_date,
            orders.c.due_date,
            orders.c.total_amount,
            customers.c.customer_name
        )
        .select_from(orders.join(customers, orders.c.customer_id == customers.c.customer_id))
        .order_by(desc(orders.c.order_date))
        .offset(offset)
        .limit(per_page)
    )
    orders_result = db.execute(query).mappings().all()

    total_orders = db.scalar(select(func.count()).select_from(orders))

    return templates.TemplateResponse("orders.html", {
        "request": request,
        "orders": [dict(order) for order in orders_result],
        "current_page": page,
        "total_pages": ceil(total_orders / per_page) if total_orders else 1
    })


# Форма редактирования заказа
@app.get("/orders/{order_id}/edit", response_class=HTMLResponse)
async def edit_order_form(order_id: int, request: Request, db: Session = Depends(get_db)):
    order = db.execute(select(orders).where(orders.c.order_id == order_id)).mappings().first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    details = db.execute(select(detail).where(detail.c.order_id == order_id)).mappings().all()
    glass_types = db.execute(select(glass_type.c.type_id, glass_type.c.type_name)).fetchall()
    return templates.TemplateResponse("edit_order.html", {
        "request": request,
        "order": dict(order),
        "details": [dict(d) for d in details],
        "glass_types": glass_types
    })

# Форма редактирования заказа
@app.get("/orders/{order_id}/edit", response_class=HTMLResponse)
async def edit_order_form(order_id: int, request: Request, db: Session = Depends(get_db)):
    order = db.execute(select(orders).where(orders.c.order_id == order_id)).mappings().first()
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    details = db.execute(select(detail).where(detail.c.order_id == order_id)).mappings().all()
    glass_types = db.execute(select(glass_type.c.type_id, glass_type.c.type_name)).fetchall()
    customers = db.execute(select(customers.c.customer_id, customers.c.customer_name)).fetchall()  # Исправлено на customers
    
    return templates.TemplateResponse("edit_order.html", {
        "request": request,
        "order": dict(order),
        "details": [dict(d) for d in details],
        "glass_types": glass_types,
        "customers": customers
    })

# Создание нового заказа
@app.get("/orders/new", response_class=HTMLResponse)
async def new_order_form(request: Request, db: Session = Depends(get_db)):
    glass_types = db.execute(select(glass_type.c.type_id, glass_type.c.type_name)).fetchall()
    customers = db.execute(select(customers.c.customer_id, customers.c.customer_name)).fetchall()  # Исправлено на customers
    
    return templates.TemplateResponse("edit_order.html", {
        "request": request,
        "order": None,
        "details": [],
        "glass_types": glass_types,
        "customers": customers
    })

# Остальные обработчики (POST /orders/new и POST /orders/{order_id}/edit) остаются без изменений

@app.post("/orders/new")
async def create_order(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    result = db.execute(insert(orders).values(
        order_date=form["order_date"],
        due_date=form["due_date"],
        customer_id=form["customer_id"],
        total_amount=form["total_amount"]
    ).returning(orders.c.order_id))
    order_id = result.scalar()
    for k in [k.split('_')[1] for k in form if k.startswith("glass_type_")]:
        db.execute(insert(detail).values(
            order_id=order_id,
            glass_type_id=form[f"glass_type_{k}"],
            width=form[f"width_{k}"],
            height=form[f"height_{k}"],
            is_completed=f"is_completed_{k}" in form
        ))
    db.commit()
    return RedirectResponse(url="/orders", status_code=303)

# Удаление заказа
@app.post("/orders/{order_id}/delete")
async def delete_order(order_id: int, db: Session = Depends(get_db)):
    db.execute(detail.delete().where(detail.c.order_id == order_id))
    db.execute(orders.delete().where(orders.c.order_id == order_id))
    db.commit()
    return RedirectResponse(url="/orders", status_code=303)

# Остатки стекла
@app.get("/inventory", response_class=HTMLResponse)
async def show_inventory(
    request: Request,
    page: int = Query(1, ge=1),
    glass_type_id: int = Query(None),
    min_width: float = Query(None),
    min_height: float = Query(None),
    db: Session = Depends(get_db)
):
    per_page = 20
    offset = (page - 1) * per_page
    query = select(
        glass_remnants.c.remnant_id,
        glass_remnants.c.width,
        glass_remnants.c.height,
        glass_remnants.c.created_at,
        glass_type.c.type_name,
        glass_type.c.type_id
    ).select_from(
        glass_remnants.join(glass_type, glass_remnants.c.glass_type_id == glass_type.c.type_id)
    )
    if glass_type_id:
        query = query.where(glass_remnants.c.glass_type_id == glass_type_id)
    if min_width:
        query = query.where(glass_remnants.c.width >= min_width)
    if min_height:
        query = query.where(glass_remnants.c.height >= min_height)

    remnants = db.execute(query.order_by(glass_remnants.c.created_at.desc()).offset(offset).limit(per_page)).mappings().all()
    glass_types = db.execute(select(glass_type.c.type_id, glass_type.c.type_name)).fetchall()
    total_count = db.scalar(select(func.count()).select_from(query.subquery()))

    return templates.TemplateResponse("inventory.html", {
        "request": request,
        "remnants": [dict(r) for r in remnants],
        "glass_types": glass_types,
        "current_page": page,
        "total_pages": ceil(total_count / per_page) if total_count else 1,
        "current_filters": {
            "glass_type": glass_type_id,
            "min_width": min_width,
            "min_height": min_height
        }
    })

# Клиенты - список
@app.get("/customers", response_class=HTMLResponse)
async def show_customers(
    request: Request,
    page: int = Query(1, ge=1),
    search: str = Query(None),
    db: Session = Depends(get_db)
):
    per_page = 15
    offset = (page - 1) * per_page
    
    query = select(customers)
    
    if search:
        query = query.where(
            customers.c.customer_name.ilike(f"%{search}%") |
            customers.c.phone_number.ilike(f"%{search}%")
        )
    
    customers_result = db.execute(
        query.order_by(customers.c.customer_name)
        .offset(offset)
        .limit(per_page)
    ).mappings().all()
    
    total_count = db.scalar(
        select(func.count())
        .select_from(query.subquery())
    )
    
    return templates.TemplateResponse("customers.html", {
        "request": request,
        "customers": [dict(c) for c in customers_result],
        "current_page": page,
        "total_pages": ceil(total_count / per_page) if total_count else 1,
        "search_query": search
    })

# Форма создания/редактирования клиента
@app.get("/customers/new", response_class=HTMLResponse)
async def new_customer_form(request: Request):
    return templates.TemplateResponse("edit_customer.html", {
        "request": request,
        "customer": None
    })

@app.get("/customers/{customer_id}/edit", response_class=HTMLResponse)
async def edit_customer_form(customer_id: int, request: Request, db: Session = Depends(get_db)):
    customer = db.execute(
        select(customers).where(customers.c.customer_id == customer_id)
    ).mappings().first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    return templates.TemplateResponse("edit_customer.html", {
        "request": request,
        "customer": dict(customer)
    })

# Сохранение клиента
@app.post("/customers/new")
@app.post("/customers/{customer_id}/edit")
async def save_customer(
    request: Request,
    customer_id: int = None,
    db: Session = Depends(get_db)
):
    form = await request.form()
    customer_data = {
        "customer_name": form["customer_name"],
        "address": form["address"],
        "phone_number": form["phone_number"]
    }
    
    if customer_id:
        db.execute(
            update(customers)
            .where(customers.c.customer_id == customer_id)
            .values(customer_data)
        )
    else:
        db.execute(insert(customers).values(customer_data))
    
    db.commit()
    return RedirectResponse(url="/customers", status_code=303)

# Удаление клиента
@app.post("/customers/{customer_id}/delete")
async def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    # Проверка наличия заказов у клиента
    order_count = db.scalar(
        select(func.count())
        .where(orders.c.customer_id == customer_id)
    )
    
    if order_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить клиента с существующими заказами"
        )
    
    db.execute(
        delete(customers)
        .where(customers.c.customer_id == customer_id)
    )
    db.commit()
    return RedirectResponse(url="/customers", status_code=303)
