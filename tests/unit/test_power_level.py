import pytest
from app.domain.value_objects.power_level import (
    calculate_power_level,
    classify_by_power,
)
from app.domain.value_objects.category import PlayerCategory


class TestCalculatePowerLevel:

    def test_iniciacion_player_dentro_de_rango(self, stats_iniciacion):
        power = calculate_power_level(stats_iniciacion, PlayerCategory.INICIACION)
        assert 100 <= power <= 1499, f"Esperado 100-1499, obtenido {power}"

    def test_tercera_player_dentro_de_rango(self, stats_tercera):
        power = calculate_power_level(stats_tercera, PlayerCategory.TERCERA)
        assert 4500 <= power <= 5999, f"Esperado 4500-5999, obtenido {power}"

    def test_pro_player_dentro_de_rango(self, stats_pro):
        power = calculate_power_level(stats_pro, PlayerCategory.PRO)
        assert 9000 <= power <= 9999, f"Esperado 9000-9999, obtenido {power}"

    def test_power_level_nunca_supera_9999(self, stats_pro):
        power = calculate_power_level(stats_pro, PlayerCategory.PRO)
        assert power <= 9999

    def test_power_level_siempre_positivo(self, stats_iniciacion):
        power = calculate_power_level(stats_iniciacion, PlayerCategory.INICIACION)
        assert power > 0

    def test_mejor_jugador_tiene_mayor_poder(self, stats_iniciacion, stats_pro):
        power_ini = calculate_power_level(stats_iniciacion, PlayerCategory.INICIACION)
        power_pro = calculate_power_level(stats_pro, PlayerCategory.PRO)
        assert power_pro > power_ini

    def test_power_level_es_entero(self, stats_tercera):
        power = calculate_power_level(stats_tercera, PlayerCategory.TERCERA)
        assert isinstance(power, int)


class TestClassifyByPower:

    def test_power_bajo_es_iniciacion(self):
        assert classify_by_power(500) == PlayerCategory.INICIACION

    def test_power_medio_es_tercera(self):
        assert classify_by_power(5000) == PlayerCategory.TERCERA

    def test_power_alto_es_pro(self):
        assert classify_by_power(9500) == PlayerCategory.PRO

    def test_limites_exactos(self):
        assert classify_by_power(1500) == PlayerCategory.QUINTA
        assert classify_by_power(3000) == PlayerCategory.CUARTA
        assert classify_by_power(4500) == PlayerCategory.TERCERA
        assert classify_by_power(6000) == PlayerCategory.SEGUNDA
        assert classify_by_power(7500) == PlayerCategory.PRIMERA
        assert classify_by_power(9000) == PlayerCategory.PRO