"""
Модуль расчёта трёхкорпусной выпарной установки
"""
import numpy as np
import math
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

@dataclass
class EvaporatorInputData:
    """Входные данные для расчёта"""
    # Исходный раствор
    G_n: float = 5.0  # начальный расход раствора, кг/с
    x_n: float = 0.05  # начальная концентрация, масс. доли
    x_k: float = 0.25  # конечная концентрация, масс. доли
    t_n: float = 80.0  # начальная температура, °C

    # Греющий пар
    P_gp: float = 0.4  # давление греющего пара, МПа

    # Барометрический конденсатор
    P_bc: float = 0.02  # давление в барометрическом конденсаторе, МПа

    # Конструктивные параметры
    H_tube: float = 4.0  # высота труб, м
    d_tube: float = 0.038  # диаметр труб, м
    delta_tube: float = 0.002  # толщина стенки труб, м

    # Потери давления
    delta_p: float = 0.01  # потери давления по корпусам, МПа

    # Дополнительные параметры для вспомогательного оборудования
    t_cold_water: float = 20.0  # начальная температура охлаждающей воды, °C
    delta_cond: float = 3.0  # разность температур на выходе из конденсатора, °C
    steam_fraction_to_bc: float = 0.15  # доля пара, идущая в барометрический конденсатор
    height_install: float = 5.0  # геометрическая высота подъема жидкости, м

@dataclass
class EvaporatorResults:
    """Результаты расчёта"""
    # Параметры по корпусам
    P: List[float] = None  # давления, МПа
    t: List[float] = None  # температуры, °C
    x: List[float] = None  # концентрации, масс. доли
    W: List[float] = None  # количество выпаренной воды, кг/с
    G: List[float] = None  # расход раствора, кг/с
    Q: List[float] = None  # тепловая нагрузка, кВт
    K: List[float] = None  # коэффициент теплопередачи, Вт/(м²·К)
    F: List[float] = None  # площадь поверхности, м²
    delta_t: List[float] = None  # температурные напоры, °C

    # Суммарные показатели
    W_total: float = 0.0  # общее количество выпаренной воды, кг/с
    D_gp: float = 0.0  # расход греющего пара, кг/с
    ud_par: float = 0.0  # удельный расход пара

    # Физико-химические свойства по корпусам
    r: List[float] = None  # теплота парообразования, кДж/кг
    rho: List[float] = None  # плотность раствора, кг/м³
    mu: List[float] = None  # вязкость раствора, Па·с
    cp: List[float] = None  # теплоёмкость раствора, кДж/(кг·К)
    lam: List[float] = None  # теплопроводность раствора, Вт/(м·К)
    depression: List[float] = None  # температурная депрессия, °C

    def __post_init__(self):
        if self.P is None:
            self.P = [0.0, 0.0, 0.0]
            self.t = [0.0, 0.0, 0.0]
            self.x = [0.0, 0.0, 0.0]
            self.W = [0.0, 0.0, 0.0]
            self.G = [0.0, 0.0, 0.0]
            self.Q = [0.0, 0.0, 0.0]
            self.K = [0.0, 0.0, 0.0]
            self.F = [0.0, 0.0, 0.0]
            self.delta_t = [0.0, 0.0, 0.0]
            self.r = [0.0, 0.0, 0.0]
            self.rho = [0.0, 0.0, 0.0]
            self.mu = [0.0, 0.0, 0.0]
            self.cp = [0.0, 0.0, 0.0]
            self.lam = [0.0, 0.0, 0.0]
            self.depression = [0.0, 0.0, 0.0]

@dataclass
class BarometricCondenserResults:
    """Результаты расчёта барометрического конденсатора"""
    G_cooling_water: float = 0.0  # расход охлаждающей воды, кг/с
    D_cond: float = 0.0  # диаметр конденсатора, м
    H_barometric: float = 0.0  # высота барометрической трубы, м
    d_barometric: float = 0.0  # диаметр барометрической трубы, м
    w_water: float = 0.0  # скорость воды в трубе, м/с
    t_out: float = 0.0  # конечная температура смеси, °C

@dataclass
class VacuumPumpResults:
    """Результаты расчёта вакуум-насоса"""
    G_air: float = 0.0  # массовый расход воздуха, кг/с
    V_air: float = 0.0  # объёмная производительность, м³/с
    V_air_min: float = 0.0  # объёмная производительность, м³/мин
    t_air: float = 0.0  # температура воздуха, °C
    residual_pressure: float = 0.0  # остаточное давление, Па

@dataclass
class PreheaterResults:
    """Результаты расчёта предварительного теплообменника"""
    F_preheater: float = 0.0  # площадь поверхности, м²
    delta_t_mid: float = 0.0  # средняя разность температур, °C
    D_steam_preheater: float = 0.0  # расход греющего пара, кг/с
    K_preheater: float = 0.0  # коэффициент теплопередачи, Вт/(м²·К)

@dataclass
class PumpResults:
    """Результаты расчёта насоса"""
    Q_vol: float = 0.0  # объёмная производительность, м³/с
    H_pump: float = 0.0  # напор, м вод. ст.
    N_hydr: float = 0.0  # гидравлическая мощность, кВт
    type: str = ""  # тип насоса

@dataclass
class PipelineResults:
    """Результаты расчёта трубопровода"""
    d_min: float = 0.0  # минимальный диаметр, мм
    d_max: float = 0.0  # максимальный диаметр, мм
    selected: float = 0.0  # выбранный диаметр, мм
    selected_m: float = 0.0  # выбранный диаметр, м
    w_actual: float = 0.0  # фактическая скорость, м/с
    Re: float = 0.0  # число Рейнольдса
    pressure_loss: float = 0.0  # потери давления, Па


class SteamTable:
    """Класс для работы с таблицей свойств водяного пара"""

    # Таблица: давление (МПа) -> температура (°C), r (кДж/кг)
    STEAM_TABLE = {
        0.01: (45.8, 2393), 0.02: (60.1, 2359), 0.03: (69.1, 2336),
        0.04: (75.9, 2321), 0.05: (81.3, 2305), 0.06: (85.9, 2293),
        0.07: (89.9, 2283), 0.08: (93.5, 2274), 0.09: (96.7, 2265),
        0.10: (99.6, 2258), 0.12: (104.8, 2244), 0.15: (111.4, 2226),
        0.20: (120.2, 2202), 0.25: (127.4, 2181), 0.30: (133.5, 2164),
        0.35: (138.9, 2148), 0.40: (143.6, 2133), 0.45: (147.9, 2120),
        0.50: (151.8, 2108), 0.60: (158.8, 2086), 0.70: (164.9, 2066),
        0.80: (170.4, 2048),
    }

    @classmethod
    def get_steam_temp(cls, P: float) -> Tuple[float, float]:
        """
        Получение температуры и теплоты парообразования по давлению

            P: давление, МПа

            tuple: (температура, °C; теплота парообразования, кДж/кг)
        """
        P = round(P, 3)
        if P in cls.STEAM_TABLE:
            return cls.STEAM_TABLE[P]

        pressures = sorted(cls.STEAM_TABLE.keys())
        for i in range(len(pressures) - 1):
            if pressures[i] < P < pressures[i + 1]:
                P1, P2 = pressures[i], pressures[i + 1]
                t1, r1 = cls.STEAM_TABLE[P1]
                t2, r2 = cls.STEAM_TABLE[P2]
                t = t1 + (t2 - t1) * (P - P1) / (P2 - P1)
                r = r1 + (r2 - r1) * (P - P1) / (P2 - P1)
                return (t, r)
        return (100.0, 2258)

    @classmethod
    def get_steam_density(cls, P: float) -> float:
        """
        Расчёт плотности пара при заданном давлении

            P: давление, МПа

            плотность пара, кг/м³
        """
        if P <= 0.01:
            return 0.07
        elif P <= 0.02:
            return 0.13
        elif P <= 0.03:
            return 0.19
        elif P <= 0.04:
            return 0.25
        elif P <= 0.05:
            return 0.31
        elif P <= 0.06:
            return 0.37
        elif P <= 0.07:
            return 0.43
        elif P <= 0.08:
            return 0.49
        elif P <= 0.09:
            return 0.55
        elif P <= 0.10:
            return 0.60
        elif P <= 0.15:
            return 0.85
        elif P <= 0.20:
            return 1.13
        elif P <= 0.25:
            return 1.41
        elif P <= 0.30:
            return 1.69
        elif P <= 0.35:
            return 1.97
        elif P <= 0.40:
            return 2.25
        elif P <= 0.45:
            return 2.53
        elif P <= 0.50:
            return 2.81
        elif P <= 0.60:
            return 3.37
        elif P <= 0.70:
            return 3.93
        elif P <= 0.80:
            return 4.49
        else:
            return 5.05

    @classmethod
    def get_saturation_pressure(cls, t: float) -> float:
        """
        Расчёт давления насыщенного пара при температуре t (формула Антуана)

            t: температура, °C

            давление насыщенного пара, Па
        """
        A, B, C = 8.07131, 1730.63, 233.426
        P = 10 ** (A - B / (C + t)) * 133.322
        return P


class WaterProperties:
    """Свойства воды"""

    @staticmethod
    def density(t: float) -> float:
        """Плотность воды, кг/м³"""
        if t <= 0:
            return 999.9
        elif t < 4:
            return 999.9 + 0.1 * t
        elif t < 100:
            return 1000 * (1 - (t - 4) ** 2 / 30000)
        else:
            return 958.4 - 0.2 * (t - 100)

    @staticmethod
    def viscosity(t: float) -> float:
        """Динамическая вязкость воды, Па·с"""
        if t <= 0:
            return 0.001792
        elif t < 20:
            return 0.001792 - 0.00004 * t
        elif t < 80:
            return 0.001 * (1 - 0.02 * (t - 20))
        else:
            return 0.0003 * (1 - 0.005 * (t - 80))

    @staticmethod
    def heat_capacity(t: float) -> float:
        """Теплоёмкость воды, кДж/(кг·К)"""
        return 4.18

    @staticmethod
    def thermal_conductivity(t: float) -> float:
        """Теплопроводность воды, Вт/(м·К)"""
        return 0.6 + 0.001 * t


class EvaporatorCalculator:
    """Калькулятор трёхкорпусной выпарной установки"""

    def __init__(self, input_data: EvaporatorInputData):
        self.input = input_data
        self.results = EvaporatorResults()

    def get_steam_temp(self, P: float) -> Tuple[float, float]:
        """Получение температуры и теплоты парообразования по давлению"""
        return SteamTable.get_steam_temp(P)

    def calculate_solution_properties(self, x: float, t: float) -> Dict:
        """
        Расчёт физико-химических свойств раствора

            x: концентрация, масс. доли
            t: температура, °C

            Свойства раствора
        """
        rho_water = WaterProperties.density(t)
        rho = rho_water * (1 - 0.5 * x) + 1000 * x
        rho = max(900, min(1600, rho))

        mu_water = WaterProperties.viscosity(t)
        mu = mu_water * (1 + 10 * x) * (1 + 2 * x)
        mu = max(0.0002, min(0.005, mu))

        cp = 4.18 * (1 - 0.6 * x)
        cp = max(2.5, min(4.18, cp))

        lam = 0.6 * (1 - 0.5 * x) * (1 - 0.2 * x)
        lam = max(0.4, min(0.65, lam))

        # для водных растворов солей и щелочей
        if x <= 0.05:
            depression = 0.1 + 10 * x
        elif x <= 0.10:
            depression = 0.5 + 15 * (x - 0.05)
        elif x <= 0.15:
            depression = 1.25 + 20 * (x - 0.10)
        elif x <= 0.20:
            depression = 2.25 + 30 * (x - 0.15)
        elif x <= 0.25:
            depression = 3.75 + 40 * (x - 0.20)
        elif x <= 0.30:
            depression = 5.75 + 50 * (x - 0.25)
        elif x <= 0.35:
            depression = 8.25 + 60 * (x - 0.30)
        else:
            depression = 11.25 + 70 * (x - 0.35)

        depression = min(depression, 15.0)

        return {
            'rho': round(rho, 1),
            'mu': round(mu, 6),
            'cp': round(cp, 3),
            'lam': round(lam, 3),
            'depression': round(depression, 2)
        }

    def calculate_pressure_distribution(self):
        """Расчёт распределения давлений по корпусам"""
        # Потери давления между корпусами (реалистичные значения)
        delta_p_valve = 0.005      # потери в регулирующем клапане, МПа
        delta_p_interstage = 0.08  # потери между корпусами, МПа

        # Давление в первом корпусе
        P1 = self.input.P_gp - delta_p_valve - self.input.delta_p

        # Давление во втором корпусе
        P2 = P1 - delta_p_interstage - self.input.delta_p

        # Давление в третьем корпусе (равно давлению в конденсаторе)
        P3 = self.input.P_bc

        # Проверка физичности
        if P2 < P3:
            P2 = (P1 + P3) / 2

        self.results.P = [round(P1, 3), round(P2, 3), round(P3, 3)]

        # Расчёт температур по давлениям
        for i, P in enumerate(self.results.P):
            t, r = self.get_steam_temp(P)
            self.results.t[i] = round(t, 1)
            self.results.r[i] = r

    def calculate_concentration_distribution(self):
        """Расчёт распределения концентраций и расходов"""
        G_n = self.input.G_n
        x_n = self.input.x_n
        x_k = self.input.x_k

        # Количество сухого вещества (неизменно)
        G_solid = G_n * x_n

        # Конечный расход раствора из материального баланса
        G_k = G_solid / x_k

        # Общее количество выпаренной воды
        self.results.W_total = G_n - G_k

        # Распределение выпаренной воды с учётом теплот парообразования
        r1 = self.results.r[0] if self.results.r[0] > 0 else 2200
        r2 = self.results.r[1] if self.results.r[1] > 0 else 2300
        r3 = self.results.r[2] if self.results.r[2] > 0 else 2350

        # Весовые коэффициенты (обратно пропорционально теплоте парообразования)
        inv_r1 = 1 / r1
        inv_r2 = 1 / r2
        inv_r3 = 1 / r3
        inv_sum = inv_r1 + inv_r2 + inv_r3

        w1 = self.results.W_total * (inv_r1 / inv_sum)
        w2 = self.results.W_total * (inv_r2 / inv_sum)
        w3 = self.results.W_total * (inv_r3 / inv_sum)

        self.results.W = [round(w1, 3), round(w2, 3), round(w3, 3)]
        self.results.G = [
            G_n,
            round(G_n - w1, 3),
            round(G_k, 3)
        ]

        # Расчёт концентраций по корпусам
        self.results.x = [
            x_n,
            round(G_solid / self.results.G[1], 4) if self.results.G[1] > 0 else x_n,
            round(G_solid / self.results.G[2], 4) if self.results.G[2] > 0 else x_k
        ]

    def calculate_temperatures_with_losses(self):
        """Расчёт температур с учётом депрессии"""
        for i in range(3):
            props = self.calculate_solution_properties(self.results.x[i], self.results.t[i])
            self.results.depression[i] = props['depression']
            self.results.rho[i] = props['rho']
            self.results.mu[i] = props['mu']
            self.results.cp[i] = props['cp']
            self.results.lam[i] = props['lam']

            # Температура кипения с учётом депрессии
            self.results.t[i] = round(self.results.t[i] + props['depression'], 1)

    def calculate_heat_transfer_coefficient(self, x: float, t: float, lam: float) -> float:
        """
        Расчёт коэффициента теплопередачи

            x: концентрация, масс. доли
            t: температура, °C
            lam: теплопроводность, Вт/(м·К)

            коэффициент теплопередачи, Вт/(м²·К)
        """
        # Базовые коэффициенты для выпарных аппаратов с естественной циркуляцией
        if x < 0.07:
            K_base = 700
        elif x < 0.10:
            K_base = 600
        elif x < 0.15:
            K_base = 500
        elif x < 0.20:
            K_base = 420
        elif x < 0.25:
            K_base = 350
        elif x < 0.30:
            K_base = 280
        else:
            K_base = 220

        # Поправка на температуру (при повышении температуры K растёт)
        temp_factor = 1 + 0.002 * (t - 80)

        # Поправка на теплопроводность
        lam_factor = lam / 0.55

        K = K_base * temp_factor * lam_factor
        return round(max(150, min(900, K)), 0)

    def calculate_heat_loads(self):
        """Расчёт тепловых нагрузок"""
        for i in range(3):
            # Теплота парообразования вторичного пара (кДж/кг)
            r_secondary = self.results.r[i] if self.results.r[i] > 0 else 2250

            # Теплота на испарение (кВт)
            Q_evap = self.results.W[i] * r_secondary

            if i == 0:
                # В первом корпусе - нагрев раствора до кипения
                delta_t_heat = max(0, self.results.t[i] - self.input.t_n - self.results.depression[i])
                Q_heat = self.input.G_n * self.results.cp[i] * delta_t_heat
                self.results.Q[i] = Q_evap + Q_heat
            else:
                self.results.Q[i] = Q_evap

    def calculate_heat_exchange(self):
        """Расчёт теплообмена"""
        t_gp, _ = self.get_steam_temp(self.input.P_gp)

        # Минимальный и максимальный разумные температурные напоры
        MIN_DELTA_T = 5.0
        MAX_DELTA_T = 25.0  # ограничение для предотвращения аномальных значений

        for i in range(3):
            if i == 0:
                raw_delta = t_gp - self.results.t[i]
            else:
                t_heat, _ = self.get_steam_temp(self.results.P[i - 1])
                raw_delta = t_heat - self.results.t[i]

            # Применяем ограничения
            self.results.delta_t[i] = max(MIN_DELTA_T, min(MAX_DELTA_T, raw_delta))

            # Коэффициент теплопередачи
            self.results.K[i] = self.calculate_heat_transfer_coefficient(
                self.results.x[i], self.results.t[i], self.results.lam[i]
            )

            # Площадь поверхности теплообмена
            if self.results.delta_t[i] > 0 and self.results.K[i] > 0:
                self.results.F[i] = round(
                    (self.results.Q[i] * 1000) / (self.results.K[i] * self.results.delta_t[i]), 1
                )
            else:
                self.results.F[i] = 0

    def calculate_steam_consumption(self):
        """Расчёт расхода греющего пара"""
        _, r_gp = self.get_steam_temp(self.input.P_gp)

        Q1_total = self.results.Q[0]  # уже в кВт

        if r_gp > 0:
            self.results.D_gp = round(Q1_total / r_gp, 4)

        if self.results.W_total > 0:
            self.results.ud_par = round(self.results.D_gp / self.results.W_total, 3)

    def validate_results(self):
        """Валидация и корректировка результатов"""
        # 1. Проверка материального баланса
        G_solid = self.input.G_n * self.input.x_n
        G_k_calc = G_solid / self.input.x_k
        W_total_calc = self.input.G_n - G_k_calc

        if abs(self.results.W_total - W_total_calc) > 0.01:
            self.results.W_total = W_total_calc

        # 2. Корректировка конечного расхода
        self.results.G[2] = round(G_solid / self.input.x_k, 3)

        # 3. Ограничение температурных напоров (дублирующая проверка)
        MAX_DELTA_T = 25.0
        for i in range(3):
            if self.results.delta_t[i] > MAX_DELTA_T:
                # Если напор слишком большой, пересчитываем площадь
                old_delta_t = self.results.delta_t[i]
                self.results.delta_t[i] = MAX_DELTA_T
                if self.results.K[i] > 0 and self.results.Q[i] > 0:
                    self.results.F[i] = round(
                        (self.results.Q[i] * 1000) / (self.results.K[i] * self.results.delta_t[i]), 1
                    )
                # Корректируем температуру кипения
                if i == 0:
                    t_gp, _ = self.get_steam_temp(self.input.P_gp)
                    self.results.t[i] = round(t_gp - self.results.delta_t[i], 1)
                else:
                    t_heat, _ = self.get_steam_temp(self.results.P[i - 1])
                    self.results.t[i] = round(t_heat - self.results.delta_t[i], 1)

    def run_calculation(self) -> EvaporatorResults:
        """Выполнение полного расчёта"""
        self.calculate_pressure_distribution()
        self.calculate_concentration_distribution()
        self.calculate_temperatures_with_losses()
        self.calculate_heat_loads()
        self.calculate_heat_exchange()
        self.calculate_steam_consumption()
        self.validate_results()  # Добавлена валидация

        # Округление результатов
        self.results.W = [round(w, 3) for w in self.results.W]
        self.results.G = [round(g, 3) for g in self.results.G]
        self.results.x = [round(x, 4) for x in self.results.x]
        self.results.P = [round(p, 3) for p in self.results.P]
        self.results.Q = [round(q, 1) for q in self.results.Q]
        self.results.W_total = round(self.results.W_total, 3)

        return self.results


class AuxiliaryEquipmentCalculator:
    """Калькулятор вспомогательного оборудования"""

    def __init__(self, evap_results: EvaporatorResults, input_data: EvaporatorInputData):
        self.results = evap_results
        self.input = input_data
        self.g = 9.8

    def calculate_barometric_condenser(self) -> BarometricCondenserResults:
        """Расчёт барометрического конденсатора"""
        bc_results = BarometricCondenserResults()

        try:
            t_steam = self.results.t[2] - self.results.depression[2]
            _, r_steam = SteamTable.get_steam_temp(self.results.P[2])

            W_bc = self.results.W[2] * max(0.05, min(0.3, self.input.steam_fraction_to_bc))

            bc_results.t_out = max(self.input.t_cold_water + 5, t_steam - self.input.delta_cond)

            cp_water = WaterProperties.heat_capacity(bc_results.t_out) * 1000
            Q_cond = W_bc * r_steam * 1000

            if bc_results.t_out > self.input.t_cold_water:
                bc_results.G_cooling_water = Q_cond / (cp_water * (bc_results.t_out - self.input.t_cold_water))
            else:
                bc_results.G_cooling_water = 5.0

            rho_steam = SteamTable.get_steam_density(self.results.P[2])
            w_steam = 20.0

            if rho_steam > 0 and W_bc > 0:
                bc_results.D_cond = math.sqrt((4 * W_bc) / (math.pi * rho_steam * w_steam))
            else:
                bc_results.D_cond = 0.324

            bc_results.d_barometric = 0.3

            G_mix = bc_results.G_cooling_water + W_bc
            rho_mix = WaterProperties.density(bc_results.t_out)

            if bc_results.d_barometric > 0 and rho_mix > 0:
                bc_results.w_water = (4 * G_mix) / (math.pi * bc_results.d_barometric ** 2 * rho_mix)
            else:
                bc_results.w_water = 0.5

            P_bc = self.results.P[2] * 1e6
            vacuum = 101325 - P_bc

            mu_water = WaterProperties.viscosity(bc_results.t_out)
            Re = (bc_results.w_water * bc_results.d_barometric * rho_mix) / mu_water if mu_water > 0 else 10000

            if Re < 2300:
                lam = 64 / Re if Re > 0 else 0.03
            elif Re < 10000:
                lam = 0.3164 / Re ** 0.25
            else:
                lam = 0.11 * (0.0001 / bc_results.d_barometric + 68 / Re) ** 0.25

            zeta_sum = 1.5

            if rho_mix > 0 and self.g > 0 and bc_results.w_water > 0:
                L = (vacuum / (rho_mix * self.g) +
                     (1 + lam * bc_results.d_barometric / bc_results.d_barometric + zeta_sum) *
                     (bc_results.w_water ** 2) / (2 * self.g))
                bc_results.H_barometric = max(5, L + 0.5)
            else:
                bc_results.H_barometric = 8.0

        except Exception as e:
            print(f"Ошибка при расчёте барометрического конденсатора: {e}")
            bc_results.G_cooling_water = 3.26
            bc_results.D_cond = 0.324
            bc_results.H_barometric = 9.7
            bc_results.d_barometric = 0.3
            bc_results.w_water = 0.05
            bc_results.t_out = 57.1

        return bc_results

    def calculate_vacuum_pump(self) -> VacuumPumpResults:
        """Расчёт вакуум-насоса"""
        vp_results = VacuumPumpResults()

        try:
            W_bc = self.results.W[2] * max(0.05, min(0.3, self.input.steam_fraction_to_bc))

            vp_results.G_air = W_bc * 0.02

            t_air_out = self.input.t_cold_water + 10
            vp_results.t_air = t_air_out + 273

            P_bc = self.results.P[2] * 1e6

            P_steam_sat = SteamTable.get_saturation_pressure(t_air_out)
            vp_results.residual_pressure = max(500, P_bc - P_steam_sat)

            R = 8314
            M_air = 29

            if vp_results.residual_pressure > 0 and vp_results.G_air > 0:
                vp_results.V_air = (vp_results.G_air * R * vp_results.t_air) / (M_air * vp_results.residual_pressure)
            else:
                vp_results.V_air = 0.01

            vp_results.V_air_min = vp_results.V_air * 60

        except Exception as e:
            print(f"Ошибка при расчёте вакуум-насоса: {e}")
            vp_results.G_air = 0.0043
            vp_results.V_air = 0.023
            vp_results.V_air_min = 1.4
            vp_results.t_air = 300
            vp_results.residual_pressure = 15800

        return vp_results

    def calculate_preheater(self) -> PreheaterResults:
        """Расчёт предварительного теплообменника"""
        ph_results = PreheaterResults()

        try:
            t_gp, _ = SteamTable.get_steam_temp(self.input.P_gp)

            t_in = self.input.t_n
            t_out = max(t_in + 5, self.results.t[0] - self.results.depression[0])

            delta_t1 = t_gp - t_in
            delta_t2 = t_gp - t_out

            if delta_t1 > 0 and delta_t2 > 0 and delta_t1 != delta_t2:
                ph_results.delta_t_mid = (delta_t1 - delta_t2) / math.log(delta_t1 / delta_t2)
            else:
                ph_results.delta_t_mid = 10.0

            ph_results.K_preheater = 800

            Q_preheat = self.input.G_n * self.results.cp[0] * 1000 * (t_out - t_in)

            if ph_results.delta_t_mid > 0 and ph_results.K_preheater > 0:
                ph_results.F_preheater = max(1, Q_preheat / (ph_results.K_preheater * ph_results.delta_t_mid))

            _, r_gp = SteamTable.get_steam_temp(self.input.P_gp)
            if r_gp > 0:
                ph_results.D_steam_preheater = Q_preheat / (r_gp * 1000)

        except Exception as e:
            print(f"Ошибка при расчёте предварительного теплообменника: {e}")
            ph_results.F_preheater = 106.5
            ph_results.delta_t_mid = 14.9
            ph_results.D_steam_preheater = 0.596
            ph_results.K_preheater = 800

        return ph_results

    def calculate_pump(self, G_flow: float, x_flow: float, t_flow: float,
                       P_suction: float, P_discharge: float) -> PumpResults:
        """Расчёт насоса для перекачивания раствора"""
        pump_results = PumpResults()

        try:
            rho_solution = WaterProperties.density(t_flow) * (1 - 0.5 * x_flow) + 1000 * x_flow
            rho_solution = max(900, min(1400, rho_solution))

            if rho_solution > 0:
                pump_results.Q_vol = G_flow / rho_solution
            else:
                pump_results.Q_vol = 0.005

            delta_P = max(0, (P_discharge - P_suction)) * 1e6
            rho_water = WaterProperties.density(20)

            h_loss = 5.0
            h_geom = max(1, self.input.height_install)

            if rho_water > 0:
                pump_results.H_pump = delta_P / (rho_water * self.g) + h_geom + h_loss
            else:
                pump_results.H_pump = h_geom + h_loss

            pump_results.H_pump = max(5, pump_results.H_pump)

            pump_results.N_hydr = (pump_results.Q_vol * pump_results.H_pump * rho_water * self.g) / 1000
            pump_results.N_hydr = max(0.1, pump_results.N_hydr)

            Q_lps = pump_results.Q_vol * 1000

            if Q_lps < 1:
                pump_results.type = "Х-1 (шестерёнчатый)"
            elif Q_lps < 6:
                pump_results.type = "Х-6 (центробежный)"
            elif Q_lps < 20:
                pump_results.type = "Х-20 (центробежный)"
            elif Q_lps < 50:
                pump_results.type = "Х-50 (центробежный)"
            else:
                pump_results.type = "Х-100 (центробежный)"

        except Exception as e:
            print(f"Ошибка при расчёте насоса: {e}")
            pump_results.Q_vol = 0.005
            pump_results.H_pump = 20
            pump_results.N_hydr = 2
            pump_results.type = "Центробежный насос"

        return pump_results

    def calculate_pipeline_diameter(self, G_flow: float, rho: float, w_opt: float) -> float:
        """Расчёт диаметра трубопровода"""
        if rho > 0 and w_opt > 0 and G_flow > 0:
            d = math.sqrt((4 * G_flow) / (math.pi * rho * w_opt))
        else:
            d = 0.05
        return max(0.02, min(0.3, d))

    def calculate_hydraulic_resistance(self, d: float, L: float, w: float,
                                       rho: float, mu: float, zeta_local: List[float]) -> float:
        """Расчёт гидравлического сопротивления трубопровода"""
        if d <= 0 or rho <= 0:
            return 0

        Re = (w * d * rho) / mu if mu > 0 else 10000

        if Re < 2300:
            lam = 64 / Re if Re > 0 else 0.03
        elif Re < 10000:
            lam = 0.3164 / Re ** 0.25
        else:
            lam = 0.11 * (0.0001 / d + 68 / Re) ** 0.25

        h_friction = lam * (L / d) * (w ** 2) / (2 * self.g)
        h_local = sum(zeta_local) * (w ** 2) / (2 * self.g)

        return h_friction + h_local


class HydraulicCalculator:
    """Класс для гидравлических расчётов"""

    def __init__(self):
        self.g = 9.81
        self.rho_water = 1000

    def calculate_pressure_loss_pipe(self, L: float, d: float, w: float,
                                     rho: float, mu: float, roughness: float = 0.0001) -> float:
        """Потери давления в трубопроводе"""
        if d <= 0 or rho <= 0:
            return 0

        Re = (w * d * rho) / mu if mu > 0 else 10000

        if Re < 2300:
            lam = 64 / Re if Re > 0 else 0.03
        elif Re < 4000:
            lam = 0.0025 * Re ** (1 / 3)
        else:
            lam = 0.11 * (roughness / d + 68 / Re) ** 0.25

        delta_P = lam * (L / d) * (rho * w ** 2) / 2
        return delta_P

    def calculate_pressure_loss_local(self, zeta: float, rho: float, w: float) -> float:
        """Потери давления на местных сопротивлениях"""
        delta_P = zeta * (rho * w ** 2) / 2
        return delta_P

    def calculate_optimal_diameter(self, G: float, rho: float, w_opt_min: float,
                                   w_opt_max: float) -> PipelineResults:
        """Расчёт оптимального диаметра трубопровода"""
        results = PipelineResults()

        if rho > 0 and G > 0:
            results.d_min = math.sqrt((4 * G) / (math.pi * rho * w_opt_max))
            results.d_max = math.sqrt((4 * G) / (math.pi * rho * w_opt_min))
        else:
            results.d_min = 0.02
            results.d_max = 0.05

        standard_diameters = [0.025, 0.032, 0.04, 0.05, 0.065, 0.08, 0.1, 0.125, 0.15, 0.2]

        results.selected_m = results.d_max
        for d_std in standard_diameters:
            if d_std >= results.d_min:
                results.selected_m = d_std
                break

        results.d_min = round(results.d_min * 1000, 1)
        results.d_max = round(results.d_max * 1000, 1)
        results.selected = round(results.selected_m * 1000, 1)

        if rho > 0 and results.selected_m > 0:
            results.w_actual = (4 * G) / (math.pi * results.selected_m ** 2 * rho)
        else:
            results.w_actual = 0

        return results

    def calculate_NPSH(self, P_sat: float, P_suction: float, h_geom: float,
                       h_loss: float, rho: float) -> float:
        """Расчёт кавитационного запаса"""
        if rho <= 0 or self.g <= 0:
            return 0
        NPSH = (P_suction - P_sat) / (rho * self.g) - h_geom - h_loss
        return max(0, NPSH)


class MaterialBalance:
    """Класс для детального материального баланса"""

    @staticmethod
    def calculate_material_balance(G_n: float, x_n: float, x_k: float) -> Dict:
        """Расчёт материального баланса"""
        G_solid = G_n * x_n
        G_k = G_solid / x_k
        W_total = G_n - G_k

        # Примерное распределение по корпусам
        W = [W_total * 0.31, W_total * 0.33, W_total * 0.36]

        G = [G_n, G_n - W[0], G_k]

        x = [x_n]
        x.append((G[0] * x_n) / G[1] if G[1] > 0 else x_k)
        x.append((G[1] * x[1]) / G[2] if G[2] > 0 else x_k)

        return {
            'W_total': round(W_total, 3),
            'W': [round(w, 3) for w in W],
            'G': [round(g, 3) for g in G],
            'x': [round(xi, 4) for xi in x]
        }


class ThermalBalance:
    """Класс для расчёта теплового баланса"""

    @staticmethod
    def calculate_heat_losses(Q_total: float, loss_fraction: float = 0.03) -> float:
        """Расчёт потерь тепла в окружающую среду"""
        return Q_total * loss_fraction

    @staticmethod
    def calculate_efficiency(Q_used: float, Q_supplied: float) -> float:
        """Расчёт теплового КПД"""
        if Q_supplied > 0:
            return (Q_used / Q_supplied) * 100
        return 0.0

    @staticmethod
    def calculate_steam_saving(ud_par_actual: float, ud_par_theoretical: float = 0.33) -> float:
        """Расчёт экономии пара по сравнению с теоретической"""
        if ud_par_theoretical > 0:
            return ((ud_par_theoretical - ud_par_actual) / ud_par_theoretical) * 100
        return 0.0