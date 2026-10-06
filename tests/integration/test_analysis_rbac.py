"""
Tests de integración RBAC del bloque ANALYSIS (app/api/v1/analysis.py).

Cubren:
- GET /analysis/{player_id}: scope por rol (admin global) y 404 para ajeno.
- POST /analysis/{player_id}: ownership DIRECTO (admin sin bypass) y 404 ajeno.
- Seguridad de coste: un POST ajeno NO llama a Gemini ni crea AnalysisModel.

La IA (Gemini) y Redis se mockean para no depender de servicios externos.
Requieren PostgreSQL local en localhost:5432.
"""
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.infrastructure.database.models import Base, UserModel, AnalysisModel
from app.infrastructure.database.session import get_db

TEST_DB_URL = "postgresql+psycopg2://padel:padel123@localhost:5432/padel_scouter"
engine = create_engine(TEST_DB_URL)
TestSession = sessionmaker(bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

STRONG_PASSWORD = "PadelScouter2026!"

AI_RESULT = {
    "descripcion_epica": "Un guerrero de prueba.",
    "fortalezas": ["Bandeja letal"],
    "debilidades": ["Revés mejorable"],
    "plan_mejora": "Plan de prueba.",
    "golpe_definitivo": "Golpe de Prueba",
    "descripcion_golpe": "Descripción de prueba.",
}


class _FakeCache:
    """Cache falsa: siempre miss, set sin efecto (evita Redis real)."""
    def get(self, prefix, data):
        return None

    def set(self, prefix, data, result, ttl=86400):
        return None


@pytest.fixture(scope="module", autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def mock_ai(monkeypatch):
    """Mockea Gemini y Redis en el módulo analysis. Devuelve el espía de Gemini."""
    spy = MagicMock(return_value=AI_RESULT)
    monkeypatch.setattr("app.api.v1.analysis.analyze_player_with_ai", spy)
    monkeypatch.setattr("app.api.v1.analysis.redis_cache", _FakeCache())
    return spy


# ── Helpers ────────────────────────────────────────────────────

def _register_and_login(role: str = "jugador"):
    email = f"{role}_{uuid.uuid4().hex[:8]}@padel.com"
    username = f"{role}_{uuid.uuid4().hex[:8]}"
    client.post("/api/v1/auth/register", json={
        "email": email, "username": username, "password": STRONG_PASSWORD,
    })
    db = TestSession()
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if role != "jugador":
        user.role = role
        db.commit()
    user_id = user.id
    db.close()
    login = client.post("/api/v1/auth/login", json={"email": email, "password": STRONG_PASSWORD})
    assert login.status_code == 200, f"login falló: {login.json()}"
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, user_id


def _new_player(headers, name="Jugador"):
    r = client.post("/api/v1/players/", json={
        "name": name, "category": "3ª Categoría", "stats": {"derecha": 60, "reves": 55},
    }, headers=headers)
    assert r.status_code == 201, r.json()
    return r.json()["id"]


# ── GET — scope por rol ────────────────────────────────────────

class TestGetAnalysis:

    def test_jugador_propio_200(self):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user)
        assert client.get(f"/api/v1/analysis/{pid}", headers=user).status_code == 200

    def test_jugador_ajeno_404(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player(b, "DeB")
        assert client.get(f"/api/v1/analysis/{pid_b}", headers=a).status_code == 404

    def test_entrenador_propio_200(self):
        coach, _ = _register_and_login("entrenador")
        pid = _new_player(coach, "Alumno")
        assert client.get(f"/api/v1/analysis/{pid}", headers=coach).status_code == 200

    def test_entrenador_ajeno_404(self):
        a, _ = _register_and_login("entrenador")
        b, _ = _register_and_login("entrenador")
        pid_b = _new_player(b, "DeB")
        assert client.get(f"/api/v1/analysis/{pid_b}", headers=a).status_code == 404

    def test_admin_propio_200(self):
        admin, _ = _register_and_login("admin")
        pid = _new_player(admin, "AdminP")
        assert client.get(f"/api/v1/analysis/{pid}", headers=admin).status_code == 200

    def test_admin_otro_owner_200(self):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DeOwner")
        assert client.get(f"/api/v1/analysis/{pid}", headers=admin).status_code == 200

    def test_player_inexistente_404(self):
        user, _ = _register_and_login("jugador")
        assert client.get(f"/api/v1/analysis/{uuid.uuid4()}", headers=user).status_code == 404


# ── POST — ownership directo (sin bypass admin) ───────────────

class TestPostAnalysis:

    def test_jugador_genera_propio_201(self, mock_ai):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user)
        r = client.post(f"/api/v1/analysis/{pid}", headers=user)
        assert r.status_code == 201
        assert r.json()["player_id"] == pid

    def test_entrenador_genera_propio_201(self, mock_ai):
        coach, _ = _register_and_login("entrenador")
        pid = _new_player(coach, "Alumno")
        assert client.post(f"/api/v1/analysis/{pid}", headers=coach).status_code == 201

    def test_admin_genera_propio_201(self, mock_ai):
        admin, _ = _register_and_login("admin")
        pid = _new_player(admin, "AdminP")
        assert client.post(f"/api/v1/analysis/{pid}", headers=admin).status_code == 201

    def test_jugador_post_ajeno_404(self, mock_ai):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player(b, "DeB")
        assert client.post(f"/api/v1/analysis/{pid_b}", headers=a).status_code == 404

    def test_entrenador_post_ajeno_404(self, mock_ai):
        a, _ = _register_and_login("entrenador")
        b, _ = _register_and_login("entrenador")
        pid_b = _new_player(b, "DeB")
        assert client.post(f"/api/v1/analysis/{pid_b}", headers=a).status_code == 404

    def test_admin_post_ajeno_404(self, mock_ai):
        # El admin NO puede generar análisis de jugadores de otros owners (coste IA)
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DeOwner")
        assert client.post(f"/api/v1/analysis/{pid}", headers=admin).status_code == 404


# ── Seguridad de generación (coste) ───────────────────────────

class TestPostGenerationSecurity:

    def test_post_ajeno_no_llama_a_gemini(self, mock_ai):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player(b, "Victima")
        r = client.post(f"/api/v1/analysis/{pid_b}", headers=a)
        assert r.status_code == 404
        mock_ai.assert_not_called()  # ownership directo corta antes de Gemini

    def test_post_ajeno_no_crea_analysis(self, mock_ai):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player(b, "Victima")
        assert client.post(f"/api/v1/analysis/{pid_b}", headers=a).status_code == 404
        db = TestSession()
        count = db.query(AnalysisModel).filter(AnalysisModel.player_id == pid_b).count()
        db.close()
        assert count == 0  # no se persistió nada

    def test_admin_post_ajeno_no_llama_a_gemini(self, mock_ai):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DeOwner")
        assert client.post(f"/api/v1/analysis/{pid}", headers=admin).status_code == 404
        mock_ai.assert_not_called()
