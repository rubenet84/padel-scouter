"""
Endpoints de autenticación: registro, login, refresh, reset de contraseña.

Implementa el flujo completo de autenticación con JWT (access + refresh tokens)
siguiendo las recomendaciones OWASP:
- A01 (Broken Access Control): ownership checks en todos los endpoints.
- A02 (Cryptographic Failures): bcrypt para passwords, JWT firmados.
- A07 (Identification & Authentication Failures): rate limiting en login/register,
  tokens de reset de corta duración, mensajes genéricos para evitar enumeración.
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, create_reset_token, verify_reset_token
)
from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import UserModel
from app.infrastructure.email.email_service import (
    send_welcome_email, send_password_reset_email
)
from app.schemas.player import (
    UserRegisterSchema, UserLoginSchema,
    TokenSchema, UserPublicSchema
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublicSchema, status_code=201)
@limiter.limit("3/minute")
def register(data: UserRegisterSchema, request: Request, db: Session = Depends(get_db)):
    """Registra un nuevo usuario con email, username y contraseña.

    Validaciones:
    - Email único en el sistema (case-insensitive).
    - Username único en el sistema.
    - Contraseña fuerte validada por UserRegisterSchema (12+ chars, mayúscula,
      minúscula, número, carácter especial).
    - Rate limit: 3 registros por minuto por IP.

    El rol por defecto es "viewer". El usuario se crea activo.
    Se envía email de bienvenida de forma no bloqueante.
    """
    email = data.email.lower().strip()

    if db.query(UserModel).filter(UserModel.email == email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    if db.query(UserModel).filter(UserModel.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username ya en uso")

    user = UserModel(
        email=email,
        username=data.username,
        hashed_password=hash_password(data.password),
        role="viewer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # OWASP A02 — enviar email de bienvenida (no bloqueante)
    send_welcome_email(email, data.username)

    return user


@router.post("/login", response_model=TokenSchema)
@limiter.limit("5/minute")
def login(data: UserLoginSchema, request: Request, db: Session = Depends(get_db)):
    """Autentica al usuario y devuelve tokens de acceso y refresco.

    Seguridad (OWASP A02):
    - El mensaje de error es genérico ("Credenciales incorrectas") tanto si el
      email no existe como si la contraseña es incorrecta, para prevenir
      enumeración de usuarios.
    - Rate limit: 5 intentos por minuto por IP para mitigar fuerza bruta.
    - El access token incluye el rol del usuario para autorización.
    """
    email = data.email.lower().strip()
    user = db.query(UserModel).filter(UserModel.email == email).first()

    # OWASP A02 — mensaje genérico, no revelar si existe el usuario
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    return TokenSchema(
        access_token=create_access_token({"sub": str(user.id), "role": user.role}),
        refresh_token=create_refresh_token({"sub": str(user.id)}),
    )


@router.post("/forgot-password", status_code=200)
@limiter.limit("3/minute")
def forgot_password(request: Request, email: str = Body(embed=True), db: Session = Depends(get_db)):
    """
    OWASP A01 — email va en el body, no en query params (consistente con reset-password).
    OWASP A07 — siempre devuelve 200 aunque el email no exista,
    para no revelar si un usuario está registrado (user enumeration).
    """
    email = email.lower().strip()
    user = db.query(UserModel).filter(UserModel.email == email).first()

    if user:
        reset_token = create_reset_token(email)
        send_password_reset_email(email, reset_token, user.username)

    # Siempre mismo mensaje — OWASP A07
    return {"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}


@router.post("/reset-password", status_code=200)
@limiter.limit("3/minute")
def reset_password(
    request: Request,
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(get_db),
):
    """
    OWASP A01 — token y password van en el body, no en query params.
    OWASP A07 — reset seguro con token firmado de un solo uso.

    Flujo:
    1. Verifica que el token de reset sea válido y no haya expirado.
    2. Valida la fortaleza de la nueva contraseña con las mismas reglas de registro.
    3. Hashea y persiste la nueva contraseña.
    """
    from app.schemas.player import UserRegisterSchema
    from pydantic import ValidationError

    # Verificar token
    email = verify_reset_token(token)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Token inválido o expirado"
        )

    # Validar fortaleza de la nueva contraseña
    try:
        UserRegisterSchema(
            email=email,
            username="placeholder",
            password=new_password
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.hashed_password = hash_password(new_password)
    db.commit()

    return {"message": "Contraseña actualizada correctamente"}


@router.post("/refresh", response_model=TokenSchema)
def refresh(refresh_token: str = Body(...), db: Session = Depends(get_db)):
    """Genera un nuevo par de tokens (access + refresh) usando un refresh token válido.

    Solo acepta tokens de tipo 'refresh'. El refresh token se rota:
    se emite uno nuevo junto con el access token. El usuario debe descartar
    el refresh token anterior.
    """
    from jose import JWTError
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token inválido")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expirado o inválido")

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return TokenSchema(
        access_token=create_access_token({"sub": str(user.id), "role": user.role}),
        refresh_token=create_refresh_token({"sub": str(user.id)}),
    )


@router.get("/me", response_model=UserPublicSchema)
def me(current_user: UserModel = Depends(get_current_user)):
    """Devuelve los datos del usuario autenticado actual (obtenidos del JWT)."""
    return current_user