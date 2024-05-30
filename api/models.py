from xmlrpc.client import boolean
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID, uuid4
from typing import Union, List
from enum import Enum
from datetime import date


class Weekday(Enum):
    Monday = 1
    Tuesday = 2
    Wednesday = 3
    Thursday = 4
    Friday = 5
    Saturday = 6
    Sunday = 7


# MODELS


class Student(BaseModel):
    id: UUID
    firstName: str = ""
    lastName: str = ""
    email: str = ""
    level: str = ""
    program: str = ""
    endDate: date = ""
    active: bool = False


class Course(BaseModel):
    id: UUID = ""
    code: str = ""
    name: str = ""
    active: bool = False


class TimeSlot(BaseModel):
    id: UUID = ""
    weekday: str = ""
    startTime: str = ""
    endTime: str = ""
    active: bool = False

    class Config:
        json_encoders = {Weekday: lambda v: {"key": v.name, "value": v.value}}


class UpdateStudentChoice(BaseModel):
    studentID: UUID
    choice: str
    courseID: str = ""


class UpdateActive(BaseModel):
    entity: str
    id: UUID
    active: bool


class UpdateAvailability(BaseModel):
    entity: str
    id: UUID
    timeSlotID: UUID
    isAvailable: boolean


class DeleteEntity(BaseModel):
    entity: str
    id: UUID


class Survey(BaseModel):
    id: UUID
    cycle: str = ""
    program: str = ""
    weekday: str = ""
