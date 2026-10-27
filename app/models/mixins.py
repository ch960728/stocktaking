from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings


class AuditMixin:
    """Shared audit columns. This system has no login, so created_by/updated_by
    are always settings.default_user ("admin"). Deletes are always logical
    (is_active flag), never a physical DELETE."""

    created_by: Mapped[str] = mapped_column(String(50), default=settings.default_user)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_by: Mapped[str] = mapped_column(
        String(50), default=settings.default_user, onupdate=lambda: settings.default_user
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
