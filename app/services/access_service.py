"""Servicio central de autorización y acceso (capa de aplicación).

Centraliza —en un único lugar— todas las decisiones de acceso que antes
tenderían a repetirse por los endpoints:

- Resolución de alcance (scope) a partir del rol (fuente: policy del dominio).
- Comprobación de ownership sobre jugadores.
- Comprobación de límites de jugadores (con bloqueo para evitar carreras).
- Registro de auditoría de acciones administrativas.

Principios:
- FAIL-CLOSED: ante rol inválido, ambigüedad o ausencia de datos, se DENIEGA.
  Un error de programación nunca amplía permisos.
- El acceso GLOBAL solo se concede cuando el rol resuelve explícitamente a
  Scope.GLOBAL (admin). Nunca por un owner_id ausente/None.
- La política pura vive en app.domain.authorization.policy (sin SQLAlchemy).
  Este servicio sí usa persistencia (repositorios) porque es capa de aplicación.

Arquitectura: Capa de aplicación — orquesta dominio + infraestructura.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.authorization.policy import (
    Scope,
    player_limit,
    resolve_scope,
    role_from_value,
)
from app.domain.authorization.errors import (
    PlayerLimitExceededError,
    ResourceNotFoundError,
)
from app.infrastructure.database.models import PlayerModel
from app.infrastructure.repositories.player_repository import (
    count_players_by_owner,
    get_all_players,
    get_player_owner_id,
    get_players_by_owner,
)
from app.infrastructure.repositories.user_repository import lock_user_by_id
from app.infrastructure.repositories.audit_repository import add_audit_entry


# ── Alcance (scope) ────────────────────────────────────────────

def resolve_scope_for(user) -> Scope:
    """Resuelve el alcance del usuario a partir de su rol (fail-closed → OWN)."""
    return resolve_scope(role_from_value(getattr(user, "role", None)))


def is_global(user) -> bool:
    """True SOLO si el usuario tiene alcance global explícito (admin)."""
    return resolve_scope_for(user) is Scope.GLOBAL


def list_accessible_players(db: Session, user, personal: bool = False) -> list:
    """Jugadores accesibles según el alcance EXPLÍCITO del usuario.

    - Scope.GLOBAL (admin): todos los jugadores (consulta sin filtro de owner).
    - Scope.OWN / ROSTER / rol inválido: solo los del propio owner (fail-closed).

    Override `personal`: cuando es True (contexto dashboard/personal) SIEMPRE se
    fuerza el ownership (get_players_by_owner) para TODOS los roles, admin
    incluido, ignorando el alcance global. Así el dashboard de un admin muestra
    sus propios jugadores y no los de toda la comunidad. Por defecto (False) se
    conserva el alcance derivado del rol.

    El alcance se deriva del rol (política central), NUNCA de un owner_id
    ausente o None. El filtrado se resuelve en la base de datos (con o sin
    cláusula de owner), sin materializar conjuntos innecesarios.
    """
    if personal:
        return get_players_by_owner(db, user.id)
    if resolve_scope_for(user) is Scope.GLOBAL:
        return get_all_players(db)
    return get_players_by_owner(db, user.id)


def apply_owner_scope(query, user, personal: bool = False):
    """Aplica el filtro de ownership a una query ORM de PlayerModel.

    - Scope.GLOBAL (admin): sin filtro (acceso a todos).
    - Scope.OWN / Scope.ROSTER: owner_id == user.id.

    Override `personal`: cuando es True (contexto dashboard/personal) SIEMPRE
    filtra por owner_id == user.id para TODOS los roles, admin incluido,
    ignorando el alcance global. Así el listado personal del dashboard queda
    owner-scoped aunque el usuario sea admin. Por defecto (False) se conserva
    el alcance derivado del rol.

    Fail-closed: un rol inválido resuelve a OWN, por lo que SIEMPRE filtra por
    el propio usuario; nunca concede acceso global por rol desconocido.
    """
    if personal:
        return query.filter(PlayerModel.owner_id == user.id)
    if resolve_scope_for(user) is Scope.GLOBAL:
        return query
    return query.filter(PlayerModel.owner_id == user.id)


# ── Ownership de jugadores ─────────────────────────────────────

def can_access_owner(user, owner_id: UUID | None) -> bool:
    """Indica si el usuario puede acceder a un recurso del owner_id dado.

    - owner_id None (recurso inexistente) → False (fail-closed).
    - Scope.GLOBAL (admin) → True (acceso a cualquier recurso existente).
    - Resto → solo si owner_id == user.id.

    Útil cuando el recurso ya se cargó y solo falta comprobar el propietario
    (evita una consulta adicional).
    """
    if owner_id is None:
        return False
    if is_global(user):
        return True
    return owner_id == user.id


def can_access_player(db: Session, user, player_id: UUID) -> bool:
    """Indica si el usuario puede acceder al jugador indicado.

    El admin (scope global) accede a cualquier jugador existente. El resto solo
    a los de su propio owner_id. Un jugador inexistente nunca es accesible.
    """
    return can_access_owner(user, get_player_owner_id(db, player_id))


def get_player_owner_or_raise(db: Session, user, player_id: UUID) -> UUID:
    """Devuelve el owner_id del jugador si es accesible; si no, lanza.

    Lanza ResourceNotFoundError tanto si el jugador no existe como si pertenece
    a otro usuario (la capa API responderá 404 sin revelar su existencia).

    Returns:
        El owner_id del jugador accesible.
    """
    owner_id = get_player_owner_id(db, player_id)
    if not can_access_owner(user, owner_id):
        raise ResourceNotFoundError("Jugador no encontrado")
    return owner_id


# ── Límites de jugadores ───────────────────────────────────────

def count_owned_players(db: Session, owner_id: UUID) -> int:
    """Cuenta los jugadores no eliminados de un propietario.

    Fail-closed: exige un owner_id explícito; nunca cuenta "todos".
    """
    if owner_id is None:
        raise ValueError("owner_id es obligatorio para contar jugadores")
    return count_players_by_owner(db, owner_id)


def enforce_player_limit(db: Session, user) -> None:
    """Comprueba que el usuario puede crear otro jugador.

    Límites (fuente única en policy): admin ilimitado, entrenador 25, jugador 2.
    Un rol inválido resuelve a límite 0 → deniega (fail-closed).

    Concurrencia: adquiere un bloqueo de fila sobre el usuario
    (SELECT ... FOR UPDATE) para serializar creaciones simultáneas del mismo
    propietario y evitar que dos peticiones concurrentes superen el límite.
    DEBE invocarse dentro de la MISMA transacción que la inserción del jugador,
    de modo que el bloqueo se mantenga hasta el commit.

    Raises:
        PlayerLimitExceededError: si ya se alcanzó el límite.
    """
    role = role_from_value(getattr(user, "role", None))
    limit = player_limit(role)
    if limit is None:
        return  # admin: ilimitado (sin bloqueo)

    lock_user_by_id(db, user.id)  # serializa creaciones concurrentes del owner
    current = count_owned_players(db, user.id)
    if current >= limit:
        raise PlayerLimitExceededError(
            f"Has alcanzado el límite de {limit} jugadores de tu plan."
        )


# ── Auditoría ──────────────────────────────────────────────────

def record_audit(
    db: Session,
    actor,
    action: str,
    target_type: str,
    target_id: UUID | None = None,
    details: str | None = None,
):
    """Registra una acción administrativa sensible (sin commit).

    Preparado para las fases posteriores (cambio de rol, suspensión, etc.).
    La transacción la controla el llamador.
    """
    return add_audit_entry(
        db,
        actor_id=actor.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
