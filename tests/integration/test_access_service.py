"""
Tests de integración del servicio de autorización (app/services/access_service.py).

Verifican ownership, resolución de scope, acceso global de admin y límites de
jugadores. Requieren un PostgreSQL local en localhost:5432 (mismos parámetros
que el resto de tests de integración).
"""
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.models import Base, PlayerModel, UserModel
from app.domain.value_objects.category import PlayerCategory
from app.domain.authorization.policy import Scope
from app.domain.authorization.errors import (
    PlayerLimitExceededError,
    ResourceNotFoundError,
)
from app.services import access_service

TEST_DB_URL = "postgresql+psycopg2://padel:padel123@localhost:5432/padel_scouter"
engine = create_engine(TEST_DB_URL)
TestSession = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)


class FakeUser:
    """Usuario no persistido, para probar fail-closed con roles inválidos."""
    def __init__(self, role, user_id=None):
        self.role = role
        self.id = user_id or uuid.uuid4()


@pytest.fixture(scope="module")
def db():
    session = TestSession()
    yield session
    session.close()


def _make_user(db, role):
    user = UserModel(
        email=f"{role}_{uuid.uuid4().hex[:8]}@padel.com",
        username=f"u_{uuid.uuid4().hex[:8]}",
        hashed_password="x",
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_player(db, owner_id, name="Jugador"):
    player = PlayerModel(
        name=name,
        category=PlayerCategory.TERCERA,
        owner_id=owner_id,
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


# ── Scope ──────────────────────────────────────────────────────

class TestScope:

    def test_admin_scope_global(self, db):
        admin = _make_user(db, "admin")
        assert access_service.resolve_scope_for(admin) is Scope.GLOBAL
        assert access_service.is_global(admin) is True

    def test_entrenador_scope_roster(self, db):
        coach = _make_user(db, "entrenador")
        assert access_service.resolve_scope_for(coach) is Scope.ROSTER
        assert access_service.is_global(coach) is False

    def test_jugador_scope_own(self, db):
        player_user = _make_user(db, "jugador")
        assert access_service.resolve_scope_for(player_user) is Scope.OWN
        assert access_service.is_global(player_user) is False

    def test_rol_invalido_scope_own_fail_closed(self, db):
        fake = FakeUser("viewer")
        assert access_service.resolve_scope_for(fake) is Scope.OWN
        assert access_service.is_global(fake) is False


# ── Ownership ──────────────────────────────────────────────────

class TestOwnership:

    def test_propio_accesible(self, db):
        owner = _make_user(db, "jugador")
        player = _make_player(db, owner.id)
        assert access_service.can_access_player(db, owner, player.id) is True

    def test_ajeno_no_accesible(self, db):
        owner = _make_user(db, "jugador")
        other = _make_user(db, "jugador")
        player = _make_player(db, owner.id)
        assert access_service.can_access_player(db, other, player.id) is False

    def test_admin_acceso_global(self, db):
        owner = _make_user(db, "entrenador")
        player = _make_player(db, owner.id)
        admin = _make_user(db, "admin")
        assert access_service.can_access_player(db, admin, player.id) is True

    def test_inexistente_no_accesible(self, db):
        user = _make_user(db, "jugador")
        assert access_service.can_access_player(db, user, uuid.uuid4()) is False

    def test_get_owner_or_raise_propio_devuelve_owner(self, db):
        owner = _make_user(db, "jugador")
        player = _make_player(db, owner.id)
        assert access_service.get_player_owner_or_raise(db, owner, player.id) == owner.id

    def test_get_owner_or_raise_ajeno_lanza(self, db):
        owner = _make_user(db, "jugador")
        other = _make_user(db, "jugador")
        player = _make_player(db, owner.id)
        with pytest.raises(ResourceNotFoundError):
            access_service.get_player_owner_or_raise(db, other, player.id)

    def test_get_owner_or_raise_inexistente_lanza(self, db):
        user = _make_user(db, "jugador")
        with pytest.raises(ResourceNotFoundError):
            access_service.get_player_owner_or_raise(db, user, uuid.uuid4())

    def test_apply_owner_scope_filtra_por_propio(self, db):
        a = _make_user(db, "jugador")
        b = _make_user(db, "jugador")
        _make_player(db, a.id)
        _make_player(db, a.id)
        _make_player(db, b.id)
        base = db.query(PlayerModel).filter(PlayerModel.owner_id.in_([a.id, b.id]))
        assert access_service.apply_owner_scope(base, a).count() == 2

    def test_apply_owner_scope_admin_sin_filtro(self, db):
        a = _make_user(db, "jugador")
        b = _make_user(db, "jugador")
        admin = _make_user(db, "admin")
        _make_player(db, a.id)
        _make_player(db, b.id)
        base = db.query(PlayerModel).filter(PlayerModel.owner_id.in_([a.id, b.id]))
        assert access_service.apply_owner_scope(base, admin).count() == 2

    def test_apply_owner_scope_rol_invalido_solo_propio(self, db):
        a = _make_user(db, "jugador")
        b = _make_user(db, "jugador")
        _make_player(db, a.id)
        _make_player(db, b.id)
        fake = FakeUser("viewer", user_id=a.id)
        base = db.query(PlayerModel).filter(PlayerModel.owner_id.in_([a.id, b.id]))
        # fail-closed: rol inválido se comporta como OWN, nunca global
        assert access_service.apply_owner_scope(base, fake).count() == 1


# ── Límites de jugadores ───────────────────────────────────────

class TestLimites:

    def test_jugador_puede_crear_con_uno(self, db):
        user = _make_user(db, "jugador")
        _make_player(db, user.id)
        try:
            access_service.enforce_player_limit(db, user)  # 1 < 2 → no lanza
        finally:
            db.rollback()

    def test_jugador_tercero_rechazado(self, db):
        user = _make_user(db, "jugador")
        _make_player(db, user.id)
        _make_player(db, user.id)
        with pytest.raises(PlayerLimitExceededError):
            access_service.enforce_player_limit(db, user)
        db.rollback()

    def test_entrenador_limite_25(self, db):
        coach = _make_user(db, "entrenador")
        for _ in range(25):
            _make_player(db, coach.id)
        with pytest.raises(PlayerLimitExceededError):
            access_service.enforce_player_limit(db, coach)
        db.rollback()

    def test_entrenador_puede_con_24(self, db):
        coach = _make_user(db, "entrenador")
        for _ in range(24):
            _make_player(db, coach.id)
        try:
            access_service.enforce_player_limit(db, coach)  # 24 < 25 → no lanza
        finally:
            db.rollback()

    def test_admin_sin_limite(self, db):
        admin = _make_user(db, "admin")
        for _ in range(30):
            _make_player(db, admin.id)
        access_service.enforce_player_limit(db, admin)  # ilimitado → no lanza

    def test_rol_invalido_deniega(self, db):
        fake = FakeUser("viewer")
        with pytest.raises(PlayerLimitExceededError):
            access_service.enforce_player_limit(db, fake)
        db.rollback()

    def test_count_owned_players_exige_owner(self, db):
        with pytest.raises(ValueError):
            access_service.count_owned_players(db, None)
