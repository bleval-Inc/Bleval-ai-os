"""BLEVAL Domain Models — Sales, CRM, Deals, Campaigns."""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from axiom.data.database import Domain, DeclarativeBase


class BlevalBase(DeclarativeBase):
    """Base for BLEVAL domain models."""
    metadata = MetaData(schema="bleval")


class LeadStatus(str, enum.Enum):
    """Lead lifecycle status."""

    NEW = "new"
    QUALIFIED = "qualified"
    CONTACTED = "contacted"
    NURTURING = "nurturing"
    PROPOSAL = "proposal"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    DISQUALIFIED = "disqualified"


class LeadSource(str, enum.Enum):
    """Lead source channels."""

    ATLAS = "atlas"
    REFERRAL = "referral"
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    PARTNER = "partner"
    EVENT = "event"
    CONTENT = "content"
    PAID_ADS = "paid_ads"


class DealStage(str, enum.Enum):
    """Deal pipeline stages."""

    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class CampaignStatus(str, enum.Enum):
    """Campaign status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ActivityType(str, enum.Enum):
    """Activity types."""

    EMAIL = "email"
    CALL = "call"
    MEETING = "meeting"
    NOTE = "note"
    TASK = "task"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    SLACK = "slack"


# ──────────────────────────────────────────────────────────────────────────────
# LEADS & CONTACTS
# ──────────────────────────────────────────────────────────────────────────────

class Lead(BlevalBase):
    """Lead model – prospective customer."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Identity
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Company
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Location
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Lead scoring & status
    status: Mapped[LeadStatus] = mapped_column(
        SQLEnum(LeadStatus), default=LeadStatus.NEW, nullable=False, index=True
    )
    source: Mapped[LeadSource] = mapped_column(
        SQLEnum(LeadSource), default=LeadSource.INBOUND, nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    opportunity_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Qualification
    qualified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    qualified_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    disqualification_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Attribution
    campaign_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("campaigns.id"), nullable=True
    )
    utm_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_content: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_term: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Ownership
    owner_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    last_contacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_follow_up_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="lead", lazy="selectin"
    )
    opportunities: Mapped[List["Opportunity"]] = relationship(
        "Opportunity", back_populates="lead", lazy="selectin"
    )
    contacts: Mapped[List["Contact"]] = relationship(
        "Contact", back_populates="lead", foreign_keys="Contact.lead_id", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_leads_email_company", "email", "company"),
        Index("ix_leads_status_score", "status", "score"),
        Index("ix_leads_owner_status", "owner_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, email={self.email}, status={self.status.value})>"


class Contact(BlevalBase):
    """Contact model – qualified lead or existing customer contact."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    # Identity
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Company
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationship
    account_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("accounts.id"), nullable=True
    )
    lead_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("leads.id"), nullable=True
    )

    # Preferences
    preferred_contact_method: Mapped[str] = mapped_column(String(50), default="email")
    do_not_contact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Owner
    owner_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    last_contacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    account: Mapped[Optional["Account"]] = relationship(
        "Account", back_populates="contacts", foreign_keys=[account_id]
    )
    lead: Mapped[Optional["Lead"]] = relationship(
        "Lead", back_populates="contacts", foreign_keys=[lead_id]
    )

    __table_args__ = (
        Index("ix_contacts_email_company", "email", "company"),
        Index("ix_contacts_owner", "owner_id"),
    )

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, email={self.email}, company={self.company})>"


# ──────────────────────────────────────────────────────────────────────────────
# ACCOUNTS & OPPORTUNITIES
# ──────────────────────────────────────────────────────────────────────────────

class Account(BlevalBase):
    """Account model – company/organization."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    annual_revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    # Address
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status
    is_customer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_partner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lifecycle_stage: Mapped[str] = mapped_column(String(50), default="prospect")

    # Owner
    owner_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    contacts: Mapped[List["Contact"]] = relationship(
        "Contact", back_populates="account", lazy="selectin"
    )
    opportunities: Mapped[List["Opportunity"]] = relationship(
        "Opportunity", back_populates="account", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, name={self.name})>"


class Opportunity(BlevalBase):
    """Opportunity model – qualified sales opportunity."""

    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    lead_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("leads.id"), nullable=True
    )
    account_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("accounts.id"), nullable=True
    )
    contact_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("contacts.id"), nullable=True
    )

    # Deal info
    stage: Mapped[DealStage] = mapped_column(
        SQLEnum(DealStage), default=DealStage.PROSPECTING, nullable=False, index=True
    )
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    probability: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    expected_close_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    actual_close_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Forecast
    forecast_category: Mapped[str] = mapped_column(String(50), default="pipeline")
    weighted_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    # Competition
    competitor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    competitive_threats: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Owner
    owner_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    lead: Mapped[Optional["Lead"]] = relationship("Lead", back_populates="opportunities")
    account: Mapped[Optional["Account"]] = relationship("Account", back_populates="opportunities")
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="opportunity", lazy="selectin"
    )
    deals: Mapped[List["Deal"]] = relationship("Deal", back_populates="opportunity", lazy="selectin")

    __table_args__ = (
        Index("ix_opportunities_stage_owner", "stage", "owner_id"),
        Index("ix_opportunities_close_date", "expected_close_date"),
    )

    def __repr__(self) -> str:
        return f"<Opportunity(id={self.id}, name={self.name}, stage={self.stage.value})>"


# ──────────────────────────────────────────────────────────────────────────────
# DEALS
# ──────────────────────────────────────────────────────────────────────────────

class Deal(BlevalBase):
    """Deal model – closed transaction."""

    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    opportunity_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("opportunities.id"), nullable=True
    )
    account_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("accounts.id"), nullable=True
    )

    # Deal terms
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contract_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    contract_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    # Owner
    owner_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    opportunity: Mapped[Optional["Opportunity"]] = relationship("Opportunity", back_populates="deals")

    def __repr__(self) -> str:
        return f"<Deal(id={self.id}, name={self.name}, amount={self.amount})>"


# ──────────────────────────────────────────────────────────────────────────────
# CAMPAIGNS
# ──────────────────────────────────────────────────────────────────────────────

class Campaign(BlevalBase):
    """Campaign model – marketing/sales campaign."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    campaign_type: Mapped[str] = mapped_column(String(50), nullable=False)  # email, linkedin, ads, etc.

    # Status
    status: Mapped[CampaignStatus] = mapped_column(
        SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False, index=True
    )

    # Dates
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Budget & ROI
    budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    spent: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    revenue_attributed: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    # Metrics
    leads_generated: Mapped[int] = mapped_column(Integer, default=0)
    opportunities_created: Mapped[int] = mapped_column(Integer, default=0)
    deals_won: Mapped[int] = mapped_column(Integer, default=0)

    # Owner
    owner_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name}, status={self.status.value})>"


# ──────────────────────────────────────────────────────────────────────────────
# ACTIVITIES
# ──────────────────────────────────────────────────────────────────────────────

class Activity(BlevalBase):
    """Activity model – all interactions with leads/contacts/opportunities."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    type: Mapped[ActivityType] = mapped_column(SQLEnum(ActivityType), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Polymorphic relationships
    lead_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("leads.id"), nullable=True
    )
    contact_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("contacts.id"), nullable=True
    )
    opportunity_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("opportunities.id"), nullable=True
    )
    account_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("accounts.id"), nullable=True
    )
    campaign_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("campaigns.id"), nullable=True
    )

    # Direction
    direction: Mapped[str] = mapped_column(String(20), default="outbound")  # inbound, outbound

    # Status
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)

    # Owner
    owner_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # External references
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    external_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # slack, email, etc.

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, index=True)

    # Relationships
    lead: Mapped[Optional["Lead"]] = relationship("Lead", back_populates="activities")
    opportunity: Mapped[Optional["Opportunity"]] = relationship("Opportunity", back_populates="activities")

    __table_args__ = (
        Index("ix_activities_lead_occurred", "lead_id", "occurred_at"),
        Index("ix_activities_opportunity_occurred", "opportunity_id", "occurred_at"),
        Index("ix_activities_type_occurred", "type", "occurred_at"),
        Index("ix_activities_owner_occurred", "owner_id", "occurred_at"),
    )

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, type={self.type.value}, subject={self.subject[:30]})>"