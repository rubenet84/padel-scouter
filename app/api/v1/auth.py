from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import UserModel
from app.schemas.player import UserRegisterSchema, UserLoginSchema, TokenSchema, UserPublicSchema

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublicSchema, status_code=201)
def register(data: UserRegisterSchema, db: Session = Depends(get_db)):
    if db.query(UserModel).filter(UserModel.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    if db.query(UserModel).filter(UserModel.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username ya en uso")

    user = UserModel(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        role="viewer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenSchema)
def login(data: UserLoginSchema, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == data.email).first()
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


@router.post("/refresh", response_model=TokenSchema)
def refresh(refresh_token: str, db: Session = Depends(get_db)):
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
    return current_user