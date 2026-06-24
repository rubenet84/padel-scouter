import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.infrastructure.database.models import Base
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

# ── Crear tablas ANTES de cualquier test ──────────────────────
Base.metadata.create_all(bind=engine)

client = TestClient(app)


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture(scope="module")
def auth_headers():
    client.post("/api/v1/auth/register", json={
        "email": "api_test@padel.com",
        "username": "api_tester",
        "password": "password123",
    })
    response = client.post("/api/v1/auth/login", json={
        "email": "api_test@padel.com",
        "password": "password123",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def created_player(auth_headers):
    response = client.post("/api/v1/players/", json={
        "name": "Test Player",
        "category": "3ª Categoría",
        "stats": {
            "derecha": 70, "reves": 65, "volea": 60,
            "bandeja": 55, "vibora": 50, "smash": 60,
            "lob": 55, "saque": 65, "bajada_pared": 58,
            "velocidad": 70, "resistencia": 65, "reflejos": 68,
            "tactica": 62, "presion": 58, "trabajo_en_pareja": 65,
            "torneos_jugados": 20, "victorias": 10,
            "puntos_ranking_fep": 500,
        }
    }, headers=auth_headers)
    assert response.status_code == 201
    return response.json()


# ── Auth tests ────────────────────────────────────────────────

class TestAuthEndpoints:

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_register_usuario(self):
        email_unico = f"nuevo_{uuid.uuid4().hex[:8]}@padel.com"
        username_unico = f"user_{uuid.uuid4().hex[:8]}"
        response = client.post("/api/v1/auth/register", json={
            "email": email_unico,
            "username": username_unico,
            "password": "password123",
        })
        assert response.status_code == 201
        assert "id" in response.json()

    def test_login_correcto(self):
        client.post("/api/v1/auth/register", json={
            "email": "login_test@padel.com",
            "username": "login_user",
            "password": "password123",
        })
        response = client.post("/api/v1/auth/login", json={
            "email": "login_test@padel.com",
            "password": "password123",
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()

    def test_login_password_incorrecto(self):
        response = client.post("/api/v1/auth/login", json={
            "email": "login_test@padel.com",
            "password": "password_malo",
        })
        assert response.status_code == 401

    def test_me_sin_token(self):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_con_token(self, auth_headers):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["email"] == "api_test@padel.com"


# ── Players tests ─────────────────────────────────────────────

class TestPlayersEndpoints:

    def test_crear_jugador(self, auth_headers):
        response = client.post("/api/v1/players/", json={
            "name": "María López",
            "category": "4ª Categoría",
            "stats": {"derecha": 60, "reves": 55},
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["name"] == "María López"

    def test_listar_jugadores(self, auth_headers, created_player):
        response = client.get("/api/v1/players/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    def test_obtener_jugador_por_id(self, auth_headers, created_player):
        player_id = created_player["id"]
        response = client.get(f"/api/v1/players/{player_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == player_id

    def test_jugador_no_encontrado(self, auth_headers):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/players/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_sin_token_no_puede_crear(self):
        response = client.post("/api/v1/players/", json={
            "name": "Intruso",
            "category": "Iniciación",
        })
        assert response.status_code == 401