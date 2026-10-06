"""
Tests de integración RBAC del bloque PLAYERS (app/api/v1/players.py).

Cubren: permisos, scope, ownership, límites, IDOR/BOLA, protección de owner_id
y regresión de soft-delete/restore/avatar. Requieren PostgreSQL local en
localhost:5432 (mismos parámetros que el resto de tests de integración).
"""
import uuid
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.infrastructure.database.models import Base, UserModel, PlayerModel
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
    """Garantiza el esquema en tiempo de test (independiente del orden de módulos)."""
    Base.metadata.create_all(bind=engine)
    yield


# ── Helpers ────────────────────────────────────────────────────

def _register_and_login(role: str = "jugador"):
    """Registra un usuario (siempre nace 'jugador'), le fija el rol en BD y
    devuelve (headers, user_id)."""
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


def _create_player(headers, name="Jugador", owner_id=None):
    payload = {
        "name": name,
        "category": "3ª Categoría",
        "stats": {"derecha": 60, "reves": 55},
    }
    if owner_id is not None:
        payload["owner_id"] = str(owner_id)  # intento de manipulación
    return client.post("/api/v1/players/", json=payload, headers=headers)


def _new_player_id(headers, name="Jugador"):
    r = _create_player(headers, name=name)
    assert r.status_code == 201, r.json()
    return r.json()["id"]


# ── ADMIN ──────────────────────────────────────────────────────

class TestAdmin:

    def test_admin_lista_solo_sus_jugadores(self):
        # El listado /players/ es PERSONAL: owner-scoped también para admin.
        admin, _ = _register_and_login("admin")
        propio = _new_player_id(admin, "PropioDelAdmin")
        owner, _ = _register_and_login("jugador")
        ajeno = _new_player_id(owner, "PlayerDeJugador")
        listed = client.get("/api/v1/players/", headers=admin)
        assert listed.status_code == 200
        ids = [p["id"] for p in listed.json()]
        assert propio in ids
        assert ajeno not in ids

    def test_admin_lista_vacia_sin_jugadores(self):
        # Un admin sin jugadores propios ve su listado personal vacío,
        # aunque existan jugadores de otros owners.
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        ajeno = _new_player_id(owner, "DeOtroOwner")
        listed = client.get("/api/v1/players/", headers=admin)
        assert listed.status_code == 200
        ids = [p["id"] for p in listed.json()]
        assert ids == []
        assert ajeno not in ids

    def test_admin_accede_a_jugador_ajeno(self):
        admin, _ = _register_and_login("admin")
        owner, _ = _register_and_login("jugador")
        pid = _new_player_id(owner, "Ajeno")
        r = client.get(f"/api/v1/players/{pid}", headers=admin)
        assert r.status_code == 200
        assert r.json()["id"] == pid

    def test_admin_sin_limite(self):
        admin, _ = _register_and_login("admin")
        for i in range(5):
            assert _create_player(admin, name=f"Admin{i}").status_code == 201


# ── ENTRENADOR ─────────────────────────────────────────────────

class TestEntrenador:

    def test_crea_hasta_25_y_26_rechazado(self):
        coach, _ = _register_and_login("entrenador")
        for i in range(25):
            r = _create_player(coach, name=f"Coach{i}")
            assert r.status_code == 201, f"fallo en {i}: {r.json()}"
        assert _create_player(coach, name="Coach26").status_code == 409

    def test_lista_solo_sus_jugadores(self):
        coach_a, _ = _register_and_login("entrenador")
        coach_b, _ = _register_and_login("entrenador")
        pid_a = _new_player_id(coach_a, "DeA")
        pid_b = _new_player_id(coach_b, "DeB")
        listed = client.get("/api/v1/players/", headers=coach_a)
        ids = [p["id"] for p in listed.json()]
        assert pid_a in ids
        assert pid_b not in ids

    def test_no_ve_jugador_ajeno(self):
        coach_a, _ = _register_and_login("entrenador")
        coach_b, _ = _register_and_login("entrenador")
        pid_b = _new_player_id(coach_b, "DeB")
        assert client.get(f"/api/v1/players/{pid_b}", headers=coach_a).status_code == 404

    def test_lista_excluye_jugador_de_admin(self):
        # El listado personal de un entrenador excluye jugadores de OTRO rol.
        coach, _ = _register_and_login("entrenador")
        pid_coach = _new_player_id(coach, "Mio")
        admin, _ = _register_and_login("admin")
        pid_admin = _new_player_id(admin, "DeAdmin")
        ids = [p["id"] for p in client.get("/api/v1/players/", headers=coach).json()]
        assert pid_coach in ids
        assert pid_admin not in ids

    def test_no_modifica_jugador_ajeno(self):
        coach_a, _ = _register_and_login("entrenador")
        coach_b, _ = _register_and_login("entrenador")
        pid_b = _new_player_id(coach_b, "DeB")
        r = client.put(f"/api/v1/players/{pid_b}", json={
            "name": "Hackeado", "category": "3ª Categoría", "stats": {"derecha": 1},
        }, headers=coach_a)
        assert r.status_code == 404

    def test_no_elimina_jugador_ajeno(self):
        coach_a, _ = _register_and_login("entrenador")
        coach_b, _ = _register_and_login("entrenador")
        pid_b = _new_player_id(coach_b, "DeB")
        assert client.delete(f"/api/v1/players/{pid_b}", headers=coach_a).status_code == 404

    def test_no_restaura_jugador_ajeno(self):
        coach_a, _ = _register_and_login("entrenador")
        coach_b, _ = _register_and_login("entrenador")
        pid_b = _new_player_id(coach_b, "DeB")
        client.delete(f"/api/v1/players/{pid_b}", headers=coach_b)
        assert client.put(f"/api/v1/players/{pid_b}/restore", headers=coach_a).status_code == 404


# ── JUGADOR ────────────────────────────────────────────────────

class TestJugador:

    def test_crea_hasta_2_y_tercero_rechazado(self):
        user, _ = _register_and_login("jugador")
        assert _create_player(user, name="Uno").status_code == 201
        assert _create_player(user, name="Dos").status_code == 201
        assert _create_player(user, name="Tres").status_code == 409

    def test_lista_solo_sus_jugadores(self):
        user, _ = _register_and_login("jugador")
        pid = _new_player_id(user, "Mio")
        listed = client.get("/api/v1/players/", headers=user)
        assert pid in [p["id"] for p in listed.json()]

    def test_no_ve_jugador_ajeno(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player_id(b, "DeB")
        assert client.get(f"/api/v1/players/{pid_b}", headers=a).status_code == 404

    def test_lista_excluye_jugador_de_entrenador(self):
        # El listado personal de un jugador excluye jugadores de OTRO rol.
        user, _ = _register_and_login("jugador")
        pid_user = _new_player_id(user, "Mio")
        coach, _ = _register_and_login("entrenador")
        pid_coach = _new_player_id(coach, "DeCoach")
        ids = [p["id"] for p in client.get("/api/v1/players/", headers=user).json()]
        assert pid_user in ids
        assert pid_coach not in ids

    def test_no_modifica_elimina_ajeno(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player_id(b, "DeB")
        assert client.put(f"/api/v1/players/{pid_b}", json={
            "name": "Hackeado", "category": "3ª Categoría", "stats": {"derecha": 1},
        }, headers=a).status_code == 404
        assert client.delete(f"/api/v1/players/{pid_b}", headers=a).status_code == 404

    def test_jugador_no_puede_restaurar(self):
        user, _ = _register_and_login("jugador")
        pid = _new_player_id(user, "Mio")
        assert client.delete(f"/api/v1/players/{pid}", headers=user).status_code == 200
        # restaurar su PROPIO jugador: sin permiso players.restore → 403
        assert client.put(f"/api/v1/players/{pid}/restore", headers=user).status_code == 403


# ── IDOR / BOLA ────────────────────────────────────────────────

class TestIDOR:

    def test_idor_get_devuelve_404_sin_datos(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player_id(b, "Victima")
        r = client.get(f"/api/v1/players/{pid_b}", headers=a)
        assert r.status_code == 404
        assert "Victima" not in r.text
        assert pid_b not in r.text

    def test_idor_update_devuelve_404(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player_id(b, "Victima")
        assert client.put(f"/api/v1/players/{pid_b}", json={
            "name": "Hackeado", "category": "3ª Categoría", "stats": {"derecha": 1},
        }, headers=a).status_code == 404

    def test_idor_delete_devuelve_404(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player_id(b, "Victima")
        assert client.delete(f"/api/v1/players/{pid_b}", headers=a).status_code == 404

    def test_idor_stats_devuelve_404(self):
        a, _ = _register_and_login("jugador")
        b, _ = _register_and_login("jugador")
        pid_b = _new_player_id(b, "Victima")
        assert client.get(f"/api/v1/players/{pid_b}/stats", headers=a).status_code == 404


# ── MANIPULACIÓN DE owner_id ───────────────────────────────────

class TestOwnerManipulation:

    def test_cliente_no_puede_fijar_owner_id(self):
        user, user_id = _register_and_login("jugador")
        otra_cuenta = uuid.uuid4()
        r = _create_player(user, name="Intento", owner_id=otra_cuenta)
        assert r.status_code == 201
        # El owner_id resultante es el del usuario autenticado, no el enviado
        assert r.json()["owner_id"] == str(user_id)
        assert r.json()["owner_id"] != str(otra_cuenta)


# ── REGRESIÓN ──────────────────────────────────────────────────

class TestRegresion:

    def test_soft_delete_y_listado(self):
        user, _ = _register_and_login("jugador")
        pid = _new_player_id(user, "ParaBorrar")
        assert client.delete(f"/api/v1/players/{pid}", headers=user).status_code == 200
        listed = client.get("/api/v1/players/", headers=user)
        assert pid not in [p["id"] for p in listed.json()]
        # soft delete: el registro sigue existiendo en BD
        db = TestSession()
        row = db.query(PlayerModel).filter(PlayerModel.id == pid).first()
        assert row is not None and row.is_deleted is True
        db.close()

    def test_restore_admin_funciona(self):
        admin, _ = _register_and_login("admin")
        pid = _new_player_id(admin, "Restaurable")
        client.delete(f"/api/v1/players/{pid}", headers=admin)
        r = client.put(f"/api/v1/players/{pid}/restore", headers=admin)
        assert r.status_code == 200
        assert client.get(f"/api/v1/players/{pid}", headers=admin).status_code == 200

    def test_restore_entrenador_funciona(self):
        coach, _ = _register_and_login("entrenador")
        pid = _new_player_id(coach, "Restaurable")
        client.delete(f"/api/v1/players/{pid}", headers=coach)
        assert client.put(f"/api/v1/players/{pid}/restore", headers=coach).status_code == 200

    def test_avatar_sigue_funcionando(self):
        from PIL import Image
        user, _ = _register_and_login("jugador")
        pid = _new_player_id(user, "ConAvatar")
        buf = BytesIO()
        Image.new("RGB", (64, 64), (200, 30, 30)).save(buf, format="PNG")
        r = client.post(
            f"/api/v1/players/{pid}/avatar",
            files={"file": ("avatar.png", buf.getvalue(), "image/png")},
            headers=user,
        )
        assert r.status_code == 200
        assert r.json()["avatar_url"]
