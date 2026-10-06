"""
Tests de integración RBAC del bloque NOTIFICATIONS.

Cubren: permisos notifications.read/update, scope OWN para los 3 roles,
aislamiento estricto por user_id (sin bypass por player_id), admin sin GLOBAL,
IDOR (404 en notificación ajena), y regresión de filtros/contadores.

Requieren PostgreSQL local en localhost:5432.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.infrastructure.database.models import Base, UserModel, NotificationModel
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


def _make_notification(user_id, title="Notif", is_read=False, player_id=None):
    db = TestSession()
    n = NotificationModel(
        user_id=user_id, type="match_added", title=title,
        message="msg", is_read=is_read, player_id=player_id,
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    nid = n.id
    db.close()
    return nid


def _new_player(headers, name="Jugador"):
    r = client.post("/api/v1/players/", json={
        "name": name, "category": "3ª Categoría", "stats": {"derecha": 60, "reves": 55},
    }, headers=headers)
    assert r.status_code == 201, r.json()
    return r.json()["id"]


# ── Autenticación ──────────────────────────────────────────────

class TestNotificationsAuth:

    def test_sin_jwt_401(self):
        assert client.get("/api/v1/notifications").status_code == 401

    def test_usuario_inactivo_401(self):
        headers, uid = _register_and_login("jugador")
        db = TestSession()
        u = db.query(UserModel).filter(UserModel.id == uid).first()
        u.is_active = False
        db.commit()
        db.close()
        assert client.get("/api/v1/notifications", headers=headers).status_code == 401


# ── READ ───────────────────────────────────────────────────────

class TestNotificationsRead:

    def test_admin_lista_200(self):
        admin, _ = _register_and_login("admin")
        assert client.get("/api/v1/notifications", headers=admin).status_code == 200

    def test_entrenador_lista_200(self):
        coach, _ = _register_and_login("entrenador")
        assert client.get("/api/v1/notifications", headers=coach).status_code == 200

    def test_jugador_lista_200(self):
        user, _ = _register_and_login("jugador")
        assert client.get("/api/v1/notifications", headers=user).status_code == 200

    def test_admin_unread_count_200(self):
        admin, _ = _register_and_login("admin")
        assert client.get("/api/v1/notifications/unread-count", headers=admin).status_code == 200

    def test_entrenador_unread_count_200(self):
        coach, _ = _register_and_login("entrenador")
        assert client.get("/api/v1/notifications/unread-count", headers=coach).status_code == 200

    def test_jugador_unread_count_200(self):
        user, _ = _register_and_login("jugador")
        assert client.get("/api/v1/notifications/unread-count", headers=user).status_code == 200


# ── UPDATE ─────────────────────────────────────────────────────

class TestNotificationsUpdate:

    def test_admin_marca_propia_200(self):
        admin, uid = _register_and_login("admin")
        nid = _make_notification(uid)
        assert client.put(f"/api/v1/notifications/{nid}/read", headers=admin).status_code == 200

    def test_entrenador_marca_propia_200(self):
        coach, uid = _register_and_login("entrenador")
        nid = _make_notification(uid)
        assert client.put(f"/api/v1/notifications/{nid}/read", headers=coach).status_code == 200

    def test_jugador_marca_propia_200(self):
        user, uid = _register_and_login("jugador")
        nid = _make_notification(uid)
        assert client.put(f"/api/v1/notifications/{nid}/read", headers=user).status_code == 200

    def test_admin_read_all_200(self):
        admin, uid = _register_and_login("admin")
        _make_notification(uid)
        assert client.put("/api/v1/notifications/read-all", headers=admin).status_code == 200

    def test_entrenador_read_all_200(self):
        coach, uid = _register_and_login("entrenador")
        _make_notification(uid)
        assert client.put("/api/v1/notifications/read-all", headers=coach).status_code == 200

    def test_jugador_read_all_200(self):
        user, uid = _register_and_login("jugador")
        _make_notification(uid)
        assert client.put("/api/v1/notifications/read-all", headers=user).status_code == 200


# ── IDOR / aislamiento ─────────────────────────────────────────

class TestNotificationsIDOR:

    def test_marcar_notificacion_ajena_404(self):
        a, _ = _register_and_login("jugador")
        b, b_id = _register_and_login("jugador")
        nid_b = _make_notification(b_id)
        assert client.put(f"/api/v1/notifications/{nid_b}/read", headers=a).status_code == 404

    def test_admin_no_puede_marcar_ajena_404(self):
        admin, _ = _register_and_login("admin")
        b, b_id = _register_and_login("jugador")
        nid_b = _make_notification(b_id)
        assert client.put(f"/api/v1/notifications/{nid_b}/read", headers=admin).status_code == 404

    def test_listado_no_incluye_ajenas(self):
        a, _ = _register_and_login("jugador")
        b, b_id = _register_and_login("jugador")
        nid_b = _make_notification(b_id, title="DeB")
        ids = [n["id"] for n in client.get("/api/v1/notifications", headers=a).json()]
        assert str(nid_b) not in ids

    def test_admin_listado_no_incluye_ajenas(self):
        admin, _ = _register_and_login("admin")
        b, b_id = _register_and_login("jugador")
        nid_b = _make_notification(b_id, title="DeB")
        ids = [n["id"] for n in client.get("/api/v1/notifications", headers=admin).json()]
        assert str(nid_b) not in ids

    def test_player_id_no_escapa_del_filtro_user(self):
        a, _ = _register_and_login("jugador")
        b, b_id = _register_and_login("jugador")
        pid = _new_player(b, "DeB")  # player real del owner B (FK válida)
        nid_b = _make_notification(b_id, player_id=pid)
        # A intenta ver las notificaciones de B usando el player_id de B
        ids = [n["id"] for n in client.get(
            f"/api/v1/notifications?player_id={pid}", headers=a).json()]
        assert str(nid_b) not in ids  # el filtro user_id sigue aplicándose

    def test_admin_player_id_no_escapa_del_filtro_user(self):
        admin, _ = _register_and_login("admin")
        b, b_id = _register_and_login("jugador")
        pid = _new_player(b, "DeB")
        nid_b = _make_notification(b_id, player_id=pid)
        ids = [n["id"] for n in client.get(
            f"/api/v1/notifications?player_id={pid}", headers=admin).json()]
        assert str(nid_b) not in ids


# ── Regresión ──────────────────────────────────────────────────

class TestNotificationsRegression:

    def test_filtro_unread_only(self):
        user, uid = _register_and_login("jugador")
        _make_notification(uid, is_read=False)
        _make_notification(uid, is_read=True)
        items = client.get("/api/v1/notifications?unread_only=true", headers=user).json()
        assert len(items) >= 1
        assert all(n["is_read"] is False for n in items)

    def test_unread_count_correcto(self):
        user, uid = _register_and_login("jugador")
        _make_notification(uid, is_read=False)
        _make_notification(uid, is_read=False)
        _make_notification(uid, is_read=True)
        r = client.get("/api/v1/notifications/unread-count", headers=user)
        assert r.json()["count"] == 2

    def test_read_all_solo_afecta_al_usuario(self):
        a, a_id = _register_and_login("jugador")
        b, b_id = _register_and_login("jugador")
        _make_notification(a_id, is_read=False)
        _make_notification(b_id, is_read=False)
        client.put("/api/v1/notifications/read-all", headers=a)
        # A queda sin no leídas; B conserva la suya
        assert client.get("/api/v1/notifications/unread-count", headers=a).json()["count"] == 0
        assert client.get("/api/v1/notifications/unread-count", headers=b).json()["count"] == 1
