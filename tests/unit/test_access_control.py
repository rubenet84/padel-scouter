"""
Tests unitarios de la capa de autorización (guards + política AND/OR).

No requieren base de datos: los guards se invocan directamente pasando un
usuario simulado (la dependencia Depends(get_current_user) es solo el valor
por defecto y se puede sobrescribir pasando el usuario como argumento).
"""
import pytest
from fastapi import HTTPException

from app.core.dependencies import require_any_permission, require_permission
from app.domain.authorization.policy import (
    Permission,
    Role,
    has_all_permissions,
    has_any_permission,
)


class FakeUser:
    """Usuario simulado con el atributo role usado por los guards."""
    def __init__(self, role: str):
        self.role = role
        self.id = "fake-id"


# ── Política: semántica AND / OR ───────────────────────────────

class TestPoliticaAndOr:

    def test_all_permissions_requiere_todas(self):
        assert has_all_permissions(Role.ADMIN, Permission.PLAYERS_CREATE, Permission.PLAYERS_READ) is True
        # jugador tiene create pero NO restore → AND falla
        assert has_all_permissions(Role.JUGADOR, Permission.PLAYERS_CREATE, Permission.PLAYERS_RESTORE) is False

    def test_any_permission_requiere_una(self):
        assert has_any_permission(Role.JUGADOR, Permission.PLAYERS_RESTORE, Permission.PLAYERS_CREATE) is True
        assert has_any_permission(Role.JUGADOR, Permission.PLAYERS_RESTORE, Permission.STATS_COMPARE) is False

    def test_sin_permisos_es_fail_closed(self):
        assert has_all_permissions(Role.ADMIN) is False
        assert has_any_permission(Role.ADMIN) is False

    def test_rol_invalido_fail_closed(self):
        assert has_all_permissions(None, Permission.PLAYERS_READ) is False
        assert has_any_permission(None, Permission.PLAYERS_READ) is False


# ── Guards: require_permission (AND) ───────────────────────────

class TestRequirePermission:

    def test_sin_permisos_es_error_de_programacion(self):
        with pytest.raises(ValueError):
            require_permission()

    def test_admin_pasa_con_todos_los_permisos(self):
        checker = require_permission(Permission.PLAYERS_CREATE, Permission.PLAYERS_READ)
        user = FakeUser("admin")
        assert checker(user) is user

    def test_jugador_pasa_si_tiene_todos(self):
        checker = require_permission(Permission.PLAYERS_CREATE, Permission.PLAYERS_READ)
        user = FakeUser("jugador")
        assert checker(user) is user

    def test_and_deniega_si_falta_uno(self):
        # jugador NO tiene players.restore → AND debe denegar
        checker = require_permission(Permission.PLAYERS_CREATE, Permission.PLAYERS_RESTORE)
        with pytest.raises(HTTPException) as exc:
            checker(FakeUser("jugador"))
        assert exc.value.status_code == 403

    def test_rol_invalido_deniega(self):
        checker = require_permission(Permission.PLAYERS_READ)
        with pytest.raises(HTTPException) as exc:
            checker(FakeUser("viewer"))
        assert exc.value.status_code == 403

    def test_rol_vacio_deniega(self):
        checker = require_permission(Permission.PLAYERS_READ)
        with pytest.raises(HTTPException) as exc:
            checker(FakeUser(""))
        assert exc.value.status_code == 403


# ── Guards: require_any_permission (OR) ────────────────────────

class TestRequireAnyPermission:

    def test_sin_permisos_es_error_de_programacion(self):
        with pytest.raises(ValueError):
            require_any_permission()

    def test_pasa_con_uno_de_los_permisos(self):
        # jugador tiene create aunque no restore → OR pasa
        checker = require_any_permission(Permission.PLAYERS_RESTORE, Permission.PLAYERS_CREATE)
        user = FakeUser("jugador")
        assert checker(user) is user

    def test_deniega_si_no_tiene_ninguno(self):
        checker = require_any_permission(Permission.PLAYERS_RESTORE, Permission.STATS_COMPARE)
        with pytest.raises(HTTPException) as exc:
            checker(FakeUser("jugador"))
        assert exc.value.status_code == 403

    def test_rol_invalido_deniega(self):
        checker = require_any_permission(Permission.PLAYERS_READ, Permission.AI_CHAT)
        with pytest.raises(HTTPException) as exc:
            checker(FakeUser("desconocido"))
        assert exc.value.status_code == 403
