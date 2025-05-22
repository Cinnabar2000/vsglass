from typing import Dict, List, Tuple
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from backend.database import Detail, GlassType, Remnant

class GlassCutter:
    def __init__(self, db_session: Session):
        self.db = db_session
        self._setup_fuzzy_system()
    
    def _setup_fuzzy_system(self):
        """Инициализация системы нечеткой логики"""
        # Антецеденты (входные переменные)
        self.size_fit = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'size_fit')
        self.material_loss = ctrl.Antecedent(np.arange(0, 1.1, 0.1), 'material_loss')
        self.quality = ctrl.Antecedent(np.arange(0, 11, 1), 'quality')
        
        # Консеквент (выходная переменная)
        self.suitability = ctrl.Consequent(np.arange(0, 1.1, 0.1), 'suitability')
        
        # Функции принадлежности
        self.size_fit.automf(3, names=['small', 'medium', 'large'])
        self.material_loss.automf(3, names=['low', 'medium', 'high'])
        self.quality.automf(3, names=['poor', 'average', 'good'])
        self.suitability.automf(3, names=['reject', 'consider', 'accept'])
        
        # Правила нечеткой логики
        rules = [
            ctrl.Rule(self.size_fit['large'] & self.material_loss['low'] & self.quality['good'], 
                     self.suitability['accept']),
            ctrl.Rule(self.size_fit['medium'] & self.material_loss['medium'] & self.quality['average'], 
                     self.suitability['consider']),
            ctrl.Rule(self.size_fit['small'] | self.material_loss['high'] | self.quality['poor'], 
                     self.suitability['reject'])
        ]
        
        self.decision_system = ctrl.ControlSystem(rules)
        self.suitability_calc = ctrl.ControlSystemSimulation(self.decision_system)

    def _calculate_suitability(self, remnant: Remnant, detail: Detail) -> float:
        """Вычисляет пригодность остатка для детали"""
        # Проверка возможности гильотинного реза
        fits_normal = (detail.width <= remnant.width and detail.height <= remnant.height)
        fits_rotated = (detail.height <= remnant.width and detail.width <= remnant.height)
        
        if not (fits_normal or fits_rotated):
            return 0.0
        
        # Вычисляем степень соответствия размеров
        if fits_normal:
            size_fit = min(remnant.width / detail.width, remnant.height / detail.height)
        else:
            size_fit = min(remnant.width / detail.height, remnant.height / detail.width)
        
        # Вычисляем потери материала
        loss = (remnant.width * remnant.height - detail.width * detail.height) / (remnant.width * remnant.height)
        
        # Нормализуем входные данные
        self.suitability_calc.input['size_fit'] = min(max(size_fit, 0), 1)
        self.suitability_calc.input['material_loss'] = min(max(loss, 0), 1)
        self.suitability_calc.input['quality'] = min(max(remnant.quality, 0), 10)
        
        # Выполняем расчет
        self.suitability_calc.compute()
        
        return float(self.suitability_calc.output['suitability'])

    def optimize_cutting(self, glass_type_id: int) -> Dict:
        """Основная функция оптимизации раскроя"""
        # Получаем данные из БД
        glass_type = self._get_glass_type(glass_type_id)
        if not glass_type:
            return {"error": "Тип стекла не найден", "status": "error"}

        details = self._get_uncut_details(glass_type_id)
        remnants = self._get_available_remnants(glass_type_id)

        cutting_plan = []
        used_remnants = set()
        unplaced_details = []

        # 1. Размещение на остатках
        self._place_on_remnants(details, remnants, cutting_plan, used_remnants, unplaced_details)

        # 2. Раскрой на новых листах
        sheet_width = 2000  # мм
        sheet_height = int(glass_type.type_height * 1000)  # м → мм
        sheet_plans = self._cut_new_sheets(unplaced_details, sheet_width, sheet_height)
        cutting_plan.extend(sheet_plans)

        # 3. Расчет статистики
        stats = self._calculate_statistics(cutting_plan, sheet_width, sheet_height, len(details))
        
        return {
            "sheet_width": sheet_width,
            "sheet_height": sheet_height,
            "cutting_plans": cutting_plan,
            "status": "success",
            **stats
        }

    def _get_glass_type(self, glass_type_id: int) -> GlassType:
        """Получает тип стекла из БД"""
        return self.db.query(GlassType).filter(
            GlassType.type_id == glass_type_id
        ).first()

    def _get_uncut_details(self, glass_type_id: int) -> List[Detail]:
        """Получает нераскроенные детали"""
        return self.db.query(Detail).filter(
            and_(
                Detail.glass_type_id == glass_type_id,
                Detail.is_completed == False
            )
        ).order_by(desc(Detail.height), desc(Detail.width)).all()

    def _get_available_remnants(self, glass_type_id: int) -> List[Remnant]:
        """Получает доступные остатки"""
        return self.db.query(Remnant).filter(
            Remnant.glass_type_id == glass_type_id
        ).order_by(desc(Remnant.width * Remnant.height)).all()

    def _place_on_remnants(self, details: List[Detail], remnants: List[Remnant],
                         cutting_plan: List[Dict], used_remnants: set, unplaced_details: List[Detail]):
        """Размещает детали на подходящих остатках"""
        for detail in details:
            best_remnant = None
            best_score = 0.0
            best_rotated = False
            
            for remnant in remnants:
                if remnant.remnant_id in used_remnants:
                    continue
                
                # Проверяем размещение без поворота
                if remnant.width >= detail.width and remnant.height >= detail.height:
                    score = self._calculate_suitability(remnant, detail)
                    if score > best_score:
                        best_score = score
                        best_remnant = remnant
                        best_rotated = False
                
                # Проверяем размещение с поворотом на 90°
                if remnant.width >= detail.height and remnant.height >= detail.width:
                    rotated_score = self._calculate_suitability(remnant, detail)
                    if rotated_score > best_score:
                        best_score = rotated_score
                        best_remnant = remnant
                        best_rotated = True
            
            if best_remnant and best_score > 0.7:
                width = detail.height if best_rotated else detail.width
                height = detail.width if best_rotated else detail.height
                
                cutting_plan.append({
                    "detail_id": detail.detail_id,
                    "width": float(detail.width),
                    "height": float(detail.height),
                    "position_x": 0,
                    "position_y": 0,
                    "is_remnant": True,
                    "remnant_id": best_remnant.remnant_id,
                    "score": best_score,
                    "rotated": best_rotated
                })
                used_remnants.add(best_remnant.remnant_id)
            else:
                unplaced_details.append(detail)

    def _cut_new_sheets(self, details: List[Detail], sheet_width: int, sheet_height: int) -> List[Dict]:
        """Раскрой на новых листах с гильотинным резом"""
        plans = []
        details = sorted(details, key=lambda d: max(d.width, d.height), reverse=True)
        
        while details:
            sheet = {
                'remaining_rects': [(0, 0, sheet_width, sheet_height)],
                'cuts': []
            }
            
            self._fill_sheet(sheet, details, plans)
        
        return plans

    def _fill_sheet(self, sheet: Dict, details: List[Detail], plans: List[Dict]):
        """Заполняет один лист деталями"""
        i = 0
        while i < len(details):
            detail = details[i]
            placed = False
            
            # Пробуем разместить деталь в каждом доступном прямоугольнике
            for rect_idx, rect in enumerate(sheet['remaining_rects'][:]):
                x, y, rect_w, rect_h = rect
                
                # Без поворота
                if detail.width <= rect_w and detail.height <= rect_h:
                    self._place_detail(details, plans, i, sheet, rect_idx, 
                                      x, y, detail.width, detail.height, False)
                    placed = True
                    break
                
                # С поворотом на 90°
                if detail.height <= rect_w and detail.width <= rect_h:
                    self._place_detail(details, plans, i, sheet, rect_idx, 
                                      x, y, detail.height, detail.width, True)
                    placed = True
                    break
            
            if not placed:
                i += 1

    def _place_detail(self, details: List[Detail], plans: List[Dict], detail_idx: int,
                    sheet: Dict, rect_idx: int, x: int, y: int, 
                    width: int, height: int, rotated: bool):
        """Размещает деталь на листе и обновляет оставшиеся прямоугольники"""
        detail = details[detail_idx]
        
        # Добавляем в план раскроя
        plans.append({
            "detail_id": detail.detail_id,
            "width": float(detail.width),
            "height": float(detail.height),
            "position_x": x,
            "position_y": y,
            "is_remnant": False,
            "score": 1.0,
            "rotated": rotated,
            "sheet_cuts": sheet['cuts'].copy()
        })
        
        # Удаляем размещенную деталь
        details.pop(detail_idx)
        
        # Получаем исходный прямоугольник
        rect = sheet['remaining_rects'].pop(rect_idx)
        x, y, rect_w, rect_h = rect
        
        # Определяем тип разреза (вертикальный или горизонтальный)
        if width == rect_w:  # Горизонтальный разрез
            new_rect = (x, y + height, rect_w, rect_h - height)
            cut_type = 'horizontal'
            cut_pos = y + height
        else:  # Вертикальный разрез
            new_rect = (x + width, y, rect_w - width, rect_h)
            cut_type = 'vertical'
            cut_pos = x + width
        
        # Добавляем разрез
        sheet['cuts'].append((cut_type, cut_pos))
        
        # Добавляем новый прямоугольник, если он не нулевой
        if new_rect[2] > 0 and new_rect[3] > 0:
            sheet['remaining_rects'].append(new_rect)
        
        # Сортируем прямоугольники для оптимального размещения
        sheet['remaining_rects'].sort()

    def _calculate_statistics(self, plans: List[Dict], sheet_width: int, 
                            sheet_height: int, total_details: int) -> Dict:
        """Вычисляет статистику раскроя"""
        placed_on_remnants = sum(1 for p in plans if p.get('is_remnant'))
        placed_on_sheets = len(plans) - placed_on_remnants
        
        total_area = sheet_width * sheet_height * max(1, placed_on_sheets)
        used_area = sum(p['width'] * p['height'] for p in plans)
        utilization = round((used_area / total_area) * 100, 2) if total_area > 0 else 0
        
        return {
            "utilization": utilization,
            "total_details": total_details,
            "placed_details": len(plans),
            "unplaced_details": total_details - len(plans),
            "placed_on_remnants": placed_on_remnants,
            "placed_on_sheets": placed_on_sheets,
            "sheets_used": max(1, placed_on_sheets)  # Минимум 1 лист
        }
