from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth_deps import get_current_user
from .db import get_session
from .models import PlatformUser
from .schemas import ChangePasswordIn, LoginIn, LoginOut, UserOut
from .security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginOut)
async def login(body: LoginIn, session: AsyncSession = Depends(get_session)) -> LoginOut:
    stmt = select(PlatformUser).where(PlatformUser.username == body.username.strip())
    user = (await session.execute(stmt)).scalars().first()
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid username or password")
    token = create_access_token(user.id, user.username)
    return LoginOut(
        token=token,
        user=UserOut(
            id=user.id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )


@router.get("/me", response_model=UserOut)
async def me(user: PlatformUser = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/change-password")
async def change_password(
    body: ChangePasswordIn,
    user: PlatformUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="current password incorrect")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="new password must be at least 6 characters")
    user.password_hash = hash_password(body.new_password)
    session.add(user)
    await session.commit()
    return {"ok": True}


@router.post("/logout")
async def logout() -> dict[str, bool]:
    return {"ok": True}
