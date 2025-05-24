document.addEventListener('DOMContentLoaded', function () {
    const glassTypeSelect = document.getElementById('glassTypeSelect');
    const calculateBtn = document.getElementById('calculateBtn');
    const confirmCuttingBtn = document.getElementById('confirmCuttingBtn');
    const detailsList = document.getElementById('detailsList');
    const totalDetailsSpan = document.getElementById('totalDetails');
    const cuttingResults = document.getElementById('cuttingResults');
    const cuttingDiagramContainer = document.getElementById('cuttingDiagramContainer');
    const cuttingImagesRow = document.getElementById('cuttingImagesRow');
    const cuttingStats = document.getElementById('cuttingStats');

    calculateBtn.addEventListener('click', function () {
        const glassTypeId = glassTypeSelect.value;
        calculateBtn.disabled = true;
        calculateBtn.textContent = 'Расчет...';

        fetch(`/api/cutting/calculate?glass_type_id=${glassTypeId}`)
            .then(response => {
                if (!response.ok) throw new Error('Ошибка расчета раскроя');
                return response.json();
            })
            .then(data => {
                if (data.status === 'error') {
                    throw new Error(data.error);
                }

                // Очищаем предыдущие результаты
                detailsList.innerHTML = '';
                cuttingResults.innerHTML = '';
                cuttingImagesRow.innerHTML = '';

                // Отображаем детали
                totalDetailsSpan.textContent = data.total_details;

                // Отображаем статистику
                cuttingStats.innerHTML = `
                    <div class="stat-item">
                        <span class="stat-label">Использование материала:</span>
                        <span class="stat-value ${getEfficiencyClass(data.utilization)}">
                            ${data.utilization}%
                        </span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Деталей размещено:</span>
                        <span class="stat-value">
                            ${data.placed_details} из ${data.total_details}
                        </span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Использовано листов:</span>
                        <span class="stat-value">${data.sheets_used}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">На остатках:</span>
                        <span class="stat-value">${data.placed_on_remnants}</span>
                    </div>
                `;

                // Отображаем схемы раскроя
                cuttingDiagramContainer.style.display = 'block';

                // Группируем планы раскроя по листам/остаткам
                const groupedPlans = groupCuttingPlans(data.cutting_plans);

                groupedPlans.forEach((plan, index) => {
                    const card = document.createElement('div');
                    card.className = 'col-md-6 mb-4';
                    card.innerHTML = `
                        <div class="card h-100">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <span>${plan.is_remnant ? 'Остаток' : 'Лист'} ${index + 1}</span>
                                ${plan.is_remnant ? `<span class="badge bg-secondary">ID: ${plan.remnant_id}</span>` : ''}
                            </div>
                            <div class="card-body p-0">
                                ${generateCuttingDiagram(plan, data.sheet_width, data.sheet_height)}
                            </div>
                            <div class="card-footer">
                                <small class="text-muted">
                                    Размещено деталей: ${plan.details.length}
                                    ${plan.is_remnant ? ` | Оценка: ${plan.score.toFixed(2)}` : ''}
                                </small>
                            </div>
                        </div>
                    `;
                    cuttingImagesRow.appendChild(card);
                });

                // Показываем кнопку подтверждения, если есть размещенные детали
                if (data.placed_details > 0) {
                    confirmCuttingBtn.style.display = 'block';
                } else {
                    confirmCuttingBtn.style.display = 'none';
                }
            })
            .catch(error => {
                console.error("Ошибка:", error);
                cuttingResults.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        ${error.message}
                    </div>
                `;
                cuttingDiagramContainer.style.display = 'none';
                confirmCuttingBtn.style.display = 'none';
            })
            .finally(() => {
                calculateBtn.disabled = false;
                calculateBtn.textContent = 'Рассчитать раскрой';
            });
    });

    // Подтверждение раскроя
    confirmCuttingBtn.addEventListener('click', function() {
        const glassTypeId = glassTypeSelect.value;
        confirmCuttingBtn.disabled = true;
        confirmCuttingBtn.textContent = 'Списание...';

        fetch('/api/cutting/confirm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ glass_type_id: glassTypeId })
        })
        .then(response => {
            if (!response.ok) throw new Error('Ошибка списания деталей');
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                showToast('Детали успешно списаны!', 'success');
                confirmCuttingBtn.style.display = 'none';
                // Обновляем список деталей
                calculateBtn.click();
            } else {
                throw new Error(data.error || 'Неизвестная ошибка');
            }
        })
        .catch(error => {
            console.error("Ошибка:", error);
            showToast(error.message, 'danger');
        })
        .finally(() => {
            confirmCuttingBtn.disabled = false;
            confirmCuttingBtn.textContent = 'Списать детали';
        });
    });

    // Группировка планов раскроя по листам/остаткам
    function groupCuttingPlans(plans) {
        const grouped = [];
        const sheetPlans = {};
        
        plans.forEach(plan => {
            if (plan.is_remnant) {
                grouped.push({
                    is_remnant: true,
                    remnant_id: plan.remnant_id,
                    score: plan.score,
                    details: [plan]
                });
            } else {
                const sheetKey = `${plan.position_x}_${plan.position_y}`;
                if (!sheetPlans[sheetKey]) {
                    sheetPlans[sheetKey] = {
                        is_remnant: false,
                        details: []
                    };
                }
                sheetPlans[sheetKey].details.push(plan);
            }
        });
        
        // Добавляем планы для новых листов
        for (const key in sheetPlans) {
            grouped.push(sheetPlans[key]);
        }
        
        return grouped;
    }

    // Генерация SVG диаграммы раскроя
    function generateCuttingDiagram(plan, sheetWidth, sheetHeight) {
        const width = plan.is_remnant ? plan.details[0].width * 1.2 : sheetWidth;
        const height = plan.is_remnant ? plan.details[0].height * 1.2 : sheetHeight;
        const scale = Math.min(500 / width, 300 / height);
        const viewBoxWidth = width;
        const viewBoxHeight = height;
        
        let svg = `
            <svg width="100%" viewBox="0 0 ${viewBoxWidth} ${viewBoxHeight}" 
                 style="max-height: 500px; background: #f8f9fa; border-radius: 4px;">
                <rect x="0" y="0" width="${viewBoxWidth}" height="${viewBoxHeight}" 
                      fill="#f5f5f5" stroke="#ddd"/>
        `;
        
        // Отрисовка деталей
        plan.details.forEach(detail => {
            const fill = detail.rotated ? '#BBDEFB' : '#90CAF9';
            svg += `
                <rect x="${detail.position_x}" y="${detail.position_y}" 
                      width="${detail.width}" height="${detail.height}"
                      fill="${fill}" stroke="#2196F3" stroke-width="1"
                      rx="2" ry="2">
                    <title>Деталь ${detail.detail_id} (${detail.width}x${detail.height} мм)
${detail.rotated ? 'Повернута на 90°' : ''}</title>
                </rect>
                <text x="${detail.position_x + detail.width/2}" 
                      y="${detail.position_y + detail.height/2}" 
                      text-anchor="middle" dominant-baseline="middle"
                      font-size="${Math.min(detail.width, detail.height) * 0.2}" 
                      fill="#0d47a1">
                    ${detail.detail_id}
                </text>
            `;
        });
        
        // Отрисовка границ листа/остатка
        svg += `
            <rect x="0" y="0" width="${viewBoxWidth}" height="${viewBoxHeight}" 
                  fill="none" stroke="#666" stroke-width="2" stroke-dasharray="5,3"/>
        `;
        
        svg += `</svg>`;
        return svg;
    }

    function getEfficiencyClass(percent) {
        if (percent >= 85) return 'efficiency-high';
        if (percent >= 70) return 'efficiency-medium';
        return 'efficiency-low';
    }

    function showToast(message, type) {
        const toastContainer = document.createElement('div');
        toastContainer.className = `toast show align-items-center text-white bg-${type} border-0`;
        toastContainer.style.position = 'fixed';
        toastContainer.style.top = '20px';
        toastContainer.style.right = '20px';
        toastContainer.style.zIndex = '1100';
        
        toastContainer.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        document.body.appendChild(toastContainer);
        
        // Автоматическое скрытие через 5 секунд
        setTimeout(() => {
            toastContainer.classList.remove('show');
            setTimeout(() => toastContainer.remove(), 300);
        }, 5000);
        
        // Закрытие по кнопке
        toastContainer.querySelector('button').addEventListener('click', () => {
            toastContainer.classList.remove('show');
            setTimeout(() => toastContainer.remove(), 300);
        });
    }
});
