"""Core data models for the automation.

These mirror the tables in schema.sql. They are the shape the scheduler and
channels work with - they are NOT an ORM.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


EngagementStatus = Literal["active", "low_engagement", "needs_followup"]
EnrollmentStatus = Literal["active", "inactive", "completed", "dropped"]
CourseStatus = Literal["active", "inactive"]
DeliveryStatus = Literal["pending", "sent", "failed", "delivered", "read"]
PaymentStatus = Literal["pending", "verified", "rejected", "refunded"]
PaymentMethod = Literal["momo", "telecel", "bank", "card", "cash"]
PaymentCurrency = Literal["GHS", "USD", "EUR"]
PaymentProvider = Literal["paystack", "seefcash", "manual_momo", "manual_telecel"]
ApprovalActionType = Literal["send_message", "create_group", "add_participant", "send_flyer", "verify_payment", "broadcast"]
ApprovalStatus = Literal["pending", "approved", "rejected", "modified", "cancelled"]
ApprovalRequestedBy = Literal["agent", "admin", "system"]
GroupType = Literal["announcement", "proof_submission", "class_access", "community", "class"]
ContentType = Literal["flyer", "announcement", "material", "template"]
ContentCreatedBy = Literal["agent", "admin", "system"]
AuditActor = Literal["agent", "admin", "system", "user"]
StudentRole = Literal["learner", "admin", "instructor"]


class Student(BaseModel):
    id: UUID
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    email_verified: bool = False
    role: StudentRole = "learner"
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime


class Course(BaseModel):
    id: UUID
    name: str
    start_date: Optional[date] = None
    class_time: Optional[str] = None
    timezone: str = "GMT"
    is_active: bool = True
    price_minor: int = 0
    currency: PaymentCurrency = "GHS"
    capacity: Optional[int] = None
    seat_reservation_minor: int = 0
    description: Optional[str] = None
    learning_outcomes: list[str] = []
    prerequisites: list[str] = []
    expected_study_hours: Optional[int] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    whatsapp_group_jid: Optional[str] = None
    proof_submission_group_jid: Optional[str] = None
    created_at: datetime


class Enrollment(BaseModel):
    id: UUID
    student_id: UUID
    course_id: UUID
    status: EnrollmentStatus = "active"
    enrolled_at: datetime


class ReminderLog(BaseModel):
    id: UUID
    enrollment_id: Optional[UUID] = None
    course_id: Optional[UUID] = None
    channel: str
    message: str
    sent_at: datetime
    delivery_status: DeliveryStatus = "pending"
    external_message_id: Optional[str] = None
    metadata: Optional[dict] = None


class Group(BaseModel):
    id: UUID
    whatsapp_jid: str
    name: str
    type: GroupType
    course_id: Optional[UUID] = None
    parent_community_jid: Optional[str] = None
    is_active: bool = True
    settings: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class Payment(BaseModel):
    id: UUID
    student_id: UUID
    course_id: UUID
    amount: float = Field(gt=0)
    currency: PaymentCurrency = "GHS"
    method: PaymentMethod
    reference: str
    proof_url: Optional[str] = None
    status: PaymentStatus = "pending"
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    rejected_by: Optional[UUID] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    provider: Optional[PaymentProvider] = None
    provider_payment_id: Optional[str] = None
    provider_reference: Optional[str] = None
    provider_fees_minor: Optional[int] = None
    provider_response: Optional[dict] = None
    seat_reservation: bool = False
    seat_reservation_verified_at: Optional[datetime] = None
    enrollment_created: bool = False
    created_at: datetime
    updated_at: datetime


class Approval(BaseModel):
    id: UUID
    action_type: ApprovalActionType
    content: Optional[str] = None
    target_group_jid: Optional[str] = None
    target_course_id: Optional[UUID] = None
    metadata: Optional[dict] = None
    status: ApprovalStatus = "pending"
    requested_by: ApprovalRequestedBy
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ContentItem(BaseModel):
    id: UUID
    type: ContentType
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    course_id: Optional[UUID] = None
    created_by: ContentCreatedBy
    version: int = 1
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class AuditLog(BaseModel):
    id: UUID
    actor: AuditActor
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime


class SystemConfig(BaseModel):
    key: str
    value: dict
    description: Optional[str] = None
    updated_at: datetime
    updated_by: Optional[str] = None