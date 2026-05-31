"""
Главный модуль Flask веб-приложения для расчёта трёхкорпусной выпарной установки
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
import os
from datetime import datetime

from calculations import (EvaporatorInputData, EvaporatorCalculator,
                          MaterialBalance, AuxiliaryEquipmentCalculator,
                          HydraulicCalculator, ThermalBalance, WaterProperties)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'evaporator-calc-secret-key-2024'
app.config['SESSION_TYPE'] = 'filesystem'

# ============================================================
# ИСПРАВЛЕНО: Обновлённые диапазоны валидации
# ============================================================
VALIDATION_RANGES = {
    'G_n': (0.1, 100, 'кг/с'),
    'x_n': (0.01, 0.5, 'масс. доли'),
    'x_k': (0.05, 0.5, 'масс. доли'),
    't_n': (20, 120, '°C'),
    'P_gp': (0.15, 0.8, 'МПа'),
    'P_bc': (0.015, 0.06, 'МПа'),
    'delta_p': (0.005, 0.03, 'МПа'),
    't_cold_water': (5, 30, '°C'),
    'steam_fraction_to_bc': (0.05, 0.25, 'доля'),
    'height_install': (1, 15, 'м'),
    'H_tube': (2.0, 5.0, 'м'),
    'd_tube': (0.025, 0.045, 'м')
}

# База данных растворов для быстрого выбора (только 12 полей)
SOLUTIONS_DB = {
    'naoh': {
        'name': 'Гидроксид натрия (NaOH)',
        'formula': 'NaOH',
        'data': {
            'G_n': 5.0, 'x_n': 0.05, 'x_k': 0.30, 't_n': 85,
            'P_gp': 0.4, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'koh': {
        'name': 'Гидроксид калия (KOH)',
        'formula': 'KOH',
        'data': {
            'G_n': 5.0, 'x_n': 0.05, 'x_k': 0.35, 't_n': 85,
            'P_gp': 0.4, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'nacl': {
        'name': 'Хлорид натрия (NaCl)',
        'formula': 'NaCl',
        'data': {
            'G_n': 5.0, 'x_n': 0.03, 'x_k': 0.26, 't_n': 90,
            'P_gp': 0.45, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'kcl': {
        'name': 'Хлорид калия (KCl)',
        'formula': 'KCl',
        'data': {
            'G_n': 5.0, 'x_n': 0.03, 'x_k': 0.28, 't_n': 90,
            'P_gp': 0.42, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'cacl2': {
        'name': 'Хлорид кальция (CaCl₂)',
        'formula': 'CaCl₂',
        'data': {
            'G_n': 5.0, 'x_n': 0.04, 'x_k': 0.32, 't_n': 88,
            'P_gp': 0.4, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'mgcl2': {
        'name': 'Хлорид магния (MgCl₂)',
        'formula': 'MgCl₂',
        'data': {
            'G_n': 5.0, 'x_n': 0.04, 'x_k': 0.28, 't_n': 88,
            'P_gp': 0.4, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'nh4cl': {
        'name': 'Хлорид аммония (NH₄Cl)',
        'formula': 'NH₄Cl',
        'data': {
            'G_n': 5.0, 'x_n': 0.04, 'x_k': 0.30, 't_n': 85,
            'P_gp': 0.4, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'na2so4': {
        'name': 'Сульфат натрия (Na₂SO₄)',
        'formula': 'Na₂SO₄',
        'data': {
            'G_n': 5.0, 'x_n': 0.02, 'x_k': 0.24, 't_n': 92,
            'P_gp': 0.45, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'mgso4': {
        'name': 'Сульфат магния (MgSO₄)',
        'formula': 'MgSO₄',
        'data': {
            'G_n': 5.0, 'x_n': 0.03, 'x_k': 0.29, 't_n': 88,
            'P_gp': 0.4, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'cuso4': {
        'name': 'Сульфат меди (CuSO₄)',
        'formula': 'CuSO₄',
        'data': {
            'G_n': 5.0, 'x_n': 0.03, 'x_k': 0.25, 't_n': 88,
            'P_gp': 0.4, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'znso4': {
        'name': 'Сульфат цинка (ZnSO₄)',
        'formula': 'ZnSO₄',
        'data': {
            'G_n': 5.0, 'x_n': 0.03, 'x_k': 0.27, 't_n': 88,
            'P_gp': 0.4, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'al2so4': {
        'name': 'Сульфат алюминия (Al₂(SO₄)₃)',
        'formula': 'Al₂(SO₄)₃',
        'data': {
            'G_n': 4.5, 'x_n': 0.02, 'x_k': 0.22, 't_n': 85,
            'P_gp': 0.38, 'P_bc': 0.018, 'delta_p': 0.008,
            't_cold_water': 22, 'steam_fraction_to_bc': 0.12,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'nano3': {
        'name': 'Нитрат натрия (NaNO₃)',
        'formula': 'NaNO₃',
        'data': {
            'G_n': 5.0, 'x_n': 0.04, 'x_k': 0.38, 't_n': 85,
            'P_gp': 0.4, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'kno3': {
        'name': 'Нитрат калия (KNO₃)',
        'formula': 'KNO₃',
        'data': {
            'G_n': 5.0, 'x_n': 0.03, 'x_k': 0.36, 't_n': 87,
            'P_gp': 0.42, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'ammonium': {
        'name': 'Аммиачная селитра (NH₄NO₃)',
        'formula': 'NH₄NO₃',
        'data': {
            'G_n': 5.0, 'x_n': 0.06, 'x_k': 0.42, 't_n': 82,
            'P_gp': 0.42, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'ch3coona': {
        'name': 'Ацетат натрия (CH₃COONa)',
        'formula': 'CH₃COONa',
        'data': {
            'G_n': 5.0, 'x_n': 0.05, 'x_k': 0.35, 't_n': 82,
            'P_gp': 0.4, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'acetic': {
        'name': 'Уксусная кислота (CH₃COOH)',
        'formula': 'CH₃COOH',
        'data': {
            'G_n': 4.0, 'x_n': 0.08, 'x_k': 0.48, 't_n': 75,
            'P_gp': 0.35, 'P_bc': 0.015, 'delta_p': 0.008,
            't_cold_water': 25, 'steam_fraction_to_bc': 0.12,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'formic': {
        'name': 'Муравьиная кислота (HCOOH)',
        'formula': 'HCOOH',
        'data': {
            'G_n': 4.0, 'x_n': 0.07, 'x_k': 0.44, 't_n': 76,
            'P_gp': 0.35, 'P_bc': 0.015, 'delta_p': 0.008,
            't_cold_water': 25, 'steam_fraction_to_bc': 0.12,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'citric': {
        'name': 'Лимонная кислота (C₆H₈O₇)',
        'formula': 'C₆H₈O₇',
        'data': {
            'G_n': 5.0, 'x_n': 0.05, 'x_k': 0.36, 't_n': 80,
            'P_gp': 0.4, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'sugar': {
        'name': 'Сахарный раствор (сахароза)',
        'formula': 'C₁₂H₂₂O₁₁',
        'data': {
            'G_n': 4.0, 'x_n': 0.08, 'x_k': 0.45, 't_n': 75,
            'P_gp': 0.35, 'P_bc': 0.015, 'delta_p': 0.008,
            't_cold_water': 25, 'steam_fraction_to_bc': 0.12,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'glucose': {
        'name': 'Глюкоза (C₆H₁₂O₆)',
        'formula': 'C₆H₁₂O₆',
        'data': {
            'G_n': 4.5, 'x_n': 0.07, 'x_k': 0.42, 't_n': 78,
            'P_gp': 0.38, 'P_bc': 0.018, 'delta_p': 0.008,
            't_cold_water': 22, 'steam_fraction_to_bc': 0.12,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'fructose': {
        'name': 'Фруктоза (C₆H₁₂O₆)',
        'formula': 'C₆H₁₂O₆',
        'data': {
            'G_n': 4.5, 'x_n': 0.07, 'x_k': 0.44, 't_n': 77,
            'P_gp': 0.38, 'P_bc': 0.018, 'delta_p': 0.008,
            't_cold_water': 22, 'steam_fraction_to_bc': 0.12,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'lactose': {
        'name': 'Лактоза (C₁₂H₂₂O₁₁)',
        'formula': 'C₁₂H₂₂O₁₁',
        'data': {
            'G_n': 4.5, 'x_n': 0.06, 'x_k': 0.38, 't_n': 79,
            'P_gp': 0.38, 'P_bc': 0.018, 'delta_p': 0.008,
            't_cold_water': 22, 'steam_fraction_to_bc': 0.12,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    },
    'urea': {
        'name': 'Мочевина (карбамид)',
        'formula': 'CH₄N₂O',
        'data': {
            'G_n': 5.0, 'x_n': 0.06, 'x_k': 0.40, 't_n': 80,
            'P_gp': 0.4, 'P_bc': 0.02, 'delta_p': 0.01,
            't_cold_water': 20, 'steam_fraction_to_bc': 0.15,
            'height_install': 5, 'H_tube': 4.0, 'd_tube': 0.038
        }
    }
}

# Хранилище пользовательских растворов
user_solutions = {}

@app.route('/api/import-csv', methods = ['POST'])
def api_import_csv():
    """API для импорта данных из CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не загружен'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не выбран'}), 400

        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Поддерживаются только CSV файлы'}), 400

        import csv
        from io import TextIOWrapper

        # Читаем CSV файл
        content = file.read().decode('utf-8-sig')
        csv_reader = csv.reader(TextIOWrapper(io.BytesIO(content.encode()), 'utf-8'))

        rows = list(csv_reader)
        if len(rows) == 0:
            return jsonify({'success': False, 'error': 'CSV файл пуст'}), 400

        # Определяем строку с данными (пропускаем заголовки если есть)
        data_row = rows[0]
        if len(rows) > 1 and any(keyword in rows[0][0].lower() for keyword in ['g_n', 'расход', 'x_n']):
            data_row = rows[1]

        # Парсим данные
        expected_fields = ['G_n', 'x_n', 'x_k', 't_n', 'P_gp', 'P_bc', 'delta_p',
                           't_cold_water', 'steam_fraction_to_bc', 'height_install', 'H_tube', 'd_tube']

        if len(data_row) < 12:
            return jsonify(
                {'success': False, 'error': f'Недостаточно данных. Найдено {len(data_row)} полей, требуется 12'}), 400

        try:
            imported_data = {
                'G_n': float(data_row[0].strip()),
                'x_n': float(data_row[1].strip()),
                'x_k': float(data_row[2].strip()),
                't_n': float(data_row[3].strip()),
                'P_gp': float(data_row[4].strip()),
                'P_bc': float(data_row[5].strip()),
                'delta_p': float(data_row[6].strip()),
                't_cold_water': float(data_row[7].strip()) if len(data_row) > 7 else 20.0,
                'steam_fraction_to_bc': float(data_row[8].strip()) if len(data_row) > 8 else 0.15,
                'height_install': float(data_row[9].strip()) if len(data_row) > 9 else 5.0,
                'H_tube': float(data_row[10].strip()) if len(data_row) > 10 else 4.0,
                'd_tube': float(data_row[11].strip()) if len(data_row) > 11 else 0.038
            }
        except ValueError as e:
            return jsonify({'success': False, 'error': f'Ошибка преобразования данных: {str(e)}'}), 400

        # ============================================================
        # ИСПРАВЛЕНО: Обновлённая валидация с новыми диапазонами
        # ============================================================
        errors = []
        if imported_data['G_n'] < 0.1 or imported_data['G_n'] > 100:
            errors.append('Расход G_n должен быть в диапазоне [0.1-100] кг/с')
        if imported_data['x_n'] < 0.01 or imported_data['x_n'] > 0.5:
            errors.append('Начальная концентрация x_n должна быть в диапазоне [0.01-0.5]')
        if imported_data['x_k'] < 0.05 or imported_data['x_k'] > 0.5:
            errors.append('Конечная концентрация x_k должна быть в диапазоне [0.05-0.5]')
        if imported_data['x_k'] <= imported_data['x_n']:
            errors.append('Конечная концентрация должна быть больше начальной')
        if imported_data['t_n'] < 20 or imported_data['t_n'] > 120:
            errors.append('Температура t_n должна быть в диапазоне [20-120] °C')
        if imported_data['P_gp'] < 0.15 or imported_data['P_gp'] > 0.8:
            errors.append('Давление P_gp должно быть в диапазоне [0.15-0.8] МПа')
        if imported_data['P_bc'] < 0.015 or imported_data['P_bc'] > 0.06:
            errors.append('Давление P_bc должно быть в диапазоне [0.015-0.06] МПа')
        if imported_data['delta_p'] < 0.005 or imported_data['delta_p'] > 0.03:
            errors.append('Потери давления должны быть в диапазоне [0.005-0.03] МПа')
        if imported_data['P_gp'] <= imported_data['P_bc']:
            errors.append('Давление греющего пара должно быть больше давления в конденсаторе')
        if imported_data['t_cold_water'] < 5 or imported_data['t_cold_water'] > 30:
            errors.append('Температура охлаждающей воды должна быть в диапазоне [5-30] °C')
        if imported_data['steam_fraction_to_bc'] < 0.05 or imported_data['steam_fraction_to_bc'] > 0.25:
            errors.append('Доля пара в конденсатор должна быть в диапазоне [0.05-0.25]')
        if imported_data['height_install'] < 1 or imported_data['height_install'] > 15:
            errors.append('Высота установки должна быть в диапазоне [1-15] м')
        if imported_data['H_tube'] < 2.0 or imported_data['H_tube'] > 5.0:
            errors.append('Высота труб H_tube должна быть в диапазоне [2-5] м')
        if imported_data['d_tube'] < 0.025 or imported_data['d_tube'] > 0.045:
            errors.append('Диаметр труб d_tube должен быть в диапазоне [0.025-0.045] м')

        if errors:
            return jsonify({'success': False, 'error': '; '.join(errors)}), 400

        return jsonify({
            'success': True,
            'data': imported_data,
            'message': 'Данные успешно импортированы'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/solutions')
def api_solutions():
    """API для получения списка доступных растворов"""
    all_solutions = dict(SOLUTIONS_DB)
    all_solutions.update(user_solutions)
    return jsonify({'success': True, 'solutions': all_solutions})


@app.route('/api/solution/<solution_key>')
def api_solution_data(solution_key):
    """API для получения данных конкретного раствора"""
    if solution_key in SOLUTIONS_DB:
        return jsonify({'success': True, 'solution': SOLUTIONS_DB[solution_key]})
    if solution_key in user_solutions:
        return jsonify({'success': True, 'solution': user_solutions[solution_key]})
    return jsonify({'success': False, 'error': 'Раствор не найден'}), 404


@app.route('/api/add-solution', methods=['POST'])
def api_add_solution():
    """API для добавления пользовательского раствора (только 12 полей)"""
    try:
        data = request.get_json()

        # Проверка обязательных полей
        required_fields = ['name', 'G_n', 'x_n', 'x_k', 't_n', 'P_gp', 'P_bc', 'delta_p']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Отсутствует поле {field}'}), 400

        # ============================================================
        # ИСПРАВЛЕНО: Валидация пользовательского раствора с новыми диапазонами
        # ============================================================
        try:
            G_n = float(data['G_n'])
            x_n = float(data['x_n'])
            x_k = float(data['x_k'])
            t_n = float(data['t_n'])
            P_gp = float(data['P_gp'])
            P_bc = float(data['P_bc'])
            delta_p = float(data['delta_p'])
            t_cold_water = float(data.get('t_cold_water', 20))
            steam_fraction_to_bc = float(data.get('steam_fraction_to_bc', 0.15))
            height_install = float(data.get('height_install', 5))
            H_tube = float(data.get('H_tube', 4.0))
            d_tube = float(data.get('d_tube', 0.038))
        except ValueError as e:
            return jsonify({'success': False, 'error': f'Ошибка преобразования чисел: {str(e)}'}), 400

        errors = []
        if G_n < 0.1 or G_n > 100:
            errors.append('Расход G_n должен быть в диапазоне 0.1-100 кг/с')
        if x_n < 0.01 or x_n > 0.5:
            errors.append('Начальная концентрация x_n должна быть в диапазоне 0.01-0.5')
        if x_k < 0.05 or x_k > 0.5:
            errors.append('Конечная концентрация x_k должна быть в диапазоне 0.05-0.5')
        if x_k <= x_n:
            errors.append('Конечная концентрация должна быть больше начальной')
        if t_n < 20 or t_n > 120:
            errors.append('Температура t_n должна быть в диапазоне 20-120 °C')
        if P_gp < 0.15 or P_gp > 0.8:
            errors.append('Давление P_gp должно быть в диапазоне 0.15-0.8 МПа')
        if P_bc < 0.015 or P_bc > 0.06:
            errors.append('Давление P_bc должно быть в диапазоне 0.015-0.06 МПа')
        if delta_p < 0.005 or delta_p > 0.03:
            errors.append('Потери давления должны быть в диапазоне 0.005-0.03 МПа')
        if P_gp <= P_bc:
            errors.append('Давление греющего пара должно быть больше давления в конденсаторе')
        if t_cold_water < 5 or t_cold_water > 30:
            errors.append('Температура охлаждающей воды должна быть в диапазоне 5-30 °C')
        if steam_fraction_to_bc < 0.05 or steam_fraction_to_bc > 0.25:
            errors.append('Доля пара в конденсатор должна быть в диапазоне 0.05-0.25')
        if height_install < 1 or height_install > 15:
            errors.append('Высота установки должна быть в диапазоне 1-15 м')
        if H_tube < 2.0 or H_tube > 5.0:
            errors.append('Высота труб H_tube должна быть в диапазоне 2-5 м')
        if d_tube < 0.025 or d_tube > 0.045:
            errors.append('Диаметр труб d_tube должен быть в диапазоне 0.025-0.045 м')

        if errors:
            return jsonify({'success': False, 'error': '; '.join(errors)}), 400

        # Генерация ключа из названия
        key = data['name'].lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')

        # Если ключ уже существует, добавляем суффикс
        original_key = key
        counter = 1
        while key in SOLUTIONS_DB or key in user_solutions:
            key = f"{original_key}_{counter}"
            counter += 1

        # Сохраняем раствор
        user_solutions[key] = {
            'name': data['name'],
            'formula': data.get('formula', ''),
            'data': {
                'G_n': G_n,
                'x_n': x_n,
                'x_k': x_k,
                't_n': t_n,
                'P_gp': P_gp,
                'P_bc': P_bc,
                'delta_p': delta_p,
                't_cold_water': t_cold_water,
                'steam_fraction_to_bc': steam_fraction_to_bc,
                'height_install': height_install,
                'H_tube': H_tube,
                'd_tube': d_tube
            },
            'is_custom': True
        }

        return jsonify({
            'success': True,
            'message': f'Раствор "{data["name"]}" успешно добавлен',
            'key': key,
            'solution': user_solutions[key]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/delete-solution/<solution_key>', methods=['DELETE'])
def api_delete_solution(solution_key):
    """API для удаления пользовательского раствора"""
    if solution_key in user_solutions:
        deleted = user_solutions.pop(solution_key)
        return jsonify({'success': True, 'message': f'Раствор "{deleted["name"]}" удален'})
    return jsonify({'success': False, 'error': 'Раствор не найден'}), 404


def validate_input(name, value):
    """Валидация входных данных"""
    if name in VALIDATION_RANGES:
        min_val, max_val, unit = VALIDATION_RANGES[name]
        if value < min_val or value > max_val:
            # Русские названия для полей
            field_names = {
                'G_n': 'Расход исходного раствора G_n',
                'x_n': 'Начальная концентрация x_n',
                'x_k': 'Конечная концентрация x_k',
                't_n': 'Начальная температура t_n',
                'P_gp': 'Давление греющего пара P_гп',
                'P_bc': 'Давление в конденсаторе P_бк',
                'delta_p': 'Потери давления Δp',
                't_cold_water': 'Температура охлаждающей воды',
                'steam_fraction_to_bc': 'Доля пара в конденсатор',
                'height_install': 'Высота подъёма жидкости',
                'H_tube': 'Высота греющих труб H_тр',
                'd_tube': 'Диаметр греющих труб d_тр'
            }
            display_name = field_names.get(name, name)
            return False, f"{display_name} должно быть в диапазоне [{min_val}, {max_val}] {unit}"
    return True, ""


@app.route('/', methods=['GET', 'POST'])
def index():
    """Главная страница с формой ввода"""
    if request.method == 'GET':
        return render_template('index.html', form_data={})

    try:
        input_data = {}
        errors = []

        fields = ['G_n', 'x_n', 'x_k', 't_n', 'P_gp', 'P_bc', 'delta_p']
        for field in fields:
            value = float(request.form.get(field, 0))
            is_valid, error_msg = validate_input(field, value)
            if is_valid:
                input_data[field] = value
            else:
                errors.append(error_msg)

        # Опциональные поля (также валидируем)
        input_data['H_tube'] = float(request.form.get('H_tube', 4.0))
        input_data['d_tube'] = float(request.form.get('d_tube', 0.038))
        input_data['t_cold_water'] = float(request.form.get('t_cold_water', 20.0))
        input_data['steam_fraction_to_bc'] = float(request.form.get('steam_fraction_to_bc', 0.15))
        input_data['height_install'] = float(request.form.get('height_install', 5.0))

        # Валидация опциональных полей
        for field in ['H_tube', 'd_tube', 't_cold_water', 'steam_fraction_to_bc', 'height_install']:
            if field in VALIDATION_RANGES:
                is_valid, error_msg = validate_input(field, input_data[field])
                if not is_valid:
                    errors.append(error_msg)

        if input_data['x_k'] <= input_data['x_n']:
            errors.append("Конечная концентрация должна быть больше начальной")

        if input_data['P_gp'] <= input_data['P_bc']:
            errors.append("Давление греющего пара должно быть больше давления в конденсаторе")

        if errors:
            return render_template('index.html',
                                   error="; ".join(errors),
                                   form_data=request.form)

        data = EvaporatorInputData(
            G_n=input_data['G_n'],
            x_n=input_data['x_n'],
            x_k=input_data['x_k'],
            t_n=input_data['t_n'],
            P_gp=input_data['P_gp'],
            P_bc=input_data['P_bc'],
            H_tube=input_data['H_tube'],
            d_tube=input_data['d_tube'],
            delta_tube=0.002,
            delta_p=input_data['delta_p'],
            t_cold_water=input_data['t_cold_water'],
            steam_fraction_to_bc=input_data['steam_fraction_to_bc'],
            height_install=input_data['height_install']
        )

        calculator = EvaporatorCalculator(data)
        results = calculator.run_calculation()

        # Расчёт вспомогательного оборудования
        aux_calc = AuxiliaryEquipmentCalculator(results, data)

        bc_results = aux_calc.calculate_barometric_condenser()
        vp_results = aux_calc.calculate_vacuum_pump()
        ph_results = aux_calc.calculate_preheater()

        # Расчёт насосов для перекачки раствора
        pump_feed = aux_calc.calculate_pump(
            G_flow=results.G[0],
            x_flow=results.x[0],
            t_flow=results.t[0],
            P_suction=0.1013,  # атмосферное давление
            P_discharge=results.P[0]
        )

        pump_product = aux_calc.calculate_pump(
            G_flow=results.G[2],
            x_flow=results.x[2],
            t_flow=results.t[2],
            P_suction=results.P[2],
            P_discharge=0.1013  # атмосферное давление
        )

        # Гидравлические расчёты
        hydr_calc = HydraulicCalculator()

        # Расчёт диаметров трубопроводов
        steam_line = hydr_calc.calculate_optimal_diameter(
            G=results.D_gp,
            rho=0.6,  # плотность пара
            w_opt_min=20,
            w_opt_max=40
        )

        solution_line = hydr_calc.calculate_optimal_diameter(
            G=results.G[0],
            rho=results.rho[0],
            w_opt_min=1,
            w_opt_max=3
        )

        # Тепловые потери
        Q_total = sum(results.Q) * 1000
        Q_loss = ThermalBalance.calculate_heat_losses(Q_total)
        efficiency = ThermalBalance.calculate_efficiency(Q_total - Q_loss, Q_total)

        # Сохраняем результаты в сессии
        session['results'] = {
            'P': results.P,
            't': results.t,
            'x': results.x,
            'W': results.W,
            'G': results.G,
            'Q': results.Q,
            'K': results.K,
            'F': results.F,
            'delta_t': results.delta_t,
            'W_total': results.W_total,
            'D_gp': results.D_gp,
            'ud_par': results.ud_par,
            'rho': results.rho,
            'mu': results.mu,
            'cp': results.cp,
            'lam': results.lam,
            'depression': results.depression
        }

        session['aux_results'] = {
            'bc': {
                'G_cooling_water': bc_results.G_cooling_water,
                'D_cond': bc_results.D_cond,
                'H_barometric': bc_results.H_barometric,
                'd_barometric': bc_results.d_barometric,
                'w_water': bc_results.w_water,
                't_out': bc_results.t_out
            },
            'vp': {
                'G_air': vp_results.G_air,
                'V_air': vp_results.V_air,
                'V_air_min': vp_results.V_air_min,
                't_air': vp_results.t_air,
                'residual_pressure': vp_results.residual_pressure
            },
            'ph': {
                'F_preheater': ph_results.F_preheater,
                'delta_t_mid': ph_results.delta_t_mid,
                'D_steam_preheater': ph_results.D_steam_preheater,
                'K_preheater': ph_results.K_preheater
            },
            'pumps': {
                'feed': {
                    'Q_vol': pump_feed.Q_vol,
                    'H_pump': pump_feed.H_pump,
                    'N_hydr': pump_feed.N_hydr,
                    'type': pump_feed.type
                },
                'product': {
                    'Q_vol': pump_product.Q_vol,
                    'H_pump': pump_product.H_pump,
                    'N_hydr': pump_product.N_hydr,
                    'type': pump_product.type
                }
            },
            'pipelines': {
                'steam': steam_line,
                'solution': solution_line
            },
            'thermal': {
                'Q_total': Q_total / 1000,
                'Q_loss': Q_loss / 1000,
                'efficiency': efficiency
            }
        }

        plots = generate_plots(results, bc_results, vp_results)

        return render_template('results.html',
                               results=results,
                               input_data=data,
                               aux_results=session['aux_results'],
                               plots=plots)

    except ValueError as e:
        return render_template('index.html',
                               error=f"Ошибка формата данных: {str(e)}",
                               form_data=request.form)
    except Exception as e:
        return render_template('index.html',
                               error=f"Ошибка расчёта: {str(e)}",
                               form_data=request.form)


@app.route('/methodology')
def methodology():
    """Страница с методикой расчёта и описанием установки"""
    installation_info = {
        'name': 'Трёхкорпусная вакуум-выпарная установка непрерывного действия',
        'type_direct': 'Прямоточная схема (1-2-3)',
        'type_mixed': 'Смешанная схема (2-3-1)',
        'description': '''
            Установка предназначена для концентрирования водных растворов 
            методом выпаривания. Процесс осуществляется в трёх последовательно 
            соединённых корпусах выпарных аппаратов. Обогрев осуществляется 
            насыщенным водяным паром, вакуум создаётся в барометрическом 
            конденсаторе смешения.
        ''',
        'advantages': [
            'Экономия греющего пара за счёт использования вторичного пара',
            'Снижение тепловых потерь',
            'Возможность работы под вакуумом',
            'Непрерывность процесса'
        ]
    }

    symbols = {
        'c': 'удельная теплоёмкость, Дж/кг∙К',
        'd': 'диаметр, м',
        'D': 'расход греющего пара, кг/с',
        'F': 'поверхность теплопередачи, м²',
        'G': 'расход выпариваемого раствора, кг/с',
        'g': 'ускорение свободного падения, м/с²',
        'H': 'высота, м',
        'i, J': 'удельная энтальпия жидкости и пара, Дж/кг',
        'K': 'коэффициент теплопередачи, Вт/(м²·К)',
        'P': 'давление, Па',
        'Q': 'тепловая нагрузка, Вт',
        'q': 'удельная тепловая нагрузка, Вт/м²',
        'r': 'скрытая теплота парообразования, Дж/кг',
        't, T': 'температура, °C, K',
        'w': 'скорость, м/с',
        'W': 'производительность по испаряемой воде, кг/с',
        'x': 'концентрация, масс. %',
        'α': 'коэффициент теплоотдачи, Вт/(м²·К)',
        'λ': 'коэффициент теплопроводности, Вт/(м·К)',
        'μ': 'динамический коэффициент вязкости, Па·с',
        'ρ': 'плотность, кг/м³',
        'σ': 'поверхностное натяжение, Н/м',
        'Re': 'критерий Рейнольдса',
        'Nu': 'критерий Нуссельта',
        'Pr': 'критерий Прандтля'
    }

    indices = {
        '11, 21, 31': 'вход в i-тый выпарной аппарат',
        '12, 22, 32': 'выход из соответствующего аппарата',
        'в': 'вода',
        'г': 'греющий пар',
        'вп': 'выпарной пар',
        'к': 'конечный параметр',
        'н': 'начальный параметр',
        'ср': 'среднее значение',
        'ст': 'стенка'
    }

    equipment = {
        '1': ' сборник исходного раствора',
        '2,10': ' центробежные насосы',
        '3': ' подогреватель раствора',
        '4,5,6': ' корпуса выпарных аппаратов',
        '7': ' барометрический конденсатор, барометрическая труба и гидрозатвор',
        '8': ' ловушка для неконденсируемых газов',
        '9': ' вакуум-насос',
        '11': ' сборник упаренного раствора',
        '12': ' конденсатоотводчики'
    }

    return render_template('methodology.html',
                           installation_info=installation_info,
                           symbols=symbols,
                           indices=indices,
                           equipment=equipment)


@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    """API для полного расчёта"""
    try:
        data = request.get_json()

        required_fields = ['G_n', 'x_n', 'x_k', 't_n', 'P_gp', 'P_bc', 'delta_p']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Отсутствует поле {field}'}), 400

        input_data = EvaporatorInputData(
            G_n=float(data.get('G_n')),
            x_n=float(data.get('x_n')),
            x_k=float(data.get('x_k')),
            t_n=float(data.get('t_n')),
            P_gp=float(data.get('P_gp')),
            P_bc=float(data.get('P_bc')),
            delta_p=float(data.get('delta_p')),
            t_cold_water=float(data.get('t_cold_water', 20)),
            steam_fraction_to_bc=float(data.get('steam_fraction_to_bc', 0.15))
        )

        calculator = EvaporatorCalculator(input_data)
        results = calculator.run_calculation()

        aux_calc = AuxiliaryEquipmentCalculator(results, input_data)
        bc_results = aux_calc.calculate_barometric_condenser()
        vp_results = aux_calc.calculate_vacuum_pump()

        response = {
            'success': True,
            'results': {
                'pressure': results.P,
                'temperature': results.t,
                'concentration': results.x,
                'water_evaporated': results.W,
                'solution_flow': results.G,
                'heat_load': results.Q,
                'heat_transfer_coef': results.K,
                'area': results.F,
                'delta_t': results.delta_t,
                'total_water': results.W_total,
                'steam_consumption': results.D_gp,
                'specific_steam': results.ud_par
            },
            'auxiliary': {
                'cooling_water': bc_results.G_cooling_water,
                'condenser_diameter': bc_results.D_cond,
                'barometric_height': bc_results.H_barometric,
                'vacuum_pump_capacity': vp_results.V_air_min,
                'air_flow': vp_results.G_air
            }
        }
        return jsonify(response)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/material-balance', methods=['POST'])
def api_material_balance():
    """API для расчёта материального баланса"""
    try:
        data = request.get_json()
        G_n = float(data.get('G_n', 5.0))
        x_n = float(data.get('x_n', 0.05))
        x_k = float(data.get('x_k', 0.25))

        balance = MaterialBalance.calculate_material_balance(G_n, x_n, x_k)

        return jsonify({'success': True, 'balance': balance})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/auxiliary', methods=['POST'])
def api_auxiliary():
    """API для расчёта вспомогательного оборудования"""
    try:
        data = request.get_json()

        class DummyResults:
            pass

        dummy = DummyResults()
        dummy.W = [0, 0, float(data.get('W3', 1.0))]
        dummy.t = [0, 0, float(data.get('t_steam', 60))]
        dummy.depression = [0, 0, 0]
        dummy.P = [0, 0, float(data.get('P_bc', 0.02))]
        dummy.r = [0, 0, float(data.get('r_steam', 2350))]

        input_data = EvaporatorInputData(
            G_n=5.0,
            x_n=0.05,
            x_k=0.25,
            t_n=80,
            P_gp=0.4,
            P_bc=float(data.get('P_bc', 0.02)),
            delta_p=0.01,
            t_cold_water=float(data.get('t_cold_water', 20)),
            steam_fraction_to_bc=float(data.get('steam_fraction', 0.15))
        )

        aux_calc = AuxiliaryEquipmentCalculator(dummy, input_data)
        bc_results = aux_calc.calculate_barometric_condenser()
        vp_results = aux_calc.calculate_vacuum_pump()

        return jsonify({
            'success': True,
            'barometric_condenser': {
                'G_cooling_water': bc_results.G_cooling_water,
                'D_cond': bc_results.D_cond,
                'H_barometric': bc_results.H_barometric,
                't_out': bc_results.t_out
            },
            'vacuum_pump': {
                'V_air_min': vp_results.V_air_min,
                'G_air': vp_results.G_air
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/export-csv')
def export_csv():
    """Экспорт результатов в CSV"""
    try:
        results = session.get('results')
        aux_results = session.get('aux_results', {})

        if not results:
            return redirect(url_for('index'))

        import csv
        from io import StringIO

        si = StringIO()
        cw = csv.writer(si, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        cw.writerow(['=' * 80])
        cw.writerow(['ТРЁХКОРПУСНАЯ ВЫПАРНАЯ УСТАНОВКА - РЕЗУЛЬТАТЫ РАСЧЁТА'])
        cw.writerow(['=' * 80])
        cw.writerow([])

        cw.writerow(['ОСНОВНЫЕ ПАРАМЕТРЫ ПО КОРПУСАМ'])
        cw.writerow(['-' * 80])
        cw.writerow(['Параметр', 'Корпус 1', 'Корпус 2', 'Корпус 3', 'Единица измерения'])
        cw.writerow(['Давление P', results['P'][0], results['P'][1], results['P'][2], 'МПа'])
        cw.writerow(['Температура t', results['t'][0], results['t'][1], results['t'][2], '°C'])
        cw.writerow(['Концентрация x', results['x'][0], results['x'][1], results['x'][2], 'масс. доли'])
        cw.writerow(['Расход G', results['G'][0], results['G'][1], results['G'][2], 'кг/с'])
        cw.writerow(['Выпарено W', results['W'][0], results['W'][1], results['W'][2], 'кг/с'])
        cw.writerow(['Тепловая нагрузка Q', results['Q'][0], results['Q'][1], results['Q'][2], 'кВт'])
        cw.writerow(['Коэф. теплопередачи K', results['K'][0], results['K'][1], results['K'][2], 'Вт/(м²·К)'])
        cw.writerow(['Площадь F', results['F'][0], results['F'][1], results['F'][2], 'м²'])
        cw.writerow(['Температурный напор Δt', results['delta_t'][0], results['delta_t'][1], results['delta_t'][2], '°C'])
        cw.writerow(['Плотность ρ', results['rho'][0], results['rho'][1], results['rho'][2], 'кг/м³'])
        cw.writerow(['Вязкость μ', results['mu'][0], results['mu'][1], results['mu'][2], 'Па·с'])
        cw.writerow(['Теплоёмкость cp', results['cp'][0], results['cp'][1], results['cp'][2], 'кДж/(кг·К)'])
        cw.writerow(['Теплопроводность λ', results['lam'][0], results['lam'][1], results['lam'][2], 'Вт/(м·К)'])
        cw.writerow(['Температурная депрессия Δ', results['depression'][0], results['depression'][1], results['depression'][2], '°C'])
        cw.writerow([])

        cw.writerow(['ИТОГОВЫЕ ПОКАЗАТЕЛИ'])
        cw.writerow(['-' * 80])
        cw.writerow(['Общее количество выпаренной воды', f"{results['W_total']} кг/с", f"{results['W_total'] * 3600} кг/ч"])
        cw.writerow(['Расход греющего пара', f"{results['D_gp']} кг/с", f"{results['D_gp'] * 3600} кг/ч"])
        cw.writerow(['Удельный расход пара', f"{results['ud_par']} кг/кг", '-'])
        cw.writerow([])

        if aux_results:
            cw.writerow(['ВСПОМОГАТЕЛЬНОЕ ОБОРУДОВАНИЕ'])
            cw.writerow(['-' * 80])

            bc = aux_results.get('bc', {})
            cw.writerow(['Барометрический конденсатор'])
            cw.writerow(['Расход охлаждающей воды', f"{bc.get('G_cooling_water', 0)} кг/с", f"{bc.get('G_cooling_water', 0) * 3600} кг/ч"])
            cw.writerow(['Диаметр конденсатора', f"{bc.get('D_cond', 0)} м", f"{bc.get('D_cond', 0) * 1000} мм"])
            cw.writerow(['Высота барометрической трубы', f"{bc.get('H_barometric', 0)} м", '-'])
            cw.writerow(['Скорость воды в трубе', f"{bc.get('w_water', 0)} м/с", '-'])
            cw.writerow(['Конечная температура смеси', f"{bc.get('t_out', 0)} °C", '-'])
            cw.writerow([])

            vp = aux_results.get('vp', {})
            cw.writerow(['Вакуум-насос'])
            cw.writerow(['Производительность', f"{vp.get('V_air_min', 0)} м³/мин", f"{vp.get('V_air', 0)} м³/с"])
            cw.writerow(['Массовый расход воздуха', f"{vp.get('G_air', 0)} кг/с", '-'])
            cw.writerow(['Остаточное давление', f"{vp.get('residual_pressure', 0)} Па", f"{vp.get('residual_pressure', 0) / 1000} кПа"])
            cw.writerow([])

            ph = aux_results.get('ph', {})
            cw.writerow(['Предварительный теплообменник'])
            cw.writerow(['Площадь поверхности', f"{ph.get('F_preheater', 0)} м²", '-'])
            cw.writerow(['Коэффициент теплопередачи', f"{ph.get('K_preheater', 0)} Вт/(м²·К)", '-'])
            cw.writerow(['Расход греющего пара', f"{ph.get('D_steam_preheater', 0)} кг/с", '-'])
            cw.writerow(['Средняя разность температур', f"{ph.get('delta_t_mid', 0)} °C", '-'])
            cw.writerow([])

            pumps = aux_results.get('pumps', {})
            cw.writerow(['Насосное оборудование'])
            feed = pumps.get('feed', {})
            cw.writerow(['Насос подачи раствора'])
            cw.writerow(['Производительность', f"{feed.get('Q_vol', 0)} м³/с", f"{feed.get('Q_vol', 0) * 1000} л/с"])
            cw.writerow(['Напор', f"{feed.get('H_pump', 0)} м вод. ст.", '-'])
            cw.writerow(['Гидравлическая мощность', f"{feed.get('N_hydr', 0)} кВт", '-'])
            cw.writerow(['Рекомендуемый тип', feed.get('type', '-'), '-'])
            cw.writerow([])

            product = pumps.get('product', {})
            cw.writerow(['Насос отвода упаренного раствора'])
            cw.writerow(['Производительность', f"{product.get('Q_vol', 0)} м³/с", f"{product.get('Q_vol', 0) * 1000} л/с"])
            cw.writerow(['Напор', f"{product.get('H_pump', 0)} м вод. ст.", '-'])
            cw.writerow(['Гидравлическая мощность', f"{product.get('N_hydr', 0)} кВт", '-'])
            cw.writerow(['Рекомендуемый тип', product.get('type', '-'), '-'])

        cw.writerow([])
        cw.writerow(['=' * 80])
        cw.writerow(['Дата расчёта:', datetime.now().strftime('%d.%m.%Y %H:%M:%S')])
        cw.writerow(['=' * 80])

        output = si.getvalue()

        from flask import make_response
        response = make_response(output)
        response.headers["Content-Disposition"] = "attachment; filename=evaporator_results.csv"
        response.headers["Content-type"] = "text/csv; charset=utf-8-sig"
        return response

    except Exception as e:
        return f"Ошибка экспорта: {str(e)}", 400


def generate_plots(results, bc_results=None, vp_results=None):
    """Генерация графиков для визуализации результатов"""
    plots = {}
    corps = ['Корпус 1', 'Корпус 2', 'Корпус 3']

    plt.style.use('seaborn-v0_8-darkgrid')

    # 1. График температур и концентраций
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.subplots_adjust(wspace=0.3)

    bars1 = ax1.bar(corps, results.t, color='#3498db', edgecolor='#2c3e50',
                    linewidth=1.5, alpha=0.8, width=0.6)
    ax1.set_ylabel('Температура, °C', fontsize=12, fontweight='bold')
    ax1.set_title('Распределение температур по корпусам', fontsize=14, fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax1.set_ylim([0, max(results.t) * 1.15 if max(results.t) > 0 else 100])

    for bar, val in zip(bars1, results.t):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(results.t) * 0.02,
                 f'{val:.1f}°C', ha='center', va='bottom', fontsize=10, fontweight='bold')

    bars2 = ax2.bar(corps, results.x, color='#e74c3c', edgecolor='#2c3e50',
                    linewidth=1.5, alpha=0.8, width=0.6)
    ax2.set_ylabel('Концентрация, масс. доли', fontsize=12, fontweight='bold')
    ax2.set_title('Распределение концентраций по корпусам', fontsize=14, fontweight='bold', pad=15)
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax2.set_ylim([0, max(results.x) * 1.15 if max(results.x) > 0 else 0.5])

    for bar, val in zip(bars2, results.x):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(results.x) * 0.02,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    img.seek(0)
    plots['temp_conc'] = base64.b64encode(img.getvalue()).decode()
    plt.close()

    # 2. График тепловых нагрузок
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(corps, results.Q, color='#2ecc71', edgecolor='#27ae60',
                  linewidth=1.5, alpha=0.8, width=0.6)
    ax.set_ylabel('Тепловая нагрузка, кВт', fontsize=12, fontweight='bold')
    ax.set_title('Тепловые нагрузки по корпусам', fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.set_ylim([0, max(results.Q) * 1.15 if max(results.Q) > 0 else 1000])

    for bar, val in zip(bars, results.Q):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(results.Q) * 0.02,
                f'{val:.1f} кВт', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    img.seek(0)
    plots['heat_load'] = base64.b64encode(img.getvalue()).decode()
    plt.close()

    # 3. График коэффициентов теплопередачи
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(corps, results.K, color='#f39c12', edgecolor='#e67e22',
                  linewidth=1.5, alpha=0.8, width=0.6)
    ax.set_ylabel('Коэффициент теплопередачи, Вт/(м²·К)', fontsize=12, fontweight='bold')
    ax.set_title('Коэффициенты теплопередачи по корпусам', fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.set_ylim([0, max(results.K) * 1.15 if max(results.K) > 0 else 1500])

    for bar, val in zip(bars, results.K):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(results.K) * 0.02,
                f'{val:.0f} Вт/(м²·К)', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    img.seek(0)
    plots['k_coef'] = base64.b64encode(img.getvalue()).decode()
    plt.close()

    # 4. Круговая диаграмма
    fig, ax = plt.subplots(figsize=(8, 8))
    colors = ['#3498db', '#2ecc71', '#e74c3c']
    if sum(results.W) > 0:
        wedges, texts, autotexts = ax.pie(results.W, labels=corps, colors=colors,
                                          autopct='%1.1f%%', startangle=90,
                                          textprops={'fontsize': 12, 'fontweight': 'bold'},
                                          wedgeprops={'edgecolor': 'white', 'linewidth': 2})
        ax.set_title('Распределение выпаренной воды по корпусам',
                     fontsize=14, fontweight='bold', pad=20)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(11)
            autotext.set_fontweight('bold')
        for text in texts:
            text.set_fontsize(11)
            text.set_fontweight('bold')

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    img.seek(0)
    plots['pie'] = base64.b64encode(img.getvalue()).decode()
    plt.close()

    # 5. График свойств
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    fig.subplots_adjust(hspace=0.3, wspace=0.3)

    ax1.plot(corps, results.rho, 'o-', color='#3498db', linewidth=2.5,
             markersize=10, markerfacecolor='white', markeredgewidth=2)
    ax1.set_ylabel('Плотность, кг/м³', fontsize=11, fontweight='bold')
    ax1.set_title('Плотность раствора по корпусам', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xlim([-0.5, 2.5])

    ax2.plot(corps, [m * 1e3 for m in results.mu], 'o-', color='#e74c3c',
             linewidth=2.5, markersize=10, markerfacecolor='white', markeredgewidth=2)
    ax2.set_ylabel('Вязкость, мПа·с', fontsize=11, fontweight='bold')
    ax2.set_title('Вязкость раствора по корпусам', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_xlim([-0.5, 2.5])

    ax3.plot(corps, results.cp, 'o-', color='#2ecc71', linewidth=2.5,
             markersize=10, markerfacecolor='white', markeredgewidth=2)
    ax3.set_ylabel('Теплоёмкость, кДж/(кг·К)', fontsize=11, fontweight='bold')
    ax3.set_title('Теплоёмкость раствора по корпусам', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, linestyle='--')
    ax3.set_xlim([-0.5, 2.5])

    ax4.plot(corps, results.lam, 'o-', color='#f39c12', linewidth=2.5,
             markersize=10, markerfacecolor='white', markeredgewidth=2)
    ax4.set_ylabel('Теплопроводность, Вт/(м·К)', fontsize=11, fontweight='bold')
    ax4.set_title('Теплопроводность раствора по корпусам', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, linestyle='--')
    ax4.set_xlim([-0.5, 2.5])

    for ax, data in [(ax1, results.rho), (ax2, [m * 1e3 for m in results.mu]),
                     (ax3, results.cp), (ax4, results.lam)]:
        for i, (x, y) in enumerate(zip(corps, data)):
            ax.annotate(f'{y:.2f}', (x, y), xytext=(0, 10),
                        textcoords='offset points', ha='center', fontsize=9,
                        fontweight='bold', bbox=dict(boxstyle='round,pad=0.3',
                                                     facecolor='white', alpha=0.8))

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    img.seek(0)
    plots['properties'] = base64.b64encode(img.getvalue()).decode()
    plt.close()

    # 6. График расходов
    fig, ax = plt.subplots(figsize=(10, 6))
    x_pos = np.arange(len(corps))
    width = 0.35

    bars1 = ax.bar(x_pos - width / 2, results.G, width, label='Расход раствора',
                   color='#3498db', edgecolor='#2c3e50', linewidth=1.5, alpha=0.8)
    bars2 = ax.bar(x_pos + width / 2, results.W, width, label='Выпарено воды',
                   color='#e74c3c', edgecolor='#2c3e50', linewidth=1.5, alpha=0.8)

    ax.set_ylabel('Расход, кг/с', fontsize=12, fontweight='bold')
    ax.set_title('Расходы раствора и выпаренной воды по корпусам',
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(corps)
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')

    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + max(results.G + results.W) * 0.02,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    img.seek(0)
    plots['flows'] = base64.b64encode(img.getvalue()).decode()
    plt.close()

    return plots


@app.context_processor
def utility_processor():
    def format_number(value, decimals=2):
        try:
            if value is None:
                return "0.00"
            return f"{value:.{decimals}f}"
        except:
            return str(value)

    def get_current_year():
        return datetime.now().year

    def format_flow(value):
        if value < 0.001:
            return f"{value * 1e6:.2f} г/с"
        elif value < 1:
            return f"{value * 1000:.2f} г/с"
        else:
            return f"{value:.2f} кг/с"

    return dict(
        format_number=format_number,
        current_year=get_current_year,
        format_flow=format_flow
    )


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500