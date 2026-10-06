"""
Tests de integración RBAC del bloque CHATBOT (app/api/v1/chatbot.py).

Cubren: autenticación (401), RBAC (AI_CHAT para los 3 roles), comportamiento
de caché (miss → Gemini; hit → sin Gemini) y validación del schema.
Gemini (RAG) y Redis se mockean: NO se hacen llamadas reales ni se depende de Redis.
Requieren PostgreSQL local en localhost:5432.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.infrastructure.database.models import Base, UserModel
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
ASK = "/api/v1/chatbot/ask"


class FakeRedis:
    """Redis falso en memoria: determinista y sin red."""
    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value


class FakeRAG:
    """RAG falso: registra cuántas veces se invoca y devuelve una respuesta fija."""
    def __init__(self):
        self.calls = 0

    def answer(self, question: str) -> str:
        self.calls += 1
        return f"Respuesta del reglamento para: {question}"


@pytest.fixture(scope="module", autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def mock_chat(monkeypatch):
    """Reemplaza Redis y el RAG (Gemini) del módulo chatbot. Devuelve (redis, rag)."""
    fake_redis = FakeRedis()
    fake_rag = FakeRAG()
    monkeypatch.setattr("app.api.v1.chatbot._redis", fake_redis)
    monkeypatch.setattr("app.api.v1.chatbot.rag_service", fake_rag)
    return fake_redis, fake_rag


def _register_and_login_email(role: str = "jugador"):
    """Registra, fija el rol, hace login y devuelve (headers, email)."""
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
    db.close()
    login = client.post("/api/v1/auth/login", json={"email": email, "password": STRONG_PASSWORD})
    assert login.status_code == 200, f"login falló: {login.json()}"
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, email


def _register_and_login(role: str = "jugador"):
    headers, _ = _register_and_login_email(role)
    return headers


# ── Autenticación ──────────────────────────────────────────────

class TestChatbotAuth:

    def test_sin_jwt_401(self):
        r = client.post(ASK, json={"question": "¿Cuántos sets tiene un partido?"})
        assert r.status_code == 401

    def test_usuario_inactivo_rechazado(self):
        headers, email = _register_and_login_email("jugador")
        # suspender la cuenta: get_current_user (fuente de verdad = BD) debe rechazar
        db = TestSession()
        user = db.query(UserModel).filter(UserModel.email == email).first()
        user.is_active = False
        db.commit()
        db.close()
        r = client.post(ASK, json={"question": "¿Cuántos sets?"}, headers=headers)
        assert r.status_code == 401


# ── RBAC — los 3 roles tienen AI_CHAT ──────────────────────────

class TestChatbotRBAC:

    def test_admin_200(self, mock_chat):
        headers = _register_and_login("admin")
        r = client.post(ASK, json={"question": "¿Cómo se puntúa?"}, headers=headers)
        assert r.status_code == 200

    def test_entrenador_200(self, mock_chat):
        headers = _register_and_login("entrenador")
        r = client.post(ASK, json={"question": "¿Cómo se puntúa?"}, headers=headers)
        assert r.status_code == 200

    def test_jugador_200(self, mock_chat):
        headers = _register_and_login("jugador")
        r = client.post(ASK, json={"question": "¿Cómo se puntúa?"}, headers=headers)
        assert r.status_code == 200


# ── Gemini (RAG) y caché ───────────────────────────────────────

class TestChatbotGeminiAndCache:

    def test_cache_miss_devuelve_respuesta(self, mock_chat):
        _, rag = mock_chat
        headers = _register_and_login("jugador")
        r = client.post(ASK, json={"question": "¿Cuántos sets?"}, headers=headers)
        assert r.status_code == 200
        assert "Respuesta del reglamento" in r.json()["answer"]
        assert r.json()["cached"] is False

    def test_cache_miss_invoca_gemini(self, mock_chat):
        _, rag = mock_chat
        headers = _register_and_login("jugador")
        client.post(ASK, json={"question": "¿Cuántos sets?"}, headers=headers)
        assert rag.calls == 1

    def test_cache_miss_guarda_en_redis(self, mock_chat):
        redis, _ = mock_chat
        headers = _register_and_login("jugador")
        client.post(ASK, json={"question": "¿Cuántos sets?"}, headers=headers)
        assert len(redis.store) == 1

    def test_cache_hit_no_invoca_gemini(self, mock_chat):
        _, rag = mock_chat
        headers = _register_and_login("jugador")
        q = {"question": "¿Cuántos sets?"}
        client.post(ASK, json=q, headers=headers)   # miss
        r2 = client.post(ASK, json=q, headers=headers)  # hit
        assert r2.status_code == 200
        assert r2.json()["cached"] is True
        assert rag.calls == 1  # no se volvió a llamar a la IA

    def test_cache_hit_devuelve_respuesta_cacheada(self, mock_chat):
        headers = _register_and_login("jugador")
        q = {"question": "¿Cuántos sets?"}
        r1 = client.post(ASK, json=q, headers=headers)
        r2 = client.post(ASK, json=q, headers=headers)
        assert r2.json()["answer"] == r1.json()["answer"]
        assert r2.json()["cached"] is True


# ── Validación del schema ──────────────────────────────────────

class TestChatbotValidation:

    def test_pregunta_vacia_422(self):
        headers = _register_and_login("jugador")
        r = client.post(ASK, json={"question": ""}, headers=headers)
        assert r.status_code == 422

    def test_pregunta_demasiado_larga_422(self):
        headers = _register_and_login("jugador")
        r = client.post(ASK, json={"question": "x" * 501}, headers=headers)
        assert r.status_code == 422
