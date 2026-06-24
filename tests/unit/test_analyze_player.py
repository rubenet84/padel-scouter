import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from app.domain.entities.player import Player, PlayerStats
from app.domain.value_objects.category import PlayerCategory
from app.domain.use_cases.analyze_player import AnalyzePlayerUseCase
from app.domain.entities.analysis import AnalysisResult


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def mock_ai_result():
    return {
        "descripcion_epica": "Un guerrero del pádel imparable.",
        "fortalezas": ["Bandeja letal", "Gran movilidad", "Saque potente"],
        "debilidades": ["Revés mejorable"],
        "plan_mejora": "Trabajar el revés 3 veces por semana.",
        "golpe_definitivo": "Bandeja paralela",
        "nivel_amenaza": "ALTO",
    }


@pytest.fixture
def mock_ai_client(mock_ai_result):
    client = MagicMock()
    client.analyze_player_with_ai.return_value = mock_ai_result
    return client


@pytest.fixture
def mock_cache_empty():
    """Cache que siempre devuelve None (sin hit)."""
    cache = MagicMock()
    cache.get.return_value = None
    return cache


@pytest.fixture
def mock_cache_with_hit(mock_ai_result):
    """Cache que devuelve resultado (cache hit)."""
    cache = MagicMock()
    cache.get.return_value = mock_ai_result
    return cache


@pytest.fixture
def player_tercera(stats_tercera):
    return Player(
        name="Juan García",
        category=PlayerCategory.TERCERA,
        stats=stats_tercera,
    )


# ── Tests ─────────────────────────────────────────────────────

class TestAnalyzePlayerUseCase:

    def test_retorna_analysis_result(self, player_tercera, mock_ai_client, mock_cache_empty):
        use_case = AnalyzePlayerUseCase(ai_client=mock_ai_client, cache=mock_cache_empty)
        result = use_case.execute(player_tercera)
        assert isinstance(result, AnalysisResult)

    def test_power_level_en_rango_tercera(self, player_tercera, mock_ai_client, mock_cache_empty):
        use_case = AnalyzePlayerUseCase(ai_client=mock_ai_client, cache=mock_cache_empty)
        result = use_case.execute(player_tercera)
        assert 4500 <= result.power_level <= 5999

    def test_categoria_correcta(self, player_tercera, mock_ai_client, mock_cache_empty):
        use_case = AnalyzePlayerUseCase(ai_client=mock_ai_client, cache=mock_cache_empty)
        result = use_case.execute(player_tercera)
        assert result.category == PlayerCategory.TERCERA

    def test_descripcion_no_vacia(self, player_tercera, mock_ai_client, mock_cache_empty):
        use_case = AnalyzePlayerUseCase(ai_client=mock_ai_client, cache=mock_cache_empty)
        result = use_case.execute(player_tercera)
        assert len(result.ai_description) > 0

    def test_fortalezas_es_lista(self, player_tercera, mock_ai_client, mock_cache_empty):
        use_case = AnalyzePlayerUseCase(ai_client=mock_ai_client, cache=mock_cache_empty)
        result = use_case.execute(player_tercera)
        assert isinstance(result.strengths, list)
        assert len(result.strengths) > 0

    def test_player_id_coincide(self, player_tercera, mock_ai_client, mock_cache_empty):
        use_case = AnalyzePlayerUseCase(ai_client=mock_ai_client, cache=mock_cache_empty)
        result = use_case.execute(player_tercera)
        assert result.player_id == player_tercera.id

    def test_llama_a_ai_cuando_no_hay_cache(self, player_tercera, mock_ai_client, mock_cache_empty):
        use_case = AnalyzePlayerUseCase(ai_client=mock_ai_client, cache=mock_cache_empty)
        use_case.execute(player_tercera)
        mock_ai_client.analyze_player_with_ai.assert_called_once()

    def test_no_llama_a_ai_si_hay_cache(self, player_tercera, mock_ai_client, mock_cache_with_hit):
        use_case = AnalyzePlayerUseCase(ai_client=mock_ai_client, cache=mock_cache_with_hit)
        use_case.execute(player_tercera)
        mock_ai_client.analyze_player_with_ai.assert_not_called()

    def test_guarda_en_cache_tras_llamar_ai(self, player_tercera, mock_ai_client, mock_cache_empty):
        use_case = AnalyzePlayerUseCase(ai_client=mock_ai_client, cache=mock_cache_empty)
        use_case.execute(player_tercera)
        mock_cache_empty.set.assert_called_once()

    def test_cache_hit_no_guarda_de_nuevo(self, player_tercera, mock_ai_client, mock_cache_with_hit):
        use_case = AnalyzePlayerUseCase(ai_client=mock_ai_client, cache=mock_cache_with_hit)
        use_case.execute(player_tercera)
        mock_cache_with_hit.set.assert_not_called()