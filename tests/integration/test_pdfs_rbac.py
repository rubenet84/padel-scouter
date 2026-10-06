"""
Tests de integración RBAC del bloque PDFs.

Cubren:
- POST /players/{pid}/pdf-token  -> reports.generate + scope (admin global).
- GET  /players/{pid}/pdf (Bearer) -> reports.download + scope.
- GET  /players/{pid}/pdf (download_token) -> token válido, usuario actual,
  permiso y scope vigentes (el token NO es bypass de RBAC).
- Content-Disposition saneado.
- Errores: 401/403/404, token manipulado/expirado, reuso (no one-time).

WeasyPrint se mockea (no se genera PDF real).
Requieren PostgreSQL local en localhost:5432.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt as jose_jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import settings
from app.core.security import create_download_token
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


@pytest.fixture(scope="module", autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def mock_pdf(monkeypatch):
    """Mockea la generación de PDF (WeasyPrint). Devuelve un contador de llamadas."""
    calls = {"n": 0}

    def fake_generate(player, analysis):
        calls["n"] += 1
        return b"%PDF-1.4 fake pdf content"

    monkeypatch.setattr(
        "app.infrastructure.pdf.generate_pdf.generate_player_pdf", fake_generate
    )
    return calls


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


def _token_url(pid, token):
    return f"/api/v1/players/{pid}/pdf?download_token={token}"


# ── POST /pdf-token ────────────────────────────────────────────

class TestPdfToken:

    def test_admin_propio_200(self):
        admin, _ = _register_and_login("admin")
        pid = _new_player(admin, "AdminP")
        assert client.post(f"/api/v1/players/{pid}/pdf-token", headers=admin).status_code == 200

    def test_admin_otro_owner_200(self):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DeOwner")
        assert client.post(f"/api/v1/players/{pid}/pdf-token", headers=admin).status_code == 200

    def test_entrenador_propio_200(self):
        coach, _ = _register_and_login("entrenador")
        pid = _new_player(coach, "Alumno")
        assert client.post(f"/api/v1/players/{pid}/pdf-token", headers=coach).status_code == 200

    def test_entrenador_ajeno_404(self):
        a, _ = _register_and_login("entrenador")
        b, _ = _register_and_login("entrenador")
        pid_b = _new_player(b, "DeB")
        assert client.post(f"/api/v1/players/{pid_b}/pdf-token", headers=a).status_code == 404

    def test_jugador_propio_200(self):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        assert client.post(f"/api/v1/players/{pid}/pdf-token", headers=user).status_code == 200

    def test_jugador_ajeno_404(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player(b, "DeB")
        assert client.post(f"/api/v1/players/{pid_b}/pdf-token", headers=a).status_code == 404


# ── GET /pdf con Bearer ────────────────────────────────────────

class TestPdfWithBearer:

    def test_admin_propio_200(self, mock_pdf):
        admin, _ = _register_and_login("admin")
        pid = _new_player(admin, "AdminP")
        r = client.get(f"/api/v1/players/{pid}/pdf", headers=admin)
        assert r.status_code == 200

    def test_admin_otro_owner_200(self, mock_pdf):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DeOwner")
        assert client.get(f"/api/v1/players/{pid}/pdf", headers=admin).status_code == 200

    def test_entrenador_propio_200(self, mock_pdf):
        coach, _ = _register_and_login("entrenador")
        pid = _new_player(coach, "Alumno")
        assert client.get(f"/api/v1/players/{pid}/pdf", headers=coach).status_code == 200

    def test_entrenador_ajeno_404(self, mock_pdf):
        a, _ = _register_and_login("entrenador")
        b, _ = _register_and_login("entrenador")
        pid_b = _new_player(b, "DeB")
        assert client.get(f"/api/v1/players/{pid_b}/pdf", headers=a).status_code == 404

    def test_jugador_propio_200(self, mock_pdf):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        assert client.get(f"/api/v1/players/{pid}/pdf", headers=user).status_code == 200

    def test_jugador_ajeno_404(self, mock_pdf):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player(b, "DeB")
        assert client.get(f"/api/v1/players/{pid_b}/pdf", headers=a).status_code == 404

    def test_respuesta_pdf_valida(self, mock_pdf):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        r = client.get(f"/api/v1/players/{pid}/pdf", headers=user)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content.startswith(b"%PDF")
        assert "content-disposition" in r.headers


# ── Autenticación ──────────────────────────────────────────────

class TestPdfAuth:

    def test_sin_credenciales_401(self):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        # sin Bearer ni download_token
        assert client.get(f"/api/v1/players/{pid}/pdf").status_code == 401

    def test_usuario_inactivo_401(self, mock_pdf):
        headers, uid = _register_and_login("jugador")
        pid = _new_player(headers, "Mio")
        db = TestSession()
        u = db.query(UserModel).filter(UserModel.id == uid).first()
        u.is_active = False
        db.commit()
        db.close()
        assert client.get(f"/api/v1/players/{pid}/pdf", headers=headers).status_code == 401


# ── download_token ─────────────────────────────────────────────

class TestDownloadToken:

    def test_token_valido_jugador_correcto_200(self, mock_pdf):
        user, uid = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        token = create_download_token(str(uid), str(pid))
        assert client.get(_token_url(pid, token)).status_code == 200

    def test_token_player_mismatch_rechazado(self, mock_pdf):
        user, uid = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        token = create_download_token(str(uid), str(pid))
        # URL con OTRO player id → token.player_id != player_id de la URL → 403
        otro = str(uuid.uuid4())
        assert client.get(_token_url(otro, token)).status_code == 403

    def test_token_manipulado_401(self, mock_pdf):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        assert client.get(_token_url(pid, "token.falso.invalido")).status_code == 401

    def test_token_expirado_401(self, mock_pdf):
        user, uid = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        expired = jose_jwt.encode(
            {"sub": str(uid), "player_id": str(pid),
             "exp": datetime.now(timezone.utc) - timedelta(minutes=1), "type": "download"},
            settings.secret_key.get_secret_value(), algorithm=settings.algorithm,
        )
        assert client.get(_token_url(pid, expired)).status_code == 401

    def test_token_de_A_para_jugador_de_B_bloqueado(self, mock_pdf):
        a, a_id = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player(b, "DeB")
        # A fabrica/obtiene un token para el jugador de B
        token = create_download_token(str(a_id), str(pid_b))
        r = client.get(_token_url(pid_b, token))
        assert r.status_code == 404  # scope de A no alcanza al jugador de B

    def test_token_usuario_inactivo_bloqueado_401(self, mock_pdf):
        user, uid = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        token = create_download_token(str(uid), str(pid))
        db = TestSession()
        u = db.query(UserModel).filter(UserModel.id == uid).first()
        u.is_active = False
        db.commit()
        db.close()
        assert client.get(_token_url(pid, token)).status_code == 401

    def test_token_reutilizable_dentro_de_5_min(self, mock_pdf):
        # Documenta el comportamiento real: NO es one-time (stateless, sin jti/blacklist)
        user, uid = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        token = create_download_token(str(uid), str(pid))
        assert client.get(_token_url(pid, token)).status_code == 200
        assert client.get(_token_url(pid, token)).status_code == 200  # reuso OK


# ── Content-Disposition saneado ────────────────────────────────

class TestContentDisposition:

    def test_nombre_problematico_saneado(self, mock_pdf):
        user, _ = _register_and_login("jugador")
        # nombre con comilla, dos puntos y CR/LF
        pid = _new_player(user, 'Malo"CRLF\r\nInjected: x')
        r = client.get(f"/api/v1/players/{pid}/pdf", headers=user)
        assert r.status_code == 200
        header = r.headers["content-disposition"]
        assert "\r" not in header and "\n" not in header
        assert header == 'attachment; filename="informe_MaloCRLFInjected_x.pdf"'
