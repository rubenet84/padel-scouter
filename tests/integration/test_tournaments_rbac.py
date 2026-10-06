"""
Tests de integración RBAC del bloque TOURNAMENTS.

Cubren: permisos tournaments.*, scope (admin GLOBAL; entrenador/jugador OWN),
aislamiento por owner (sin torneo compartido por nombre+fecha), validación de
player_id por owner, IDOR en GET/PUT/DELETE, y la validación mínima de
tournament_id en Matches (sin romper el Bloque 2).

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
TDATE = "2026-10-20"
MATCH_PAYLOAD = {"rival_nombre": "Rival Test", "resultado": "6-4 6-3", "ganado": True}


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


def _new_player(headers, name="Jugador"):
    r = client.post("/api/v1/players/", json={
        "name": name, "category": "3ª Categoría", "stats": {"derecha": 60, "reves": 55},
    }, headers=headers)
    assert r.status_code == 201, r.json()
    return r.json()["id"]


def _unique_name():
    return f"Torneo {uuid.uuid4().hex[:8]}"


def _new_tournament(headers, name=None, player_id=None, fep=100):
    payload = {"name": name or _unique_name(), "date": TDATE, "fep_points": fep}
    if player_id is not None:
        payload["player_id"] = player_id
    return client.post("/api/v1/tournaments/", json=payload, headers=headers)


def _tournament_id(headers, name=None, player_id=None):
    r = _new_tournament(headers, name=name, player_id=player_id)
    assert r.status_code == 201, r.json()
    return r.json()["id"]


# ── CREATE ─────────────────────────────────────────────────────

class TestCreateTournament:

    def test_admin_crea_propio_201(self):
        admin, _ = _register_and_login("admin")
        assert _new_tournament(admin).status_code == 201

    def test_entrenador_crea_201(self):
        coach, _ = _register_and_login("entrenador")
        assert _new_tournament(coach).status_code == 201

    def test_jugador_crea_201(self):
        user, _ = _register_and_login("jugador")
        assert _new_tournament(user).status_code == 201

    def test_crea_con_player_propio_201(self):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        r = _new_tournament(user, player_id=pid)
        assert r.status_code == 201
        assert r.json()["player_id"] == pid

    def test_entrenador_player_ajeno_404(self):
        coach, _ = _register_and_login("entrenador")
        other, _ = _register_and_login("jugador")
        pid_ajeno = _new_player(other, "Ajeno")
        assert _new_tournament(coach, player_id=pid_ajeno).status_code == 404

    def test_jugador_player_ajeno_404(self):
        user, _ = _register_and_login("jugador")
        other, _ = _register_and_login("jugador")
        pid_ajeno = _new_player(other, "Ajeno")
        assert _new_tournament(user, player_id=pid_ajeno).status_code == 404

    def test_admin_player_ajeno_404(self):
        admin, _ = _register_and_login("admin")
        other, _ = _register_and_login("jugador")
        pid_ajeno = _new_player(other, "Ajeno")
        assert _new_tournament(admin, player_id=pid_ajeno).status_code == 404

    def test_cliente_no_fija_owner_id(self):
        user, uid = _register_and_login("jugador")
        r = client.post("/api/v1/tournaments/", json={
            "name": _unique_name(), "date": TDATE,
            "owner_id": str(uuid.uuid4()),  # intento de manipulación
        }, headers=user)
        assert r.status_code == 201
        assert r.json()["owner_id"] == str(uid)


# ── LIST ───────────────────────────────────────────────────────

class TestListTournaments:

    def test_admin_ve_todos(self):
        admin, _ = _register_and_login("admin")
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        ta = _tournament_id(a)
        tb = _tournament_id(b)
        ids = [t["id"] for t in client.get("/api/v1/tournaments/", headers=admin).json()]
        assert ta in ids and tb in ids

    def test_entrenador_solo_propios(self):
        coach_a, _ = _register_and_login("entrenador")
        coach_b, _ = _register_and_login("entrenador")
        ta = _tournament_id(coach_a)
        tb = _tournament_id(coach_b)
        ids = [t["id"] for t in client.get("/api/v1/tournaments/", headers=coach_a).json()]
        assert ta in ids and tb not in ids

    def test_jugador_solo_propios(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        ta = _tournament_id(a)
        tb = _tournament_id(b)
        ids = [t["id"] for t in client.get("/api/v1/tournaments/", headers=a).json()]
        assert ta in ids and tb not in ids

    def test_entrenador_player_id_propio_ok(self):
        coach, _ = _register_and_login("entrenador")
        pid = _new_player(coach, "Alumno")
        r = client.get(f"/api/v1/tournaments/?player_id={pid}", headers=coach)
        assert r.status_code == 200

    def test_entrenador_player_id_ajeno_404(self):
        coach, _ = _register_and_login("entrenador")
        other, _ = _register_and_login("jugador")
        pid_ajeno = _new_player(other, "Ajeno")
        r = client.get(f"/api/v1/tournaments/?player_id={pid_ajeno}", headers=coach)
        assert r.status_code == 404

    def test_jugador_player_id_ajeno_404(self):
        user, _ = _register_and_login("jugador")
        other, _ = _register_and_login("jugador")
        pid_ajeno = _new_player(other, "Ajeno")
        assert client.get(f"/api/v1/tournaments/?player_id={pid_ajeno}", headers=user).status_code == 404

    def test_admin_player_id_otro_owner_ok(self):
        admin, _ = _register_and_login("admin")
        other, _ = _register_and_login("jugador")
        pid = _new_player(other, "DeOtro")
        assert client.get(f"/api/v1/tournaments/?player_id={pid}", headers=admin).status_code == 200


# ── GET BY ID ──────────────────────────────────────────────────

class TestGetTournament:

    def test_admin_propio_200(self):
        admin, _ = _register_and_login("admin")
        tid = _tournament_id(admin)
        assert client.get(f"/api/v1/tournaments/{tid}", headers=admin).status_code == 200

    def test_admin_ajeno_200(self):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        tid = _tournament_id(owner)
        r = client.get(f"/api/v1/tournaments/{tid}", headers=admin)
        assert r.status_code == 200
        assert r.json()["id"] == tid

    def test_entrenador_propio_200(self):
        coach, _ = _register_and_login("entrenador")
        tid = _tournament_id(coach)
        assert client.get(f"/api/v1/tournaments/{tid}", headers=coach).status_code == 200

    def test_entrenador_ajeno_404(self):
        coach, _ = _register_and_login("entrenador")
        owner, _ = _register_and_login("jugador")
        tid = _tournament_id(owner)
        r = client.get(f"/api/v1/tournaments/{tid}", headers=coach)
        assert r.status_code == 404
        assert tid not in r.text  # no revela datos del torneo ajeno

    def test_jugador_propio_200(self):
        user, _ = _register_and_login("jugador")
        tid = _tournament_id(user)
        assert client.get(f"/api/v1/tournaments/{tid}", headers=user).status_code == 200

    def test_jugador_ajeno_404(self):
        user, _ = _register_and_login("jugador")
        owner, _ = _register_and_login("jugador")
        tid = _tournament_id(owner)
        assert client.get(f"/api/v1/tournaments/{tid}", headers=user).status_code == 404

    def test_inexistente_404(self):
        user, _ = _register_and_login("jugador")
        assert client.get(f"/api/v1/tournaments/{uuid.uuid4()}", headers=user).status_code == 404


# ── UPDATE ─────────────────────────────────────────────────────

class TestUpdateTournament:

    def test_admin_propio_200(self):
        admin, _ = _register_and_login("admin")
        tid = _tournament_id(admin)
        assert client.put(f"/api/v1/tournaments/{tid}", json={"fep_points": 250}, headers=admin).status_code == 200

    def test_admin_ajeno_200(self):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        tid = _tournament_id(owner)
        assert client.put(f"/api/v1/tournaments/{tid}", json={"fep_points": 250}, headers=admin).status_code == 200

    def test_entrenador_propio_200(self):
        coach, _ = _register_and_login("entrenador")
        tid = _tournament_id(coach)
        assert client.put(f"/api/v1/tournaments/{tid}", json={"fep_points": 250}, headers=coach).status_code == 200

    def test_entrenador_ajeno_404(self):
        coach, _ = _register_and_login("entrenador")
        owner, _ = _register_and_login("jugador")
        tid = _tournament_id(owner)
        assert client.put(f"/api/v1/tournaments/{tid}", json={"fep_points": 250}, headers=coach).status_code == 404

    def test_jugador_propio_200(self):
        user, _ = _register_and_login("jugador")
        tid = _tournament_id(user)
        assert client.put(f"/api/v1/tournaments/{tid}", json={"fep_points": 250}, headers=user).status_code == 200

    def test_jugador_ajeno_404(self):
        user, _ = _register_and_login("jugador")
        owner, _ = _register_and_login("jugador")
        tid = _tournament_id(owner)
        assert client.put(f"/api/v1/tournaments/{tid}", json={"fep_points": 250}, headers=user).status_code == 404


# ── DELETE ─────────────────────────────────────────────────────

class TestDeleteTournament:

    def test_admin_propio_204(self):
        admin, _ = _register_and_login("admin")
        tid = _tournament_id(admin)
        assert client.delete(f"/api/v1/tournaments/{tid}", headers=admin).status_code == 204

    def test_admin_ajeno_204(self):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        tid = _tournament_id(owner)
        assert client.delete(f"/api/v1/tournaments/{tid}", headers=admin).status_code == 204

    def test_entrenador_propio_204(self):
        coach, _ = _register_and_login("entrenador")
        tid = _tournament_id(coach)
        assert client.delete(f"/api/v1/tournaments/{tid}", headers=coach).status_code == 204

    def test_entrenador_ajeno_404(self):
        coach, _ = _register_and_login("entrenador")
        owner, _ = _register_and_login("jugador")
        tid = _tournament_id(owner)
        assert client.delete(f"/api/v1/tournaments/{tid}", headers=coach).status_code == 404

    def test_jugador_propio_204(self):
        user, _ = _register_and_login("jugador")
        tid = _tournament_id(user)
        assert client.delete(f"/api/v1/tournaments/{tid}", headers=user).status_code == 204

    def test_jugador_ajeno_404(self):
        user, _ = _register_and_login("jugador")
        owner, _ = _register_and_login("jugador")
        tid = _tournament_id(owner)
        assert client.delete(f"/api/v1/tournaments/{tid}", headers=user).status_code == 404

    def test_con_matches_400(self):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        tid = _tournament_id(user, player_id=pid)
        # crear un match asociado al torneo (mismo owner)
        r = client.post(f"/api/v1/players/{pid}/matches",
                        json={**MATCH_PAYLOAD, "tournament_id": tid}, headers=user)
        assert r.status_code == 201, r.json()
        assert client.delete(f"/api/v1/tournaments/{tid}", headers=user).status_code == 400


# ── MATCH + TOURNAMENT (no romper Bloque 2) ────────────────────

class TestMatchTournamentOwnership:

    def test_match_sin_tournament_ok(self):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        assert client.post(f"/api/v1/players/{pid}/matches", json=MATCH_PAYLOAD, headers=user).status_code == 201

    def test_match_con_tournament_mismo_owner_ok(self):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user, "Mio")
        tid = _tournament_id(user, player_id=pid)
        r = client.post(f"/api/v1/players/{pid}/matches",
                        json={**MATCH_PAYLOAD, "tournament_id": tid}, headers=user)
        assert r.status_code == 201

    def test_match_con_tournament_otro_owner_404(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_a = _new_player(a, "DeA")
        tid_b = _tournament_id(b)  # torneo del owner B
        r = client.post(f"/api/v1/players/{pid_a}/matches",
                        json={**MATCH_PAYLOAD, "tournament_id": tid_b}, headers=a)
        assert r.status_code == 404

    def test_admin_global_matches_ok(self):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DeOwner")
        tid = _tournament_id(owner, player_id=pid)
        r = client.post(f"/api/v1/players/{pid}/matches",
                        json={**MATCH_PAYLOAD, "tournament_id": tid}, headers=admin)
        assert r.status_code == 201


# ── DUPLICADOS POR OWNER ───────────────────────────────────────

class TestDuplicateByOwner:

    def test_mismo_nombre_date_distintos_owners_dos_torneos(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        name = _unique_name()
        ta = _new_tournament(a, name=name).json()["id"]
        tb = _new_tournament(b, name=name).json()["id"]
        assert ta != tb  # NO se comparte fila entre owners

    def test_mismo_owner_reutiliza(self):
        a, _ = _register_and_login("jugador")
        name = _unique_name()
        t1 = _new_tournament(a, name=name).json()["id"]
        t2 = _new_tournament(a, name=name).json()["id"]
        assert t1 == t2  # dentro del mismo owner se reutiliza (comportamiento actual)


# ── AUTH ───────────────────────────────────────────────────────

class TestTournamentAuth:

    def test_sin_jwt_401(self):
        assert client.get("/api/v1/tournaments/").status_code == 401

    def test_usuario_inactivo_401(self):
        headers, uid = _register_and_login("jugador")
        db = TestSession()
        u = db.query(UserModel).filter(UserModel.id == uid).first()
        u.is_active = False
        db.commit()
        db.close()
        assert client.get("/api/v1/tournaments/", headers=headers).status_code == 401
