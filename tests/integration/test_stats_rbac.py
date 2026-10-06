"""
Tests de integración RBAC del bloque STATS (app/api/v1/stats.py).

Cubren: aislamiento por owner en `/stats/*`, scope global de admin,
comparaciones cross-owner (admin) y 404 para jugadores inaccesibles,
más IDOR en los sub-recursos de player (/players/{id}/evolution|analytics).
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


@pytest.fixture(scope="module", autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    yield


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


def _ranking_ids(headers):
    r = client.get("/api/v1/stats/ranking?page_size=200", headers=headers)
    assert r.status_code == 200, r.json()
    return [p["id"] for p in r.json()["data"]["players"]]


def _summary(headers):
    r = client.get("/api/v1/stats/summary", headers=headers)
    assert r.status_code == 200, r.json()
    return r.json()["data"]


def _summary_personal(headers):
    r = client.get("/api/v1/stats/summary?personal=true", headers=headers)
    assert r.status_code == 200, r.json()
    return r.json()["data"]


def _ranking_ids_personal(headers):
    r = client.get("/api/v1/stats/ranking?page_size=200&personal=true", headers=headers)
    assert r.status_code == 200, r.json()
    return [p["id"] for p in r.json()["data"]["players"]]


# ── JUGADOR ────────────────────────────────────────────────────

class TestJugadorStats:

    def test_solo_ve_sus_estadisticas(self):
        user, _ = _register_and_login("jugador")
        p1 = _new_player(user, "Mio1")
        p2 = _new_player(user, "Mio2")
        # otro owner con su jugador
        other, _ = _register_and_login("jugador")
        p_other = _new_player(other, "Ajeno")

        ids = _ranking_ids(user)
        assert p1 in ids and p2 in ids
        assert p_other not in ids
        assert _summary(user)["total_players"] == 2

    def test_compare_dos_propios_denegado_403(self):
        # jugador NO tiene stats.compare (matriz congelada) → 403.
        # El ownership no se evalúa: el guard de permiso corta antes.
        user, _ = _register_and_login("jugador")
        p1 = _new_player(user, "PA")
        p2 = _new_player(user, "PB")
        r = client.get(f"/api/v1/stats/compare/{p1}/{p2}", headers=user)
        assert r.status_code == 403

    def test_compare_jugador_ajeno_denegado_403(self):
        # También con un jugador ajeno → 403 (permiso antes que ownership; no revela)
        user, _ = _register_and_login("jugador")
        p1 = _new_player(user, "PA")
        other, _ = _register_and_login("jugador")
        p_other = _new_player(other, "Ajeno")
        r = client.get(f"/api/v1/stats/compare/{p1}/{p_other}", headers=user)
        assert r.status_code == 403

    def test_h2h_dos_propios_denegado_403(self):
        user, _ = _register_and_login("jugador")
        p1 = _new_player(user, "PA")
        p2 = _new_player(user, "PB")
        r = client.get(f"/api/v1/stats/h2h/{p1}/{p2}", headers=user)
        assert r.status_code == 403

    def test_h2h_jugador_ajeno_denegado_403(self):
        user, _ = _register_and_login("jugador")
        p1 = _new_player(user, "PA")
        other, _ = _register_and_login("jugador")
        p_other = _new_player(other, "Ajeno")
        r = client.get(f"/api/v1/stats/h2h/{p1}/{p_other}", headers=user)
        assert r.status_code == 403


# ── ENTRENADOR ─────────────────────────────────────────────────

class TestEntrenadorStats:

    def test_solo_ve_sus_estadisticas(self):
        coach, _ = _register_and_login("entrenador")
        c1 = _new_player(coach, "Alumno1")
        c2 = _new_player(coach, "Alumno2")
        other, _ = _register_and_login("entrenador")
        p_other = _new_player(other, "Ajeno")

        ids = _ranking_ids(coach)
        assert c1 in ids and c2 in ids
        assert p_other not in ids

    def test_compare_solo_entre_suyos(self):
        coach, _ = _register_and_login("entrenador")
        c1 = _new_player(coach, "Alumno1")
        c2 = _new_player(coach, "Alumno2")
        assert client.get(f"/api/v1/stats/compare/{c1}/{c2}", headers=coach).status_code == 200

        other, _ = _register_and_login("entrenador")
        p_other = _new_player(other, "Ajeno")
        assert client.get(f"/api/v1/stats/compare/{c1}/{p_other}", headers=coach).status_code == 404

    def test_h2h_jugador_ajeno_404(self):
        coach, _ = _register_and_login("entrenador")
        c1 = _new_player(coach, "Alumno1")
        other, _ = _register_and_login("entrenador")
        p_other = _new_player(other, "Ajeno")
        assert client.get(f"/api/v1/stats/h2h/{c1}/{p_other}", headers=coach).status_code == 404


# ── ADMIN ──────────────────────────────────────────────────────

class TestAdminStats:

    def test_ve_datos_de_multiples_owners(self):
        admin, _ = _register_and_login("admin")
        owner_a, _ = _register_and_login("jugador")
        owner_b, _ = _register_and_login("jugador")
        pa = _new_player(owner_a, "OwnerA")
        pb = _new_player(owner_b, "OwnerB")

        ids = _ranking_ids(admin)
        assert pa in ids      # jugador de otro owner
        assert pb in ids      # jugador de otro owner distinto

    def test_summary_personal_solo_sus_jugadores(self):
        # Con personal=true el resumen del admin cuenta SOLO sus jugadores.
        admin, _ = _register_and_login("admin")
        _new_player(admin, "AdminPropio1")
        _new_player(admin, "AdminPropio2")
        owner, _ = _register_and_login("jugador")
        _new_player(owner, "Ajeno")
        assert _summary_personal(admin)["total_players"] == 2

    def test_ranking_personal_excluye_ajenos(self):
        # Con personal=true el ranking del admin excluye jugadores ajenos.
        admin, _ = _register_and_login("admin")
        propio = _new_player(admin, "AdminPropio")
        owner, _ = _register_and_login("jugador")
        ajeno = _new_player(owner, "Ajeno")
        ids = _ranking_ids_personal(admin)
        assert propio in ids
        assert ajeno not in ids

    def test_compare_cross_owner_ok(self):
        admin, _ = _register_and_login("admin")
        owner_a, _ = _register_and_login("jugador")
        owner_b, _ = _register_and_login("jugador")
        pa = _new_player(owner_a, "OwnerA")
        pb = _new_player(owner_b, "OwnerB")
        assert client.get(f"/api/v1/stats/compare/{pa}/{pb}", headers=admin).status_code == 200

    def test_h2h_cross_owner_ok(self):
        admin, _ = _register_and_login("admin")
        owner_a, _ = _register_and_login("jugador")
        owner_b, _ = _register_and_login("jugador")
        pa = _new_player(owner_a, "OwnerA")
        pb = _new_player(owner_b, "OwnerB")
        assert client.get(f"/api/v1/stats/h2h/{pa}/{pb}", headers=admin).status_code == 200

    def test_compare_inexistente_404(self):
        admin, _ = _register_and_login("admin")
        pa = _new_player(admin, "AdminP")
        r = client.get(f"/api/v1/stats/compare/{pa}/{uuid.uuid4()}", headers=admin)
        assert r.status_code == 404


# ── SUB-RECURSOS DE PLAYER (IDOR + admin global) ───────────────

class TestPlayerSubresourcesRBAC:

    def test_idor_evolution_404(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player(b, "Victima")
        assert client.get(f"/api/v1/players/{pid_b}/evolution", headers=a).status_code == 404

    def test_idor_analytics_404(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player(b, "Victima")
        assert client.get(f"/api/v1/players/{pid_b}/analytics", headers=a).status_code == 404

    def test_admin_accede_a_jugador_ajeno(self):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DeOwner")
        assert client.get(f"/api/v1/players/{pid}/stats", headers=admin).status_code == 200
        assert client.get(f"/api/v1/players/{pid}/evolution", headers=admin).status_code == 200
        assert client.get(f"/api/v1/players/{pid}/analytics", headers=admin).status_code == 200
