document.addEventListener('DOMContentLoaded', function () {
    const glassTypeSelect = document.getElementById('glassTypeSelect');
    const calculateBtn = document.getElementById('calculateBtn');
    const detailsList = document.getElementById('detailsList');
    const totalDetailsSpan = document.getElementById('totalDetails');
    const cuttingResults = document.getElementById('cuttingResults');
    const cuttingDiagramContainer = document.getElementById('cuttingDiagramContainer');
    const cuttingImagesRow = document.getElementById('cuttingImagesRow');

    calculateBtn.addEventListener('click', function () {
        const glassTypeId = glassTypeSelect.value;

        // Загружаем детали по типу стекла
        fetch(`/details?glass_type_id=${glassTypeId}`)
            .then(response => {
                if (!response.ok) throw new Error('Ошибка загрузки деталей');
                return response.json();
            })
            .then(data => {
                // Очистка и вывод деталей
                detailsList.innerHTML = '';
                totalDetailsSpan.textContent = data.length;

                data.forEach(detail => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${detail.detail_id}</td>
                        <td>${detail.width}</td>
                        <td>${detail.height}</td>
                    `;
                    detailsList.appendChild(row);
                });

                // Убираем предупреждение
                cuttingResults.innerHTML = '';

                // Показываем контейнер для картинок
                cuttingDiagramContainer.style.display = 'block';

                // Генерация HTML для картинок раскроя
                const imagesHTML = Array.from({ length: 7 }, (_, i) => {
                    const num = i + 1;
                    return `
                        <div class="col-md-6 mb-3">
                            <div class="card">
                                <div class="card-header">Раскрой ${num}</div>
                                <div class="card-body">
                                    <img src="../static/cutting/l${num}.png" 
                                        alt="Раскрой ${num}" 
                                        class="img-fluid rounded border shadow-sm"
                                        style="max-height: 300px; object-fit: contain;">
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');

                cuttingImagesRow.innerHTML = imagesHTML;
            })
            .catch(error => {
                console.error("Ошибка при загрузке данных:", error);
                cuttingResults.innerHTML = `<div class="alert alert-danger">Ошибка загрузки деталей</div>`;
                cuttingDiagramContainer.style.display = 'none';
            });
    });
});
