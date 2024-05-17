from neo4jDriver import query_neo4j
from fastapi_setup import app
from fastapi import FastAPI

app = FastAPI()

# Models
# from API.models import Room, Teacher, Student, Course, TimeSlot
# from API.models import UpdateStrength, UpdateActive, DeleteEntity
# from API.models import Assign, Event, UpdateAvailability, UpdateStudentChoice

# Utility functions
# from API.utils import find_course, get_active_slots


### ROOT
@app.get("/")
async def read_root() -> dict[str, str]:
    return {"msg": "API for EF Tokyo"}
