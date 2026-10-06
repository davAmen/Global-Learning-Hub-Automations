"""Core data models for the automation.

These mirror the tables in schema.sql. They are the shape the scheduler and
channels work with - they are NOT an ORM.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


EngagementStatus = Literal["active", "low_engagement", "needs_followup"]


class Student(BaseModel):
    id: UUID
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime


class Course(BaseModel):
    id: UUID
    name: str
    start_date: Optional[date] = None
    class_time: Optional[str] = None
    created_at: datetime


class Enrollment(BaseModel):
    id: UUID
    student_id: UUID
    course_id: UUID
    status: Literal["active", "inactive"] = "active"
    enrolled_at: datetime


class ReminderLog(BaseModel):
    id: UUID
    enrollment_id: UUID
    channel: str
    message: str
    sent_at: datetime
    delivery_status: Literal["sent", "failed", "pending"] = "pending"
    external_message_id: Optional[str] = None


class Group(BaseModel):
    id: UUID
    whatsapp_jid: str
    name: str
    type: Literal["announcement", "proof_submission", "class_access", "community"]
    course_id: Optional[UUID] = None
    parent_community_jid: Optional[str] = None
    is_active: bool = True
    created_at: datetime


class Payment(BaseModel):
    id: UUID
    student_id: UUID
    course_id: UUID
    amount: float
    currency: str = "GHS"
    method: Literal["momo", "telecel", "bank"]
    reference: str
    proof_url: Optional[str] = None
    status: Literal["pending", "verified", "rejected"] = "pending"
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    created_at: datetime


class Approval(BaseModel):
    id: UUID
    action_type: Literal["send_message", "create_group", "add_participant", "send_flyer"]
    content: Optional[str] = None
    target_group_jid: Optional[str] = None
    target_course_id: Optional[UUID] = None
    metadata: Optional[dict] = None
    status: Literal["pending", "approved", "rejected", "modified"] = "pending"
    requested_by: str
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime


class ContentItem(BaseModel):
    id: UUID
    type: Literal["flyer", "announcement", "material"]
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    course_id: Optional[UUID] = None
    created_by: str
    created_at: datetime


class AuditLog(BaseModel):
    id: UUID
    actor: Literal["agent", "admin", "system"]
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    details: Optional[dict] = None
    created_at: datetime