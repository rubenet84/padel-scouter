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
Base.metadata.create_all(bind=engine)
client = TestClient(app)

# Contraseña fuerte que cumple OWASP
STRONG_PASSWORD = "PadelScouter2026!"


@pytest.fixture(scope="module")
def auth_headers():
    email_unico = f"api_test_{uuid.uuid4().hex[:8]}@padel.com"
    username_unico = f"api_tester_{uuid.uuid4().hex[:8]}"
    client.post("/api/v1/auth/register", json={
        "email": email_unico,
        "username": username_unico,
        "password": STRONG_PASSWORD,
    })
    response = client.post("/api/v1/auth/login", json={
        "email": email_unico,
        "password": STRONG_PASSWORD,
    })
    assert response.status_code == 200, f"Login falló: {response.json()}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def created_player(auth_headers):
    response = client.post("/api/v1/players/", json={
        "name": "Test Player",
        "category": "3ª Categoría",
        "stats": {
            "derecha": 70, "reves": 65, "volea_derecha": 60, "volea_reves": 60,
            "bandeja": 55, "vibora": 50, "remate": 60,
            "globo": 55, "saque": 65, "bajada_pared": 58,
            "velocidad": 70, "resistencia": 65, "reflejos": 68,
            "tactica": 62, "presion": 58, "trabajo_en_pareja": 65,
        }
    }, headers=auth_headers)
    assert response.status_code == 201
    return response.json()


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
            "password": STRONG_PASSWORD,
        })
        assert response.status_code == 201
        assert "id" in response.json()

    def test_register_password_debil_rechazada(self):
        """OWASP A07 — contraseña débil debe ser rechazada"""
        response = client.post("/api/v1/auth/register", json={
            "email": "weak@padel.com",
            "username": "weakuser",
            "password": "password123",  # sin mayúscula ni especial
        })
        assert response.status_code == 422

    def test_email_case_insensitive(self):
        """OWASP A07 — email normalizado a minúsculas"""
        email_unico = f"CaseTEST_{uuid.uuid4().hex[:6]}@PADEL.COM"
        response = client.post("/api/v1/auth/register", json={
            "email": email_unico,
            "username": f"caseuser_{uuid.uuid4().hex[:6]}",
            "password": STRONG_PASSWORD,
        })
        assert response.status_code == 201
        assert response.json()["email"] == email_unico.lower()

    def test_login_correcto(self):
        email = f"login_{uuid.uuid4().hex[:6]}@padel.com"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "username": f"login_{uuid.uuid4().hex[:6]}",
            "password": STRONG_PASSWORD,
        })
        response = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": STRONG_PASSWORD,
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()

    def test_login_password_incorrecto(self):
        response = client.post("/api/v1/auth/login", json={
            "email": "api_test@padel.com",
            "password": "WrongPassword999!",
        })
        assert response.status_code == 401

    def test_me_sin_token(self):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_con_token(self, auth_headers):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert "@padel.com" in response.json()["email"]


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


class TestPasswordResetFlow:

    def test_forgot_password_email_existente(self):
        """OWASP A07 — siempre 200 aunque el email no exista"""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "api_test@padel.com"},
        )
        assert response.status_code == 200
        assert "recibirás" in response.json()["message"]

    def test_forgot_password_email_no_existente(self):
        """OWASP A07 — mismo mensaje aunque el email no exista"""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "noexiste@padel.com"},
        )
        assert response.status_code == 200

    def test_reset_password_token_invalido(self):
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "token_falso", "new_password": "NuevaPass2026!"},
        )
        assert response.status_code == 400

    def test_reset_password_nueva_pass_debil(self):
        from app.core.security import create_reset_token
        token = create_reset_token("api_test@padel.com")
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "new_password": "debil"},
        )
        assert response.status_code == 422


class TestRolesRegistro:
    """Fase 3 — el registro crea siempre 'jugador' y no permite autoasignar rol."""

    def _register_and_me(self, role_payload=None):
        email = f"role_{uuid.uuid4().hex[:8]}@padel.com"
        username = f"role_{uuid.uuid4().hex[:8]}"
        payload = {
            "email": email,
            "username": username,
            "password": STRONG_PASSWORD,
        }
        if role_payload is not None:
            payload["role"] = role_payload  # intento de autoasignación
        client.post("/api/v1/auth/register", json=payload)
        login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": STRONG_PASSWORD},
        )
        assert login.status_code == 200, f"Login falló: {login.json()}"
        token = login.json()["access_token"]
        me = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 200, f"/me falló: {me.json()}"
        return me.json()

    def test_registro_nuevo_recibe_jugador(self):
        assert self._register_and_me()["role"] == "jugador"

    def test_cliente_no_puede_registrarse_como_admin(self):
        assert self._register_and_me("admin")["role"] == "jugador"

    def test_cliente_no_puede_registrarse_como_entrenador(self):
        assert self._register_and_me("entrenador")["role"] == "jugador"

    def test_get_current_user_y_login_siguen_funcionando(self):
        data = self._register_and_me()
        assert "@padel.com" in data["email"]
        assert data["role"] == "jugador"

    def test_rol_invalido_no_persiste_por_check(self):
        from sqlalchemy.exc import IntegrityError
        from app.infrastructure.database.models import UserModel

        db = TestSession()
        try:
            bad = UserModel(
                email=f"bad_{uuid.uuid4().hex[:8]}@padel.com",
                username=f"bad_{uuid.uuid4().hex[:8]}",
                hashed_password="x",
                role="superuser",  # inválido → debe violar ck_users_role
            )
            db.add(bad)
            with pytest.raises(IntegrityError):
                db.commit()
        finally:
            db.rollback()
            db.close()


class TestSuspension:
    """Fase 4 — un usuario suspendido no puede usar la API con un token previo."""

    def test_usuario_suspendido_bloqueado_con_token_previo(self):
        from app.infrastructure.database.models import UserModel

        email = f"susp_{uuid.uuid4().hex[:8]}@padel.com"
        username = f"susp_{uuid.uuid4().hex[:8]}"
        client.post("/api/v1/auth/register", json={
            "email": email,
            "username": username,
            "password": STRONG_PASSWORD,
        })
        login = client.post("/api/v1/auth/login", json={
            "email": email,
            "password": STRONG_PASSWORD,
        })
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # El token funciona mientras la cuenta está activa
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 200

        # Suspender la cuenta (is_active = False)
        db = TestSession()
        user = db.query(UserModel).filter(UserModel.email == email).first()
        user.is_active = False
        db.commit()
        db.close()

        # El MISMO token ya no sirve: la BD es la fuente de verdad
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 401