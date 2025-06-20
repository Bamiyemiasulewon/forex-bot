from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# SQLAlchemy model for audit logging of user actions and critical events.
class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True, index=True)  # Unique log entry ID
    user_id = Column(Integer, nullable=True)  # ID of the user who performed the action
    action = Column(String(255), nullable=False)  # Description of the action
    details = Column(Text)  # Additional details about the action
    timestamp = Column(DateTime(timezone=True), server_default=func.now())  # Time of the action 