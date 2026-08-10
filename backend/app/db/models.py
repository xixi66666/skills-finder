from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    owner: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(201), unique=True)
    html_url: Mapped[str] = mapped_column(String(512))
    homepage: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    topics: Mapped[list[Any]] = mapped_column(JSON)
    categories: Mapped[list[Any]] = mapped_column(JSON)
    matched_rules: Mapped[list[Any]] = mapped_column(JSON)
    stars_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    forks_count: Mapped[int] = mapped_column(Integer, default=0)
    open_issues_count: Mapped[int] = mapped_column(Integer, default=0)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    github_created_at: Mapped[datetime] = mapped_column(DateTime(6))
    github_updated_at: Mapped[datetime] = mapped_column(DateTime(6))
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(6))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(6), default=datetime.utcnow, server_default="CURRENT_TIMESTAMP(6)"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(6),
        default=datetime.utcnow,
        server_default="CURRENT_TIMESTAMP(6)",
        onupdate=datetime.utcnow,
    )


class StarSnapshot(Base):
    __tablename__ = "star_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "repository_id", "snapshot_date", name="uk_star_snapshots_repository_date"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("repositories.id", ondelete="CASCADE")
    )
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    stars_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(6), default=datetime.utcnow, server_default="CURRENT_TIMESTAMP(6)"
    )


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    trigger_type: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(6), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(6), nullable=True)
    query_count: Mapped[int] = mapped_column(Integer, default=0)
    discovered_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    rate_limit_remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rate_limit_reset_at: Mapped[datetime | None] = mapped_column(DateTime(6), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(6), default=datetime.utcnow, server_default="CURRENT_TIMESTAMP(6)"
    )
