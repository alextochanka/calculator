// static/js/script.js
// Полная логика работы с растворами и валидация форм

document.addEventListener('DOMContentLoaded', function() {
    console.log('Script.js загружен и выполняется');
    
    // Данные растворов для автозаполнения
    const solutionsData = {
        'naoh': { G_n:5.0, x_n:0.05, x_k:0.30, t_n:85, P_gp:0.4, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'koh': { G_n:5.0, x_n:0.05, x_k:0.35, t_n:85, P_gp:0.4, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'nacl': { G_n:5.0, x_n:0.03, x_k:0.26, t_n:90, P_gp:0.45, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'kcl': { G_n:5.0, x_n:0.03, x_k:0.28, t_n:90, P_gp:0.42, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'cacl2': { G_n:5.0, x_n:0.04, x_k:0.32, t_n:88, P_gp:0.4, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'mgcl2': { G_n:5.0, x_n:0.04, x_k:0.28, t_n:88, P_gp:0.4, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'nh4cl': { G_n:5.0, x_n:0.04, x_k:0.30, t_n:85, P_gp:0.4, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'na2so4': { G_n:5.0, x_n:0.02, x_k:0.24, t_n:92, P_gp:0.45, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'mgso4': { G_n:5.0, x_n:0.03, x_k:0.29, t_n:88, P_gp:0.4, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'cuso4': { G_n:5.0, x_n:0.03, x_k:0.25, t_n:88, P_gp:0.4, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'znso4': { G_n:5.0, x_n:0.03, x_k:0.27, t_n:88, P_gp:0.4, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'al2so4': { G_n:4.5, x_n:0.02, x_k:0.22, t_n:85, P_gp:0.38, P_bc:0.018, delta_p:0.008, t_cold_water:22, steam_fraction_to_bc:0.12, height_install:5, H_tube:4.0, d_tube:0.038 },
        'nano3': { G_n:5.0, x_n:0.04, x_k:0.38, t_n:85, P_gp:0.4, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'kno3': { G_n:5.0, x_n:0.03, x_k:0.36, t_n:87, P_gp:0.42, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'ammonium': { G_n:5.0, x_n:0.06, x_k:0.42, t_n:82, P_gp:0.42, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'ch3coona': { G_n:5.0, x_n:0.05, x_k:0.35, t_n:82, P_gp:0.4, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'acetic': { G_n:4.0, x_n:0.08, x_k:0.48, t_n:75, P_gp:0.35, P_bc:0.015, delta_p:0.008, t_cold_water:25, steam_fraction_to_bc:0.12, height_install:5, H_tube:4.0, d_tube:0.038 },
        'formic': { G_n:4.0, x_n:0.07, x_k:0.44, t_n:76, P_gp:0.35, P_bc:0.015, delta_p:0.008, t_cold_water:25, steam_fraction_to_bc:0.12, height_install:5, H_tube:4.0, d_tube:0.038 },
        'citric': { G_n:5.0, x_n:0.05, x_k:0.36, t_n:80, P_gp:0.4, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 },
        'sugar': { G_n:4.0, x_n:0.08, x_k:0.45, t_n:75, P_gp:0.35, P_bc:0.015, delta_p:0.008, t_cold_water:25, steam_fraction_to_bc:0.12, height_install:5, H_tube:4.0, d_tube:0.038 },
        'glucose': { G_n:4.5, x_n:0.07, x_k:0.42, t_n:78, P_gp:0.38, P_bc:0.018, delta_p:0.008, t_cold_water:22, steam_fraction_to_bc:0.12, height_install:5, H_tube:4.0, d_tube:0.038 },
        'fructose': { G_n:4.5, x_n:0.07, x_k:0.44, t_n:77, P_gp:0.38, P_bc:0.018, delta_p:0.008, t_cold_water:22, steam_fraction_to_bc:0.12, height_install:5, H_tube:4.0, d_tube:0.038 },
        'lactose': { G_n:4.5, x_n:0.06, x_k:0.38, t_n:79, P_gp:0.38, P_bc:0.018, delta_p:0.008, t_cold_water:22, steam_fraction_to_bc:0.12, height_install:5, H_tube:4.0, d_tube:0.038 },
        'urea': { G_n:5.0, x_n:0.06, x_k:0.40, t_n:80, P_gp:0.4, P_bc:0.02, delta_p:0.01, t_cold_water:20, steam_fraction_to_bc:0.15, height_install:5, H_tube:4.0, d_tube:0.038 }
    };
    
    // Функция заполнения полей
    function fillForm(data) {
        const fields = ['G_n', 'x_n', 'x_k', 't_n', 'P_gp', 'P_bc', 'delta_p', 't_cold_water', 'steam_fraction_to_bc', 'height_install', 'H_tube', 'd_tube'];
        for (const field of fields) {
            const element = document.getElementById(field);
            if (element && data[field] !== undefined && data[field] !== null) {
                element.value = data[field];
                element.classList.remove('is-invalid');
            }
        }
    }
    
    // Функция для загрузки пользовательских растворов из localStorage
    function loadCustomSolutionsFromStorage() {
        const customSolutions = JSON.parse(localStorage.getItem('customSolutions') || '[]');
        const customGroup = document.getElementById('custom-solutions-group');
        if (customGroup) {
            customGroup.innerHTML = '';
            customSolutions.forEach(solution => {
                const option = document.createElement('option');
                option.value = solution.key;
                const displayText = solution.formula ? 
                    `${solution.name} (${solution.formula})` : 
                    solution.name;
                option.textContent = displayText;
                option.style.fontStyle = 'italic';
                customGroup.appendChild(option);
                
                // Добавляем данные в solutionsData
                solutionsData[solution.key] = solution.data;
            });
        }
        return customSolutions;
    }
    
    // Функция показа уведомлений
    function showNotification(message, type = 'success') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
        const icon = type === 'success' ? 'fa-check-circle' : (type === 'danger' ? 'fa-exclamation-triangle' : 'fa-info-circle');
        alertDiv.innerHTML = `
            <strong><i class="fas ${icon}"></i> ${type === 'success' ? 'Успешно!' : (type === 'danger' ? 'Ошибка!' : 'Внимание!')}</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const cardBody = document.querySelector('.card-body');
        const form = document.querySelector('#calc-form');
        if (cardBody && form) {
            cardBody.insertBefore(alertDiv, form);
            setTimeout(() => alertDiv.remove(), 5000);
        } else {
            alert(message);
        }
    }
    
    // Кнопка "Заполнить поля"
    const applyBtn = document.getElementById('apply-solution');
    if (applyBtn) {
        applyBtn.addEventListener('click', function() {
            const select = document.getElementById('solution-select');
            const key = select.value;
            if (key && solutionsData[key]) {
                fillForm(solutionsData[key]);
                const selectedOption = select.options[select.selectedIndex];
                const displayName = selectedOption?.textContent || key;
                showNotification(`Раствор "${displayName}" выбран. Все поля заполнены.`);
            } else if (key) {
                showNotification('Данные для выбранного раствора не найдены', 'danger');
            } else {
                showNotification('Пожалуйста, выберите раствор из списка', 'warning');
            }
        });
    }
    
    // Кнопка "Очистить все поля"
    const clearBtn = document.getElementById('clear-fields');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            const defaultValues = {
                G_n: 5.0, x_n: 0.05, x_k: 0.25, t_n: 80,
                P_gp: 0.4, P_bc: 0.02, delta_p: 0.01,
                t_cold_water: 20, steam_fraction_to_bc: 0.15,
                height_install: 5, H_tube: 4.0, d_tube: 0.038
            };
            for (const [id, val] of Object.entries(defaultValues)) {
                const el = document.getElementById(id);
                if (el) el.value = val;
            }
            const select = document.getElementById('solution-select');
            if (select) select.value = '';
            showNotification('Все поля очищены.', 'info');
        });
    }
    
    // ============================================================
    // Обновлённая валидация при добавлении раствора
    // ============================================================
    const saveBtn = document.getElementById('save-solution-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            const name = document.getElementById('solution-name')?.value;
            const formula = document.getElementById('solution-formula')?.value || '';
            if (!name) { showNotification('Введите название раствора', 'danger'); return; }
            
            // Собираем данные из полей
            const newData = {
                G_n: parseFloat(document.getElementById('solution-gn')?.value) || 5.0,
                x_n: parseFloat(document.getElementById('solution-xn')?.value) || 0.05,
                x_k: parseFloat(document.getElementById('solution-xk')?.value) || 0.25,
                t_n: parseFloat(document.getElementById('solution-tn')?.value) || 80,
                P_gp: parseFloat(document.getElementById('solution-pgp')?.value) || 0.4,
                P_bc: parseFloat(document.getElementById('solution-pbc')?.value) || 0.02,
                delta_p: parseFloat(document.getElementById('solution-deltap')?.value) || 0.01,
                t_cold_water: parseFloat(document.getElementById('solution-tcw')?.value) || 20,
                steam_fraction_to_bc: parseFloat(document.getElementById('solution-steam-fraction')?.value) || 0.15,
                height_install: parseFloat(document.getElementById('solution-height')?.value) || 5,
                H_tube: parseFloat(document.getElementById('solution-htube')?.value) || 4.0,
                d_tube: parseFloat(document.getElementById('solution-dtube')?.value) || 0.038
            };
            
            // Обновлённые диапазоны валидации
            if (newData.G_n < 0.1 || newData.G_n > 100) { showNotification('Расход G_n должен быть в диапазоне 0.1-100 кг/с', 'danger'); return; }
            if (newData.x_n < 0.01 || newData.x_n > 0.5) { showNotification('Начальная концентрация x_n должна быть в диапазоне 0.01-0.5', 'danger'); return; }
            if (newData.x_k < 0.05 || newData.x_k > 0.5) { showNotification('Конечная концентрация x_k должна быть в диапазоне 0.05-0.5', 'danger'); return; }
            if (newData.x_k <= newData.x_n) { showNotification('Конечная концентрация должна быть больше начальной', 'danger'); return; }
            if (newData.t_n < 20 || newData.t_n > 120) { showNotification('Температура t_n должна быть в диапазоне 20-120 °C', 'danger'); return; }
            if (newData.P_gp < 0.15 || newData.P_gp > 0.8) { showNotification('Давление P_gp должно быть в диапазоне 0.15-0.8 МПа', 'danger'); return; }
            if (newData.P_bc < 0.015 || newData.P_bc > 0.06) { showNotification('Давление P_bc должно быть в диапазоне 0.015-0.06 МПа', 'danger'); return; }
            if (newData.delta_p < 0.005 || newData.delta_p > 0.03) { showNotification('Потери давления должны быть в диапазоне 0.005-0.03 МПа', 'danger'); return; }
            if (newData.P_gp <= newData.P_bc) { showNotification('Давление греющего пара должно быть больше давления в конденсаторе', 'danger'); return; }
            if (newData.t_cold_water < 5 || newData.t_cold_water > 30) { showNotification('Температура охлаждающей воды должна быть в диапазоне 5-30 °C', 'danger'); return; }
            if (newData.steam_fraction_to_bc < 0.05 || newData.steam_fraction_to_bc > 0.25) { showNotification('Доля пара должна быть в диапазоне 0.05-0.25', 'danger'); return; }
            if (newData.height_install < 1 || newData.height_install > 15) {showNotification('Высота подъёма жидкости должна быть в диапазоне 1-15 м', 'danger'); return; }
            if (newData.H_tube < 2.0 || newData.H_tube > 5.0) { showNotification('Высота труб должна быть в диапазоне 2-5 м', 'danger'); return; }
            if (newData.d_tube < 0.025 || newData.d_tube > 0.045) { showNotification('Диаметр труб должен быть в диапазоне 0.025-0.045 м', 'danger'); return; }
            
            const key = 'custom_' + Date.now() + '_' + name.toLowerCase().replace(/[^a-z0-9]/g, '_');
            solutionsData[key] = newData;
            
            // Сохраняем в localStorage
            const customSolutions = JSON.parse(localStorage.getItem('customSolutions') || '[]');
            customSolutions.push({
                key: key,
                name: name,
                formula: formula,
                data: newData
            });
            localStorage.setItem('customSolutions', JSON.stringify(customSolutions));
            
            // Обновляем выпадающий список
            const customGroup = document.getElementById('custom-solutions-group');
            if (customGroup) {
                const option = document.createElement('option');
                option.value = key;
                const displayText = formula ? `${name} (${formula})` : name;
                option.textContent = displayText;
                option.style.fontStyle = 'italic';
                customGroup.appendChild(option);
                option.selected = true;
            }
            
            fillForm(newData);
            
            const modal = bootstrap.Modal.getInstance(document.getElementById('addSolutionModal'));
            if (modal) modal.hide();
            
            // Сброс формы
            document.getElementById('add-solution-form')?.reset();
            document.getElementById('solution-name').value = '';
            document.getElementById('solution-formula').value = '';
            
            showNotification(`Раствор "${name}"${formula ? ' (' + formula + ')' : ''} успешно добавлен!`);
        });
    }
    
    // Импорт из CSV
    const importCsvBtn = document.getElementById('import-csv-btn');
    const csvFileInput = document.getElementById('csv-file-input');
    const confirmImportBtn = document.getElementById('confirm-import-btn');
    let importedData = null;
    
    if (importCsvBtn) {
        importCsvBtn.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('importCsvModal'));
            modal.show();
            if (csvFileInput) csvFileInput.value = '';
            document.getElementById('csv-preview').style.display = 'none';
            importedData = null;
        });
    }
    
    if (csvFileInput) {
        csvFileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(event) {
                const content = event.target.result;
                const lines = content.split('\n');
                
                // Определяем, есть ли заголовки
                let startLine = 0;
                let firstLine = lines[0].trim().toLowerCase();
                
                // Проверяем, является ли первая строка заголовком
                if (firstLine.includes('g_n') || firstLine.includes('расход') || firstLine.includes('x_n')) {
                    startLine = 1;
                }
                
                // Парсим данные
                const dataLine = lines[startLine];
                if (!dataLine) {
                    showNotification('CSV файл пуст или имеет неверный формат', 'danger');
                    return;
                }
                
                const values = dataLine.split(',').map(v => parseFloat(v.trim()));
                
                // Проверяем количество полей
                if (values.length < 12) {
                    showNotification(`Недостаточно данных. Найдено ${values.length} полей, требуется 12`, 'danger');
                    return;
                }
                
                importedData = {
                    G_n: values[0],
                    x_n: values[1],
                    x_k: values[2],
                    t_n: values[3],
                    P_gp: values[4],
                    P_bc: values[5],
                    delta_p: values[6],
                    t_cold_water: values[7],
                    steam_fraction_to_bc: values[8],
                    height_install: values[9],
                    H_tube: values[10],
                    d_tube: values[11]
                };
                
                // Показываем предпросмотр
                const previewDiv = document.getElementById('csv-preview');
                const previewContent = document.getElementById('csv-preview-content');
                previewContent.textContent = JSON.stringify(importedData, null, 2);
                previewDiv.style.display = 'block';
                
                // ============================================================
                // Обновлённая валидация CSV
                // ============================================================
                const errors = [];
                if (importedData.G_n < 0.1 || importedData.G_n > 100) errors.push('Расход G_n вне диапазона [0.1-100]');
                if (importedData.x_n < 0.01 || importedData.x_n > 0.5) errors.push('Начальная концентрация x_n вне диапазона [0.01-0.5]');
                if (importedData.x_k < 0.05 || importedData.x_k > 0.5) errors.push('Конечная концентрация x_k вне диапазона [0.05-0.5]');
                if (importedData.x_k <= importedData.x_n) errors.push('Конечная концентрация должна быть больше начальной');
                if (importedData.t_n < 20 || importedData.t_n > 120) errors.push('Температура t_n вне диапазона [20-120]');
                if (importedData.P_gp < 0.15 || importedData.P_gp > 0.8) errors.push('Давление P_gp вне диапазона [0.15-0.8]');
                if (importedData.P_bc < 0.015 || importedData.P_bc > 0.06) errors.push('Давление P_bc вне диапазона [0.015-0.06]');
                if (importedData.delta_p < 0.005 || importedData.delta_p > 0.03) errors.push('Потери давления вне диапазона [0.005-0.03]');
                if (importedData.P_gp <= importedData.P_bc) errors.push('Давление греющего пара должно быть больше давления в конденсаторе');
                if (importedData.t_cold_water < 5 || importedData.t_cold_water > 30) errors.push('Температура охлаждающей воды вне диапазона [5-30]');
                if (importedData.steam_fraction_to_bc < 0.05 || importedData.steam_fraction_to_bc > 0.25) errors.push('Доля пара вне диапазона [0.05-0.25]');
                if (importedData.height_install < 1 || importedData.height_install > 15) errors.push('Высота подъёма жидкости вне диапазона [1-15]');
                if (importedData.H_tube < 2.0 || importedData.H_tube > 5.0) errors.push('Высота труб вне диапазона [2-5]');
                if (importedData.d_tube < 0.025 || importedData.d_tube > 0.045) errors.push('Диаметр труб вне диапазона [0.025-0.045]');
      
                if (errors.length > 0) {
                    previewContent.innerHTML = `<span style="color: red;">Ошибки валидации:\n${errors.join('\n')}</span>\n\nДанные:\n${previewContent.textContent}`;
                    confirmImportBtn.disabled = true;
                } else {
                    confirmImportBtn.disabled = false;
                }
            };
            
            reader.onerror = function() {
                showNotification('Ошибка чтения файла', 'danger');
            };
            
            reader.readAsText(file, 'UTF-8');
        });
    }
    
    if (confirmImportBtn) {
        confirmImportBtn.addEventListener('click', function() {
            if (importedData) {
                fillForm(importedData);
                
                const modal = bootstrap.Modal.getInstance(document.getElementById('importCsvModal'));
                modal.hide();
                
                showNotification('Данные успешно импортированы из CSV!', 'success');
                
                if (csvFileInput) csvFileInput.value = '';
                importedData = null;
            }
        });
    }
    
    // Функция экспорта текущих данных в CSV
    function exportToCsv() {
        const fields = ['G_n', 'x_n', 'x_k', 't_n', 'P_gp', 'P_bc', 'delta_p', 't_cold_water', 'steam_fraction_to_bc', 'height_install', 'H_tube', 'd_tube'];
        const data = [];
        
        // Заголовки
        data.push(fields.join(','));
        
        // Значения
        const values = fields.map(field => {
            const element = document.getElementById(field);
            return element ? element.value : '';
        });
        data.push(values.join(','));
        
        // Создаем и скачиваем файл
        const blob = new Blob([data.join('\n')], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', 'evaporator_data.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        showNotification('Данные экспортированы в CSV файл', 'success');
    }
    
    // Добавляем кнопку экспорта
    function addExportButton() {
        const clearBtnParent = document.getElementById('clear-fields')?.closest('.d-grid');
        if (clearBtnParent && !document.getElementById('export-csv-btn')) {
            const exportBtn = document.createElement('button');
            exportBtn.type = 'button';
            exportBtn.id = 'export-csv-btn';
            exportBtn.className = 'btn btn-outline-info mb-2';
            exportBtn.innerHTML = '<i class="fas fa-download"></i> Экспорт в CSV';
            exportBtn.onclick = exportToCsv;
            clearBtnParent.insertBefore(exportBtn, document.getElementById('clear-fields'));
        }
    }
    
    // Загружаем пользовательские растворы при старте
    loadCustomSolutionsFromStorage();
    addExportButton();
    
    console.log('Script.js инициализация завершена');
});