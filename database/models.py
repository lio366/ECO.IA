"""ECO-IA SQLAlchemy models."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Boolean, Integer,
    DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from database.connection import Base
import enum


class PlanEnum(str, enum.Enum):
    basic = "basic"
    pro = "pro"
    enterprise = "enterprise"


class Client(Base):
    """Paying client of ECO-IA."""
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    plan = Column(Enum(PlanEnum), default=PlanEnum.basic, nullable=False)
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    monthly_spend = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")
    api_usages = relationship("APIUsage", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client {self.email} plan={self.plan}>"


class Invoice(Base):
    """Stripe invoice record."""
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    stripe_invoice_id = Column(String(255), nullable=True, unique=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="usd")
    status = Column(String(50), default="pending")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

    client = relationship("Client", back_populates="invoices")


class APIUsage(Base):
    """API usage tracking per client."""
    __tablename__ = "api_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    endpoint = Column(String(255), nullable=False)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    model = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    client = relationship("Client", back_populates="api_usages")


class SystemMetric(Base):
    """Historical system metrics."""
    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cpu_percent = Column(Float, nullable=False)
    ram_percent = Column(Float, nullable=False)