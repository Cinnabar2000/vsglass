from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db, Detail, GlassType
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="frontend/templates")

@router.get("/cutting", response_class=HTMLResponse)
async def cutting_page(request: Request, db: Session = Depends(get_db)):
    glass_types = db.query(GlassType).all()
    return templates.TemplateResponse("cutting.html", {
        "request": request,
        "glass_types": glass_types
    })

@router.get("/details")
def get_details(glass_type_id: int, db: Session = Depends(get_db)):
    # Проверяем существование типа стекла
    if not db.query(GlassType).filter_by(type_id=glass_type_id).first():
        raise HTTPException(404, detail="Тип стекла не найден")
    
    # Получаем детали
    details = db.query(Detail).filter(
        Detail.glass_type_id == glass_type_id,
        Detail.is_completed == False
    ).all()
    
    return [
        {
            "detail_id": d.detail_id,
            "width": float(d.width),
            "height": float(d.height)
        }
        for d in details
    ]

@router.get("/details/{glass_type_id}")
def optimize_cutting(glass_type_id: int, db: Session = Depends(get_db)):
    print(f"Оптимизация раскроя для glass_type_id={glass_type_id}")
    return {"message": f"Cutting plan for glass_type_id={glass_type_id}"}
