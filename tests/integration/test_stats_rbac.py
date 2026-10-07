"""
Tests de integración RBAC del bloque STATS (app/api/v1/stats.py).

Cubren: resolución OWNER-ONLY de TODOS los endpoints `/stats/*` (mismo criterio
que el dashboard: `owner_id == current_user.id`) para TODOS los roles, admin
incluido; comparación/H2H estricta por owner (404 si algún jugador es ajeno,
también para admin); 403 sin el permiso `stats.compare`; y regresiones de
frontera (`/admin/users` sigue siendo GLOBAL para admin, `/players/*` sin
cambios). Además, IDOR en los sub-recursos de player
(/players/{id}/evolution|analytics).
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


def _top_player_ids(headers):
    r = client.get("/api/v1/stats/top", headers=headers)
    assert r.status_code == 200, r.json()
    return {
        entry["player_id"]
        for entries in r.json()["data"].values()
        for entry in entries
    }


def _record_player_ids(headers):
    r = client.get("/api/v1/stats/records", headers=headers)
    assert r.status_code == 200, r.json()
    return {rec["player_id"] for rec in r.json()["data"]}


def _category_player_ids(headers):
    r = client.get("/api/v1/stats/categories", headers=headers)
    assert r.status_code == 200, r.json()
    return {
        tp["player_id"]
        for cat in r.json()["data"]
        for tp in cat["top_players"]
    }


def _evolution_player_ids(headers):
    r = client.get("/api/v1/stats/evolution", headers=headers)
    assert r.status_code == 200, r.json()
    return {e["player_id"] for e in r.json()["data"]}


def _community_player_ids(headers):
    r = client.get("/api/v1/stats/community", headers=headers)
    assert r.status_code == 200, r.json()
    data = r.json()["data"]
    ids = set()
    for key in ("most_points", "best_form", "most_active"):
        if data.get(key):
            ids.add(data[key]["id"])
    best_pair = data.get("best_pair")
    if best_pair:
        ids.add(str(best_pair["player1_id"]))
        ids.add(str(best_pair["player2_id"]))
    return ids


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


# ── AISLAMIENTO POR OWNER (entrenador y jugador) ───────────────

class TestStatsOwnerIsolation:

    @pytest.mark.parametrize("role", ["entrenador", "jugador"])
    def test_listados_nunca_incluyen_jugadores_ajenos(self, role):
        a, _ = _register_and_login(role)
        a1 = _new_player(a, "A1")
        a2 = _new_player(a, "A2")
        b, _ = _register_and_login(role)
        b1 = _new_player(b, "B1")
        b2 = _new_player(b, "B2")

        own = {a1, a2}
        foreign = {b1, b2}

        assert _summary(a)["total_players"] == 2

        rank = set(_ranking_ids(a))
        assert own <= rank
        assert not (foreign & rank)

        assert not (foreign & _top_player_ids(a))
        assert not (foreign & _record_player_ids(a))

        cats = _category_player_ids(a)
        assert own <= cats
        assert not (foreign & cats)

        evo = _evolution_player_ids(a)
        assert own <= evo
        assert not (foreign & evo)

        assert not (foreign & _community_player_ids(a))


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

    def test_h2h_solo_entre_suyos(self):
        coach, _ = _register_and_login("entrenador")
        c1 = _new_player(coach, "Alumno1")
        c2 = _new_player(coach, "Alumno2")
        assert client.get(f"/api/v1/stats/h2h/{c1}/{c2}", headers=coach).status_code == 200

    def test_h2h_jugador_ajeno_404(self):
        coach, _ = _register_and_login("entrenador")
        c1 = _new_player(coach, "Alumno1")
        other, _ = _register_and_login("entrenador")
        p_other = _new_player(other, "Ajeno")
        assert client.get(f"/api/v1/stats/h2h/{c1}/{p_other}", headers=coach).status_code == 404


# ── ADMIN (owner-only para TODOS los roles, admin incluido) ────

class TestAdminStats:
    """El admin NO tiene bypass de lectura en `/stats/*`: igual que el
    dashboard, ve SOLO sus propios jugadores (`owner_id == admin.id`)."""

    def test_listados_solo_propios(self):
        admin, _ = _register_and_login("admin")
        a1 = _new_player(admin, "AdminA")
        a2 = _new_player(admin, "AdminB")
        owner, _ = _register_and_login("jugador")
        f1 = _new_player(owner, "Ajeno1")
        f2 = _new_player(owner, "Ajeno2")

        own = {a1, a2}
        foreign = {f1, f2}

        assert _summary(admin)["total_players"] == 2
        assert set(_ranking_ids(admin)) == own

        assert not (foreign & _top_player_ids(admin))
        assert not (foreign & _record_player_ids(admin))
        assert not (foreign & _category_player_ids(admin))
        assert set(_evolution_player_ids(admin)) == own
        assert not (foreign & _community_player_ids(admin))

    def test_personal_param_no_filtra_datos_globales(self):
        # `personal` es ignorado: ni `personal=false` ni `personal=true` cambian
        # el alcance owner-only del admin.
        admin, _ = _register_and_login("admin")
        own = _new_player(admin, "AdminP")
        owner, _ = _register_and_login("jugador")
        foreign = _new_player(owner, "AjenoP")

        for qs in ("", "&personal=true", "&personal=false"):
            r = client.get(f"/api/v1/stats/ranking?page_size=200{qs}", headers=admin)
            assert r.status_code == 200, r.json()
            ids = {p["id"] for p in r.json()["data"]["players"]}
            assert own in ids
            assert foreign not in ids

        for qs in ("", "?personal=true", "?personal=false"):
            r = client.get(f"/api/v1/stats/summary{qs}", headers=admin)
            assert r.status_code == 200, r.json()
            assert r.json()["data"]["total_players"] == 1

    def test_compare_ajeno_404(self):
        admin, _ = _register_and_login("admin")
        own = _new_player(admin, "AdminOwn")
        own2 = _new_player(admin, "AdminOwn2")

        owner_a, _ = _register_and_login("jugador")
        foreign_a = _new_player(owner_a, "AjenoA")
        owner_b, _ = _register_and_login("jugador")
        foreign_b = _new_player(owner_b, "AjenoB")

        # admin + ajeno → 404 (owner estricto, sin bypass admin)
        assert client.get(f"/api/v1/stats/compare/{own}/{foreign_a}", headers=admin).status_code == 404
        # dos ajenos → 404
        assert client.get(f"/api/v1/stats/compare/{foreign_a}/{foreign_b}", headers=admin).status_code == 404
        # par propio del admin → 200
        assert client.get(f"/api/v1/stats/compare/{own}/{own2}", headers=admin).status_code == 200

    def test_h2h_ajeno_404(self):
        admin, _ = _register_and_login("admin")
        own = _new_player(admin, "AdminOwnH")
        own2 = _new_player(admin, "AdminOwnH2")

        owner_a, _ = _register_and_login("jugador")
        foreign_a = _new_player(owner_a, "AjenoHA")
        owner_b, _ = _register_and_login("jugador")
        foreign_b = _new_player(owner_b, "AjenoHB")

        assert client.get(f"/api/v1/stats/h2h/{own}/{foreign_a}", headers=admin).status_code == 404
        assert client.get(f"/api/v1/stats/h2h/{foreign_a}/{foreign_b}", headers=admin).status_code == 404
        assert client.get(f"/api/v1/stats/h2h/{own}/{own2}", headers=admin).status_code == 200

    def test_compare_inexistente_404(self):
        admin, _ = _register_and_login("admin")
        pa = _new_player(admin, "AdminP")
        r = client.get(f"/api/v1/stats/compare/{pa}/{uuid.uuid4()}", headers=admin)
        assert r.status_code == 404


# ── REGRESIONES DE FRONTERA (no deben cambiar) ─────────────────

class TestBoundaryRegressions:

    def test_admin_users_sigue_siendo_global_para_admin(self):
        admin, _ = _register_and_login("admin")
        _, uid = _register_and_login("jugador")
        db = TestSession()
        email = db.query(UserModel).filter(UserModel.id == uid).first().email
        db.close()
        r = client.get(f"/api/v1/admin/users?search={email}", headers=admin)
        assert r.status_code == 200
        assert r.json()["total"] == 1

    def test_admin_users_403_para_coach_y_jugador(self):
        coach, _ = _register_and_login("entrenador")
        assert client.get("/api/v1/admin/users", headers=coach).status_code == 403
        user, _ = _register_and_login("jugador")
        assert client.get("/api/v1/admin/users", headers=user).status_code == 403

    def test_players_list_sigue_owner_scoped(self):
        a, _ = _register_and_login("entrenador")
        own = _new_player(a, "PropioLista")
        b, _ = _register_and_login("entrenador")
        foreign = _new_player(b, "AjenoLista")

        r = client.get("/api/v1/players/", headers=a)
        assert r.status_code == 200
        ids = {p["id"] for p in r.json()}
        assert own in ids
        assert foreign not in ids

    def test_players_list_admin_owner_scoped(self):
        admin, _ = _register_and_login("admin")
        own = _new_player(admin, "AdminPropioLista")
        owner, _ = _register_and_login("jugador")
        foreign = _new_player(owner, "AjenoAdminLista")

        r = client.get("/api/v1/players/", headers=admin)
        assert r.status_code == 200
        ids = {p["id"] for p in r.json()}
        assert own in ids
        assert foreign not in ids

    def test_admin_lee_detalle_de_jugador_ajeno(self):
        # `/players/{id}` mantiene el alcance admin GLOBAL (solo lectura).
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DetalleAjeno")
        r = client.get(f"/api/v1/players/{pid}", headers=admin)
        assert r.status_code == 200
        assert r.json()["id"] == pid


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
