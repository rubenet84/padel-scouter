"""
Tests de integración RBAC del panel de administración de usuarios.

Cubren: autenticación (401), RBAC (admin 200 / entrenador y jugador 403),
listado con búsqueda/filtros/paginación, detalle, cambio de rol (jugador<->entrenador),
suspensión/reactivación, auditoría, protección del último admin y anti-escalada.

Requieren PostgreSQL local en localhost:5432.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
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
ADMIN = "/api/v1/admin"


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
    uid = user.id
    db.close()
    login = client.post("/api/v1/auth/login", json={"email": email, "password": STRONG_PASSWORD})
    assert login.status_code == 200, login.json()
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, uid


def _audit_count(target_id, action=None) -> int:
    db = TestSession()
    q = "SELECT COUNT(*) FROM audit_log WHERE target_id = :t"
    params = {"t": target_id}
    if action:
        q += " AND action = :a"
        params["a"] = action
    n = db.execute(text(q), params).scalar()
    db.close()
    return n


def _active_admins() -> int:
    db = TestSession()
    n = db.execute(text("SELECT COUNT(*) FROM users WHERE role='admin' AND is_active=true")).scalar()
    db.close()
    return n


# ── Autenticación ──────────────────────────────────────────────

class TestAdminAuth:

    def test_sin_token_401(self):
        assert client.get(f"{ADMIN}/users").status_code == 401

    def test_token_invalido_401(self):
        assert client.get(f"{ADMIN}/users", headers={"Authorization": "Bearer garbage.token"}).status_code == 401


# ── RBAC ───────────────────────────────────────────────────────

class TestAdminRBAC:

    def test_admin_200(self):
        admin, _ = _register_and_login("admin")
        assert client.get(f"{ADMIN}/users", headers=admin).status_code == 200

    def test_entrenador_403(self):
        coach, _ = _register_and_login("entrenador")
        assert client.get(f"{ADMIN}/users", headers=coach).status_code == 403

    def test_jugador_403(self):
        user, _ = _register_and_login("jugador")
        assert client.get(f"{ADMIN}/users", headers=user).status_code == 403


# ── Listado + búsqueda + filtros + paginación ──────────────────

class TestAdminListing:

    def test_listado_basico(self):
        admin, _ = _register_and_login("admin")
        r = client.get(f"{ADMIN}/users", headers=admin)
        assert r.status_code == 200
        body = r.json()
        assert {"items", "total", "page", "page_size", "total_pages"} <= set(body.keys())
        assert isinstance(body["items"], list)

    def test_paginacion_y_total(self):
        admin, _ = _register_and_login("admin")
        prefix = f"pg{uuid.uuid4().hex[:6]}"
        for i in range(3):
            client.post("/api/v1/auth/register", json={
                "email": f"{prefix}_{i}@padel.com", "username": f"{prefix}_{i}",
                "password": STRONG_PASSWORD,
            })
        r = client.get(f"{ADMIN}/users?search={prefix}&page=1&page_size=2", headers=admin)
        body = r.json()
        assert body["total"] == 3
        assert body["total_pages"] == 2
        assert len(body["items"]) == 2
        r2 = client.get(f"{ADMIN}/users?search={prefix}&page=2&page_size=2", headers=admin)
        assert len(r2.json()["items"]) == 1

    def test_busqueda_por_email(self):
        admin, _ = _register_and_login("admin")
        _, uid = _register_and_login("jugador")
        db = TestSession()
        email = db.query(UserModel).filter(UserModel.id == uid).first().email
        db.close()
        r = client.get(f"{ADMIN}/users?search={email}", headers=admin)
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["email"] == email

    def test_busqueda_por_username(self):
        admin, _ = _register_and_login("admin")
        email = f"un_{uuid.uuid4().hex[:8]}@padel.com"
        username = f"uname_{uuid.uuid4().hex[:8]}"
        client.post("/api/v1/auth/register", json={"email": email, "username": username, "password": STRONG_PASSWORD})
        r = client.get(f"{ADMIN}/users?search={username}", headers=admin)
        assert any(u["username"] == username for u in r.json()["items"])

    def test_filtro_por_rol(self):
        admin, _ = _register_and_login("admin")
        _register_and_login("entrenador")
        r = client.get(f"{ADMIN}/users?role=entrenador&page_size=100", headers=admin)
        assert r.status_code == 200
        assert all(u["role"] == "entrenador" for u in r.json()["items"])

    def test_filtro_por_estado(self):
        admin, _ = _register_and_login("admin")
        r = client.get(f"{ADMIN}/users?is_active=false&page_size=100", headers=admin)
        assert r.status_code == 200
        assert all(u["is_active"] is False for u in r.json()["items"])

    def test_combinacion_filtros(self):
        admin, _ = _register_and_login("admin")
        user, uid = _register_and_login("jugador")
        db = TestSession()
        email = db.query(UserModel).filter(UserModel.id == uid).first().email
        db.close()
        r = client.get(f"{ADMIN}/users?role=jugador&is_active=true&search={email}", headers=admin)
        assert r.json()["total"] == 1

    def test_rol_query_invalido_422(self):
        admin, _ = _register_and_login("admin")
        assert client.get(f"{ADMIN}/users?role=superuser", headers=admin).status_code == 422


# ── Detalle ────────────────────────────────────────────────────

class TestAdminDetail:

    def test_detalle_200_sin_secretos(self):
        admin, _ = _register_and_login("admin")
        user, uid = _register_and_login("jugador")
        r = client.get(f"{ADMIN}/users/{uid}", headers=admin)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == str(uid)
        assert "hashed_password" not in body
        assert "created_at" in body

    def test_detalle_counts(self):
        admin, _ = _register_and_login("admin")
        user, uid = _register_and_login("jugador")
        client.post("/api/v1/players/", json={"name": "P1", "category": "3ª Categoría"}, headers=user)
        r = client.get(f"{ADMIN}/users/{uid}", headers=admin)
        assert r.json()["players_count"] == 1

    def test_detalle_inexistente_404(self):
        admin, _ = _register_and_login("admin")
        assert client.get(f"{ADMIN}/users/{uuid.uuid4()}", headers=admin).status_code == 404


# ── Cambio de rol ──────────────────────────────────────────────

class TestAdminRoleChange:

    def test_jugador_a_entrenador(self):
        admin, _ = _register_and_login("admin")
        _, uid = _register_and_login("jugador")
        r = client.patch(f"{ADMIN}/users/{uid}/role", json={"role": "entrenador"}, headers=admin)
        assert r.status_code == 200
        assert r.json()["role"] == "entrenador"
        assert _audit_count(uid, "role_changed") == 1

    def test_entrenador_a_jugador(self):
        admin, _ = _register_and_login("admin")
        _, uid = _register_and_login("entrenador")
        r = client.patch(f"{ADMIN}/users/{uid}/role", json={"role": "jugador"}, headers=admin)
        assert r.status_code == 200
        assert r.json()["role"] == "jugador"

    def test_admin_rechazado_422(self):
        admin, _ = _register_and_login("admin")
        _, uid = _register_and_login("jugador")
        assert client.patch(f"{ADMIN}/users/{uid}/role", json={"role": "admin"}, headers=admin).status_code == 422

    def test_rol_invalido_422(self):
        admin, _ = _register_and_login("admin")
        _, uid = _register_and_login("jugador")
        assert client.patch(f"{ADMIN}/users/{uid}/role", json={"role": "superuser"}, headers=admin).status_code == 422

    def test_no_admin_403(self):
        coach, _ = _register_and_login("entrenador")
        _, uid = _register_and_login("jugador")
        assert client.patch(f"{ADMIN}/users/{uid}/role", json={"role": "entrenador"}, headers=coach).status_code == 403

    def test_inexistente_404(self):
        admin, _ = _register_and_login("admin")
        assert client.patch(f"{ADMIN}/users/{uuid.uuid4()}/role", json={"role": "entrenador"}, headers=admin).status_code == 404

    def test_self_demotion_403(self):
        admin, aid = _register_and_login("admin")
        assert client.patch(f"{ADMIN}/users/{aid}/role", json={"role": "jugador"}, headers=admin).status_code == 403

    def test_admin_objetivo_403(self):
        admin, _ = _register_and_login("admin")
        _, other_admin = _register_and_login("admin")
        assert client.patch(f"{ADMIN}/users/{other_admin}/role", json={"role": "entrenador"}, headers=admin).status_code == 403

    def test_sin_cambio_no_audita(self):
        admin, _ = _register_and_login("admin")
        _, uid = _register_and_login("jugador")
        r = client.patch(f"{ADMIN}/users/{uid}/role", json={"role": "jugador"}, headers=admin)
        assert r.status_code == 200
        assert r.json()["role"] == "jugador"
        assert _audit_count(uid, "role_changed") == 0


# ── Estado (suspender/reactivar) ───────────────────────────────

class TestAdminStatus:

    def test_suspender_y_reactivar(self):
        admin, _ = _register_and_login("admin")
        _, uid = _register_and_login("jugador")
        r = client.patch(f"{ADMIN}/users/{uid}/status", json={"is_active": False}, headers=admin)
        assert r.status_code == 200 and r.json()["is_active"] is False
        assert _audit_count(uid, "user_suspended") == 1
        r = client.patch(f"{ADMIN}/users/{uid}/status", json={"is_active": True}, headers=admin)
        assert r.status_code == 200 and r.json()["is_active"] is True
        assert _audit_count(uid, "user_reactivated") == 1

    def test_suspendido_no_puede_autenticarse(self):
        admin, _ = _register_and_login("admin")
        email = f"susp_{uuid.uuid4().hex[:8]}@padel.com"
        client.post("/api/v1/auth/register", json={"email": email, "username": f"susp_{uuid.uuid4().hex[:8]}", "password": STRONG_PASSWORD})
        db = TestSession()
        uid = db.query(UserModel).filter(UserModel.email == email).first().id
        db.close()
        client.patch(f"{ADMIN}/users/{uid}/status", json={"is_active": False}, headers=admin)
        assert client.post("/api/v1/auth/login", json={"email": email, "password": STRONG_PASSWORD}).status_code in (400, 401)

    def test_inexistente_404(self):
        admin, _ = _register_and_login("admin")
        assert client.patch(f"{ADMIN}/users/{uuid.uuid4()}/status", json={"is_active": False}, headers=admin).status_code == 404

    def test_no_admin_403(self):
        coach, _ = _register_and_login("entrenador")
        _, uid = _register_and_login("jugador")
        assert client.patch(f"{ADMIN}/users/{uid}/status", json={"is_active": False}, headers=coach).status_code == 403

    def test_sin_cambio_no_audita(self):
        admin, _ = _register_and_login("admin")
        _, uid = _register_and_login("jugador")  # activo por defecto
        r = client.patch(f"{ADMIN}/users/{uid}/status", json={"is_active": True}, headers=admin)
        assert r.status_code == 200
        assert _audit_count(uid, "user_reactivated") == 0
        assert _audit_count(uid, "user_suspended") == 0

    def test_ultimo_admin_no_se_puede_suspender(self):
        # El único admin activo necesariamente es el actor → lo cubre self-suspend (F2).
        # La protección de "último admin" (400) permanece en backend como defensa en profundidad.
        admin, aid = _register_and_login("admin")
        r = client.patch(f"{ADMIN}/users/{aid}/status", json={"is_active": False}, headers=admin)
        assert r.status_code == 403
        db = TestSession()
        assert db.query(UserModel).filter(UserModel.id == aid).first().is_active is True
        db.close()

    def test_admin_suspende_a_otro_admin_200(self):
        # TEST 1: A suspende a B → 200; queda exactamente 1 admin activo.
        admin_a, aid_a = _register_and_login("admin")
        _, aid_b = _register_and_login("admin")
        # Aislar: dejar SOLO a A y B como admins activos
        db = TestSession()
        db.execute(text("UPDATE users SET is_active=false WHERE role='admin' AND is_active=true AND id NOT IN (:a, :b)"), {"a": aid_a, "b": aid_b})
        db.commit()
        db.close()
        assert _active_admins() == 2
        r = client.patch(f"{ADMIN}/users/{aid_b}/status", json={"is_active": False}, headers=admin_a)
        assert r.status_code == 200
        db = TestSession()
        a = db.query(UserModel).filter(UserModel.id == aid_a).first()
        b = db.query(UserModel).filter(UserModel.id == aid_b).first()
        assert a.is_active is True and b.is_active is False
        db.close()
        assert _active_admins() == 1

    def test_self_suspend_403(self):
        # TEST 2: admin único intenta suspenderse → 403; sigue activo (no 400).
        admin, aid = _register_and_login("admin")
        r = client.patch(f"{ADMIN}/users/{aid}/status", json={"is_active": False}, headers=admin)
        assert r.status_code == 403
        db = TestSession()
        assert db.query(UserModel).filter(UserModel.id == aid).first().is_active is True
        db.close()

    def test_self_suspend_con_otro_admin_403(self):
        # TEST 3: admin con otro admin presente intenta suspenderse → 403; ambos activos.
        admin_a, aid_a = _register_and_login("admin")
        _, aid_b = _register_and_login("admin")
        r = client.patch(f"{ADMIN}/users/{aid_a}/status", json={"is_active": False}, headers=admin_a)
        assert r.status_code == 403
        db = TestSession()
        assert db.query(UserModel).filter(UserModel.id == aid_a).first().is_active is True
        assert db.query(UserModel).filter(UserModel.id == aid_b).first().is_active is True
        db.close()

    def test_self_reactivate_noop_200(self):
        # TEST 4: reactivarse estando ya activo sigue siendo no-op 200 (no se bloquea).
        admin, aid = _register_and_login("admin")
        r = client.patch(f"{ADMIN}/users/{aid}/status", json={"is_active": True}, headers=admin)
        assert r.status_code == 200
        assert r.json()["is_active"] is True


# ── Estadísticas ───────────────────────────────────────────────

class TestAdminStats:

    def test_stats_estructura(self):
        admin, _ = _register_and_login("admin")
        r = client.get(f"{ADMIN}/users/stats", headers=admin)
        assert r.status_code == 200
        body = r.json()
        assert {"total", "admins", "entrenadores", "jugadores", "suspended"} <= set(body.keys())
        assert body["total"] >= 1
        assert body["admins"] >= 1

    def test_stats_no_admin_403(self):
        user, _ = _register_and_login("jugador")
        assert client.get(f"{ADMIN}/users/stats", headers=user).status_code == 403


# ── Seguridad / anti-escalada ──────────────────────────────────

class TestAdminSecurity:

    def test_jugador_no_puede_escalar(self):
        user, _ = _register_and_login("jugador")
        _, uid = _register_and_login("jugador")
        # jugador intenta cambiar el rol de otro → 403 (sin permiso)
        assert client.patch(f"{ADMIN}/users/{uid}/role", json={"role": "entrenador"}, headers=user).status_code == 403

    def test_jugador_no_accede_a_detalle(self):
        user, _ = _register_and_login("jugador")
        _, uid = _register_and_login("admin")
        assert client.get(f"{ADMIN}/users/{uid}", headers=user).status_code == 403

    def test_no_existe_endpoint_delete(self):
        admin, _ = _register_and_login("admin")
        _, uid = _register_and_login("jugador")
        assert client.delete(f"{ADMIN}/users/{uid}", headers=admin).status_code == 405
