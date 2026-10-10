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
