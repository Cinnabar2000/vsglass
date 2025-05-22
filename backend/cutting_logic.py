from typing import Dict, List
from math import ceil
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from backend.database import Detail, GlassType

class GlassCutter:
    def __init__(self, db_session: Session):
        self.db = db_session

    def optimize_cutting(self, glass_type_id: int) -> Dict:
        # Получаем параметры стекла
        glass_type = self.db.query(GlassType).filter(
            GlassType.type_id == glass_type_id
        ).first()
        
        if not glass_type:
            return {
                "error": "Тип стекла не найден",
                "status": "error"
            }

        sheet_width = 2000  # мм (фиксированная ширина листа)
        sheet_height = int(glass_type.type_height * 1000)  # переводим метры в мм

        # Получаем все невыполненные детали для этого типа стекла
        details = self.db.query(Detail).filter(
            and_(
                Detail.glass_type_id == glass_type_id,
                Detail.is_completed == False
            )
        ).order_by(
            desc(Detail.height),
            desc(Detail.width)
        ).all()

        if not details:
            return {
                "sheet_width": sheet_width,
                "sheet_height": sheet_height,
                "details": [],
                "utilization": 0,
                "total_details": 0,
                "placed_details": 0,
                "message": "Нет деталей для раскроя"
            }

        # Алгоритм раскроя (простейший вариант - последовательное размещение)
        cutting_plan = []
        current_x = 0
        current_y = 0
        row_height = 0
        placed_details = []

        for detail in details:
            # Проверяем, помещается ли деталь
            if current_x + detail.width > sheet_width:
                current_x = 0
                current_y += row_height
                row_height = 0

            if current_y + detail.height > sheet_height:
                continue  # Не помещается - пропускаем

            cutting_plan.append({
                "detail_id": detail.detail_id,
                "width": float(detail.width),
                "height": float(detail.height),
                "position_x": current_x,
                "position_y": current_y
            })

            current_x += detail.width
            row_height = max(row_height, detail.height)
            placed_details.append(detail.detail_id)

        # Рассчитываем процент использования
        used_area = sum(d['width'] * d['height'] for d in cutting_plan)
        total_area = sheet_width * sheet_height
        utilization = round((used_area / total_area) * 100, 2) if total_area > 0 else 0

        return {
            "sheet_width": sheet_width,
            "sheet_height": sheet_height,
            "details": cutting_plan,
            "utilization": utilization,
            "total_details": len(details),
            "placed_details": len(placed_details),
            "unplaced_details": len(details) - len(placed_details),
            "status": "success"
        }