"""
Dependencias reutilizables de FastAPI para autenticación y autorización.

Provee:
- get_current_user: Dependencia que extrae y valida el JWT del request,
  devuelve el UserModel autenticado o lanza 401.
- _optional_auth: Similar a get_current_user pero devuelve None si no hay
  token (útil para endpoints que aceptan acceso anónimo y autenticado).
- require_role: Factory que genera dependencias de autorización por rol
  (ej: require_role("admin") devuelve 403 si el usuario no es admin).

Todas las dependencias usan los esquemas de seguridad OAuth2 Bearer
de FastAPI para obtener el token del header Authorization.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import UserModel

# Esquema OAuth2 para Swagger UI — espera token en header Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
# Bearer opcional para endpoints que aceptan tanto acceso anónimo como autenticado
optional_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserModel:
    """Dependencia de autenticación obligatoria.

    Extrae el JWT del header Authorization, lo decodifica, verifica que sea
    de tipo 'access' y que el usuario exista y esté activo en la base de datos.

    Returns:
        UserModel del usuario autenticado.

    Raises:
        HTTPException 401 si el token es inválido, expirado, no es 'access',
            el usuario no existe o está inactivo.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        # Solo se aceptan tokens de tipo 'access' — los refresh/reset/download no pasan
        if user_id is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def _optional_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
    db: Session = Depends(get_db),
) -> UserModel | None:
    """Autenticación opcional: como get_current_user pero devuelve None si no hay token.

    Útil para endpoints como la descarga de PDF que aceptan tanto JWT en el header
    como un download_token por query param. Si el token no está presente o es inválido,
    no falla — simplemente devuelve None para que el endpoint decida cómo proceder.
    """
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "access":
            return None
    except JWTError:
        return None
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None or not user.is_active:
        return None
    return user


def require_role(*roles: str):
    """Factory de dependencia de autorización por rol.

    Uso:
        @router.get("/admin")
        def admin_panel(user = Depends(require_role("admin"))):
            ...

    Args:
        *roles: Uno o más nombres de rol permitidos (ej: "admin", "editor").

    Returns:
        Una dependencia que verifica que el current_user tenga uno de los roles
        especificados. Lanza 403 si no cumple.
    """
    def checker(current_user: UserModel = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol requerido: {roles}",
            )
        return current_user
    return checker