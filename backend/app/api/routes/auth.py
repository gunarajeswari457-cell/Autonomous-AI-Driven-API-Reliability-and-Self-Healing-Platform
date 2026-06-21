from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


@router.post("/register", response_model=Token)
async def register(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    email = _normalize_email(str(payload.email))
    exists = await session.execute(select(User).where(func.lower(User.email) == email))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    token = create_access_token(subject=email, extra={"uid": user.id})
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)):
    email = _normalize_email(str(payload.email))
    result = await session.execute(select(User).where(func.lower(User.email) == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=email, extra={"uid": user.id})
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
