# models.py - core models
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from enum import Enum

class Role(str, Enum):
    ORG_USER = "org_user"
    VALIDATOR = "validator"
    ADMIN = "admin"

class Organization(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    contact_email: Optional[str] = None

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    name: Optional[str] = None
    password_hash: str
    role: Role = Field(sa_column=None)
    org_id: Optional[int] = Field(default=None, foreign_key="organization.id")
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Upload(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int
    uploaded_by: Optional[int] = None
    file_path: Optional[str] = None
    status: str = Field(default="processing")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Parameter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    upload_id: int
    org_id: int
    parameter: str
    value: float
    unit: Optional[str] = None
    measured_at: Optional[datetime] = None

class Threshold(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int
    parameter: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    severity: Optional[str] = "warning"

class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int
    parameter: str
    value: float
    threshold_id: Optional[int] = None
    status: str = Field(default="new")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ActivityLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = None
    org_id: Optional[int] = None
    action: str
    details: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ValidatorReview(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    upload_id: int
    validator_id: int
    status: str = Field(default="pending")
    notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None

class Presence(SQLModel, table=True):
    user_id: int = Field(primary_key=True)
    last_ping: datetime = Field(default_factory=datetime.utcnow)
