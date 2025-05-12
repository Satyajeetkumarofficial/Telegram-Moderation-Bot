from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.connection import Base

class ModerationLog(Base):
    __tablename__ = "moderation_logs"
    id = Column(Integer, primary_key=True)
    group_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    admin_id = Column(BigInteger, nullable=False)
    action = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Warning(Base):
    __tablename__ = "warnings"
    id = Column(Integer, primary_key=True)
    group_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    admin_id = Column(BigInteger, nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GroupConfig(Base):
    __tablename__ = "group_configs"
    id = Column(Integer, primary_key=True)
    group_id = Column(BigInteger, nullable=False, unique=True)
    welcome_message = Column(Text, nullable=True)
    goodbye_message = Column(Text, nullable=True)
    rules = Column(Text, nullable=True)
    warn_limit = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
