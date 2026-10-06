"""
Tests de integración RBAC del bloque MATCHES (app/api/v1/players.py).

Cubren: permisos, ownership vía player de la URL, IDOR por match_id, acceso
global de admin, restricción de compañero (mismo owner, también para admin),
no-manipulación de propiedad, y regresión (rondas, notificaciones, borrado).
Requieren PostgreSQL local en localhost:5432.
"""
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.infrastructure.database.models import Base, UserModel, PlayerModel, MatchModel, TournamentModel, NotificationModel
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
MATCH_PAYLOAD = {"rival_nombre": "Rival Test", "resultado": "6-4 6-3", "ganado": True}


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


def _create_match(headers, player_id, **overrides):
    payload = dict(MATCH_PAYLOAD)
    payload.update(overrides)
    return client.post(f"/api/v1/players/{player_id}/matches", json=payload, headers=headers)


def _new_match(headers, player_id, **overrides):
    r = _create_match(headers, player_id, **overrides)
    assert r.status_code == 201, r.json()
    return r.json()["id"]


# ── JUGADOR ────────────────────────────────────────────────────

class TestJugadorMatches:

    def test_crud_propio(self):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user)
        # create
        mid = _new_match(user, pid)
        # list
        listed = client.get(f"/api/v1/players/{pid}/matches", headers=user)
        assert listed.status_code == 200
        assert mid in [m["id"] for m in listed.json()]
        # update
        upd = client.put(f"/api/v1/players/{pid}/matches/{mid}", json={
            "rival_nombre": "Rival Editado", "resultado": "7-5 6-4", "ganado": False,
        }, headers=user)
        assert upd.status_code == 200
        # delete
        assert client.delete(f"/api/v1/players/{pid}/matches/{mid}", headers=user).status_code == 204
        after = client.get(f"/api/v1/players/{pid}/matches", headers=user)
        assert mid not in [m["id"] for m in after.json()]

    def test_no_accede_player_ajeno(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player(b, "DeB")
        assert client.get(f"/api/v1/players/{pid_b}/matches", headers=a).status_code == 404

    def test_idor_match_ajeno_con_player_propio(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_a = _new_player(a, "DeA")
        pid_b = _new_player(b, "DeB")
        mid_b = _new_match(b, pid_b)
        # match ajeno + player propio → 404 en update y delete
        assert client.put(f"/api/v1/players/{pid_a}/matches/{mid_b}", json=MATCH_PAYLOAD, headers=a).status_code == 404
        assert client.delete(f"/api/v1/players/{pid_a}/matches/{mid_b}", headers=a).status_code == 404


# ── ENTRENADOR ─────────────────────────────────────────────────

class TestEntrenadorMatches:

    def test_operaciones_sobre_sus_jugadores(self):
        coach, _ = _register_and_login("entrenador")
        pid = _new_player(coach, "Alumno")
        mid = _new_match(coach, pid)
        assert client.get(f"/api/v1/players/{pid}/matches", headers=coach).status_code == 200
        assert client.put(f"/api/v1/players/{pid}/matches/{mid}", json={
            "rival_nombre": "Otro Rival", "resultado": "6-0 6-1", "ganado": True,
        }, headers=coach).status_code == 200
        assert client.delete(f"/api/v1/players/{pid}/matches/{mid}", headers=coach).status_code == 204

    def test_partner_mismo_owner_ok(self):
        coach, _ = _register_and_login("entrenador")
        p1 = _new_player(coach, "Alumno1")
        p2 = _new_player(coach, "Alumno2")
        r = _create_match(coach, p1, partner_id=p2)
        assert r.status_code == 201
        assert r.json()["partner_id"] == p2

    def test_no_accede_player_ajeno(self):
        a, _ = _register_and_login("entrenador")
        b, _ = _register_and_login("entrenador")
        pid_b = _new_player(b, "DeB")
        assert client.get(f"/api/v1/players/{pid_b}/matches", headers=a).status_code == 404


# ── ADMIN ──────────────────────────────────────────────────────

class TestAdminMatches:

    def test_admin_no_gestiona_partidos_ajenos_404(self):
        # Escritura owner-only: el admin mantiene lectura global pero NO puede
        # crear/editar/borrar partidos de jugadores ajenos.
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DeOwner")
        mid = _new_match(owner, pid)

        # listar: lectura global del admin → 200
        listed = client.get(f"/api/v1/players/{pid}/matches", headers=admin)
        assert listed.status_code == 200
        assert mid in [m["id"] for m in listed.json()]
        # crear en jugador ajeno → 404
        assert _create_match(admin, pid).status_code == 404
        # actualizar partido ajeno → 404
        assert client.put(f"/api/v1/players/{pid}/matches/{mid}", json={
            "rival_nombre": "Admin Edit", "resultado": "6-3 6-2", "ganado": True,
        }, headers=admin).status_code == 404
        # borrar partido ajeno → 404
        assert client.delete(f"/api/v1/players/{pid}/matches/{mid}", headers=admin).status_code == 404


# ── ADMIN: LECTURA GLOBAL vs ESCRITURA OWNER-ONLY ──────────────

class TestAdminEscrituraOwnership:
    """El admin conserva lectura global pero no puede mutar partidos ajenos."""

    def test_admin_get_ajeno_200(self):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DeOwner")
        _new_match(owner, pid)
        assert client.get(f"/api/v1/players/{pid}/matches", headers=admin).status_code == 200

    def test_admin_create_match_ajeno_404(self):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DeOwner")
        assert _create_match(admin, pid).status_code == 404

    def test_admin_update_match_ajeno_404(self):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DeOwner")
        mid = _new_match(owner, pid)
        r = client.put(f"/api/v1/players/{pid}/matches/{mid}", json={
            "rival_nombre": "Admin Edit", "resultado": "6-3 6-2", "ganado": True,
        }, headers=admin)
        assert r.status_code == 404

    def test_admin_delete_match_ajeno_404(self):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player(owner, "DeOwner")
        mid = _new_match(owner, pid)
        assert client.delete(f"/api/v1/players/{pid}/matches/{mid}", headers=admin).status_code == 404

    def test_admin_crud_propio_ok(self):
        admin, _ = _register_and_login("admin")
        pid = _new_player(admin, "AdminP")
        mid = _new_match(admin, pid)
        assert client.put(f"/api/v1/players/{pid}/matches/{mid}", json={
            "rival_nombre": "Propio Edit", "resultado": "6-1 6-1", "ganado": True,
        }, headers=admin).status_code == 200
        assert client.delete(f"/api/v1/players/{pid}/matches/{mid}", headers=admin).status_code == 204


# ── RESTRICCIÓN DE COMPAÑERO ───────────────────────────────────

class TestPartnerOwnerRestriction:

    def test_partner_otra_cuenta_rechazado_jugador(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_a = _new_player(a, "DeA")
        pid_b = _new_player(b, "DeB")
        r = _create_match(a, pid_a, partner_id=pid_b)
        assert r.status_code == 400

    def test_partner_otra_cuenta_rechazado_admin(self):
        # El admin escribe su PROPIO jugador, pero no puede emparejarlo con un
        # jugador de otra cuenta: la restricción de compañero aplica también al admin.
        admin, _ = _register_and_login("admin")
        pid_a = _new_player(admin, "AdminP1")
        owner_b, _ = _register_and_login("jugador")
        pid_b = _new_player(owner_b, "OwnerB")
        r = _create_match(admin, pid_a, partner_id=pid_b)
        assert r.status_code == 400

    def test_admin_partner_mismo_owner_ok(self):
        # Sanity: el admin SÍ puede escribir y emparejar sus propios jugadores.
        admin, _ = _register_and_login("admin")
        p1 = _new_player(admin, "AdminP1")
        p2 = _new_player(admin, "AdminP2")
        r = _create_match(admin, p1, partner_id=p2)
        assert r.status_code == 201
        assert r.json()["partner_id"] == p2


# ── MANIPULACIÓN DE PROPIEDAD ──────────────────────────────────

class TestOwnerManipulationMatches:

    def test_cliente_no_altera_player1_ni_owner(self):
        user, user_id = _register_and_login("jugador")
        pid = _new_player(user)
        otra = str(uuid.uuid4())
        # intento de inyectar player1_id / owner_id / partner_id ajenos
        r = _create_match(user, pid, player1_id=otra, owner_id=otra)
        assert r.status_code == 201
        # la propiedad la define la URL (player1_id = pid), no el cuerpo
        assert r.json()["player1_id"] == pid
        assert r.json()["player1_id"] != otra


# ── REGRESIÓN ──────────────────────────────────────────────────

class TestRegresionMatches:

    def _make_tournament(self, owner_id, player_id):
        db = TestSession()
        t = TournamentModel(
            name=f"Torneo {uuid.uuid4().hex[:6]}",
            date=date.today(),
            fep_points=100,
            owner_id=owner_id,
            player_id=player_id,
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        tid = t.id
        db.close()
        return tid

    def test_validacion_ronda_duplicada(self):
        user, user_id = _register_and_login("jugador")
        pid = _new_player(user)
        tid = self._make_tournament(user_id, pid)
        r1 = _create_match(user, pid, tournament_id=str(tid), ronda="Fase de grupos")
        assert r1.status_code == 201
        # misma ronda en el mismo torneo → 400
        r2 = _create_match(user, pid, tournament_id=str(tid), ronda="Fase de grupos")
        assert r2.status_code == 400

    def test_notificacion_al_companero(self):
        user, user_id = _register_and_login("jugador")
        p1 = _new_player(user, "Titular")
        p2 = _new_player(user, "Compañero")
        _new_match(user, p1, partner_id=p2)
        db = TestSession()
        notif = db.query(NotificationModel).filter(
            NotificationModel.user_id == user_id,
            NotificationModel.type == "match_added",
        ).first()
        assert notif is not None
        db.close()

    def test_delete_elimina_match(self):
        user, _ = _register_and_login("jugador")
        pid = _new_player(user)
        mid = _new_match(user, pid)
        assert client.delete(f"/api/v1/players/{pid}/matches/{mid}", headers=user).status_code == 204
        db = TestSession()
        assert db.query(MatchModel).filter(MatchModel.id == mid).first() is None
        db.close()
