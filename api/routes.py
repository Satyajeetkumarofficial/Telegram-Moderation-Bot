from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from database.connection import get_db
from database.models import ModerationLog, Warning, GroupConfig
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from datetime import datetime

router = APIRouter(prefix="/api")

# API Key authentication
API_KEY_NAME = "X-API-Token"
API_KEY = os.getenv("API_TOKEN")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )

# Pydantic models for API responses
class Log(BaseModel):
    id: int
    group_id: int
    user_id: int
    admin_id: int
    action: str
    created_at: str

class Warning(BaseModel):
    id: int
    group_id: int
    user_id: int
    admin_id: int
    reason: Optional[str]
    created_at: str

class Group(BaseModel):
    id: int
    group_id: int
    welcome_message: Optional[str]
    goodbye_message: Optional[str]
    rules: Optional[str]
    warn_limit: int
    created_at: str
    updated_at: Optional[str]

class Stats(BaseModel):
    total_groups: int
    total_users: int
    total_warnings: int
    total_actions: int
    actions_by_type: Dict[str, int]
    most_active_groups: List[Dict[str, Any]]
    most_warned_users: List[Dict[str, Any]]

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/logs", response_model=List[Log])
async def get_logs(
    skip: int = 0, 
    limit: int = 100, 
    group_id: Optional[int] = None,
    user_id: Optional[int] = None,
    admin_id: Optional[int] = None,
    action: Optional[str] = None,
    api_key: str = Depends(get_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Get moderation logs with optional filtering.
    """
    query = select(ModerationLog).order_by(desc(ModerationLog.created_at)).offset(skip).limit(limit)

    # Apply filters if provided
    if group_id:
        query = query.where(ModerationLog.group_id == group_id)
    if user_id:
        query = query.where(ModerationLog.user_id == user_id)
    if admin_id:
        query = query.where(ModerationLog.admin_id == admin_id)
    if action:
        query = query.where(ModerationLog.action.contains(action))

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        Log(
            id=log.id,
            group_id=log.group_id,
            user_id=log.user_id,
            admin_id=log.admin_id,
            action=log.action,
            created_at=log.created_at.isoformat()
        )
        for log in logs
    ]

@router.get("/warns/{user_id}", response_model=List[Warning])
async def get_user_warnings(
    user_id: int,
    group_id: Optional[int] = None,
    api_key: str = Depends(get_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Get warnings for a specific user, optionally filtered by group.
    """
    query = select(Warning).where(Warning.user_id == user_id).order_by(desc(Warning.created_at))

    if group_id:
        query = query.where(Warning.group_id == group_id)

    result = await db.execute(query)
    warnings = result.scalars().all()

    return [
        Warning(
            id=warning.id,
            group_id=warning.group_id,
            user_id=warning.user_id,
            admin_id=warning.admin_id,
            reason=warning.reason,
            created_at=warning.created_at.isoformat()
        )
        for warning in warnings
    ]

@router.get("/groups", response_model=List[Group])
async def get_groups(
    skip: int = 0,
    limit: int = 100,
    api_key: str = Depends(get_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all groups with their configurations.
    """
    query = select(GroupConfig).order_by(GroupConfig.group_id).offset(skip).limit(limit)
    result = await db.execute(query)
    groups = result.scalars().all()

    return [
        Group(
            id=group.id,
            group_id=group.group_id,
            welcome_message=group.welcome_message,
            goodbye_message=group.goodbye_message,
            rules=group.rules,
            warn_limit=group.warn_limit,
            created_at=group.created_at.isoformat(),
            updated_at=group.updated_at.isoformat() if group.updated_at else None
        )
        for group in groups
    ]

@router.get("/stats", response_model=Stats)
async def get_stats(
    api_key: str = Depends(get_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall statistics about the bot's usage.
    """
    # Total groups
    total_groups_query = select(func.count(GroupConfig.id))
    total_groups_result = await db.execute(total_groups_query)
    total_groups = total_groups_result.scalar() or 0

    # Total unique users (from warnings and logs)
    total_users_query = select(
        func.count(
            func.distinct(
                func.coalesce(ModerationLog.user_id, Warning.user_id)
            )
        )
    ).select_from(
        func.full_outer_join(
            ModerationLog,
            Warning,
            ModerationLog.user_id == Warning.user_id
        ).alias()
    )
    total_users_result = await db.execute(total_users_query)
    total_users = total_users_result.scalar() or 0

    # Total warnings
    total_warnings_query = select(func.count(Warning.id))
    total_warnings_result = await db.execute(total_warnings_query)
    total_warnings = total_warnings_result.scalar() or 0

    # Total actions
    total_actions_query = select(func.count(ModerationLog.id))
    total_actions_result = await db.execute(total_actions_query)
    total_actions = total_actions_result.scalar() or 0

    # Actions by type
    actions_by_type_query = select(
        ModerationLog.action,
        func.count(ModerationLog.id).label("count")
    ).group_by(ModerationLog.action)
    actions_by_type_result = await db.execute(actions_by_type_query)
    actions_by_type = {
        action: count
        for action, count in actions_by_type_result.all()
    }

    # Most active groups
    most_active_groups_query = select(
        ModerationLog.group_id,
        func.count(ModerationLog.id).label("action_count")
    ).group_by(ModerationLog.group_id).order_by(desc("action_count")).limit(5)
    most_active_groups_result = await db.execute(most_active_groups_query)
    most_active_groups = [
        {"group_id": group_id, "action_count": count}
        for group_id, count in most_active_groups_result.all()
    ]

    # Most warned users
    most_warned_users_query = select(
        Warning.user_id,
        func.count(Warning.id).label("warning_count")
    ).group_by(Warning.user_id).order_by(desc("warning_count")).limit(5)
    most_warned_users_result = await db.execute(most_warned_users_query)
    most_warned_users = [
        {"user_id": user_id, "warning_count": count}
        for user_id, count in most_warned_users_result.all()
    ]

    return Stats(
        total_groups=total_groups,
        total_users=total_users,
        total_warnings=total_warnings,
        total_actions=total_actions,
        actions_by_type=actions_by_type,
        most_active_groups=most_active_groups,
        most_warned_users=most_warned_users
    )
