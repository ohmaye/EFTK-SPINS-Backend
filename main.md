from API.neo4jDriver import query_neo4j
from API.fastapi_setup import app
from uuid import uuid4
import pandas as pd


# Models
from API.models import Room, Teacher, Student, Course, TimeSlot
from API.models import UpdateStrength, UpdateActive, DeleteEntity
from API.models import Assign, Event, UpdateAvailability, UpdateStudentChoice

# Utility functions
from API.utils import find_course, get_active_slots


### ROOT
@app.get("/")
async def read_root():
    return {"API for EF Tokyo"}


### GENERIC ENTITY(ies) API
# Get all entities of a type
@app.get("/entities/{entity:str}")
async def get_entities(entity: str, activeOnly: bool = False):
    query = f"MATCH (node:{entity}) {'WHERE node.active = true' if activeOnly else ''} RETURN node {{.*}}"
    result = query_neo4j(query)
    records = [record.data()["node"] for record in result.records]
    return records


# Get a single entity by id
@app.get("/entity/{entity:str}")
async def get_entity(entity: str, id: str):
    # print("Entity get: ", entity, id)
    result = query_neo4j(f"MATCH (node:{entity}) WHERE node.id = '{id}' RETURN node")
    node = [record.data()["node"] for record in result.records]
    return node[0] if len(node) > 0 else {}


# Create a new empy entity with UUID id
@app.post("/entity/{entity:str}")
async def post_entity(entity: str):
    id = uuid4()
    result = query_neo4j(f"CREATE (node:{entity} {{id: '{id}'}}) RETURN node")
    node = [record.data()["node"] for record in result.records]
    return node[0]


# Update an entity based on the key/value pairs in the item body of the request
# This path name creates conflicts
# @app.put("/update/{entity}")
# async def update_entity(entity: str, item: dict):
#     query = f"""
#     MATCH (n:{entity} {{id: '{item['id']}'}})
#     """
#     set_clause = ", ".join(
#         [
#             f"n.{key} = {'true' if value else 'false'}"
#             if key == "active"
#             else f"n.{key} = '{value}'"
#             for key, value in item.items()
#             if key != "id"
#         ]
#     )
#     query += f"SET {set_clause} RETURN n"
#     # result = await query_neo4j(query)
#     print("Query: ", query)
#     return {"query": query, "result": "result"}


# Delete an entity
@app.delete("/delete")
async def delete_entity(data: DeleteEntity):
    query = f"MATCH (n:{data.entity}) WHERE n.id = '{data.id}' DETACH DELETE n"
    result = query_neo4j(query)
    return {"result": "Deleted"}


@app.put("/update/active")
async def update_active(data: UpdateActive):
    query = f"MATCH (n:{data.entity}) WHERE n.id = '{data.id}' SET n.active = {data.active} RETURN n"
    query_neo4j(query)
    return {"result": f"Active flag set to {data.active}"}


### ENTITY SPECIFIC API


@app.get("/preferences")
async def get_preferences():
    # Courses that are active with codes sorted by code and id
    courses = await get_entities("Course", activeOnly=True)

    # Teachers who are active
    teachers = await get_entities("Teacher", activeOnly=True)

    # Preferences per teacher
    query = """MATCH (t:Teacher)-[r:TEACHES]->(c:Course) WHERE t.active = true AND c.active = true
        RETURN t.id AS teacherId, t.name as name, COLLECT({courseID: c.id, strength: r.strength}) AS preferences"""
    result = query_neo4j(query)
    teaches = [record.data() for record in result.records]

    # Put it into a table format to simplify the frontend
    preferences = []

    for teacher in teachers:
        row = [{"name": teacher["name"], "id": teacher["id"]}]
        teacherPreferences = [ts for ts in teaches if ts["teacherId"] == teacher["id"]]

        for course in courses:
            if (len(teacherPreferences)) == 0:
                row += [0]
            else:
                strength = [
                    item["strength"]
                    for item in teacherPreferences[0]["preferences"]
                    if item["courseID"] == course["id"]
                ]
                row += [strength]
        preferences += [row]

        # Send back courses (for headers), teachers (for rows), and preferences (for cells
        # print("preferences: ", preferences)
        # print("Courses: ", courses)
        # print("Teachers: ", teachers)
    return {"courses": courses, "preferences": preferences}


### SCHEDULING


# Get Teachers for a Course
@app.get("/get/course_teachers/")
async def get_course_teachers():
    query = """
        MATCH (c:Course {active: true}) 
        MATCH (t:Teacher {active: true})-[able:TEACHES]-(c) WHERE able.strength > 0
        WITH c.name as course, c.id as courseID, COLLECT({strength: able.strength, name: t.name, teacherID: t.id}) as teachers
        RETURN course, courseID, teachers
    """
    result = query_neo4j(query)
    schedule_map = [record.data() for record in result.records]
    return schedule_map


### UPDATE


# Generic update: Takes an action, entity (neo4j node label), and params
@app.put("/update/Teacher")
async def update_teacher(teacher: Teacher):
    query = f"""
    MATCH (t:Teacher {{id: '{teacher.id}'}})
    SET t.name = '{teacher.name}', t.nameJP = '{teacher.nameJP}', t.email = '{teacher.email}', t.active = {teacher.active}
    RETURN t
    """
    result = query_neo4j(query)
    return {"query": query, "result": result}
    # EO Alternative implementation below
    # update_entity("Teacher", teacher)
    # return {"message": "Teacher updated successfully"}


@app.put("/update/Student")
async def update_student(student: Student):
    query = f"""
    MATCH (s:Student {{id: '{student.id}'}})
    SET s.firstName = '{student.firstName}', s.lastName = '{student.lastName}', s.email = '{student.email}',
    s.level = '{student.level}', s.program = '{student.program}', 
    s.endDate = '{student.endDate}', s.active = {student.active}
    RETURN s
    """
    result = query_neo4j(query)
    return {"query": query, "result": result}


@app.put("/update/Course")
async def update_course(course: Course):
    query = f"""
    MATCH (c:Course {{id: '{course.id}'}})
    SET c.code = '{course.code}', c.name = '{course.name}',  c.active = {course.active}
    RETURN c 
    """
    result = query_neo4j(query)
    return {"query": query, "result": result}


@app.put("/update/StudentChoice")
async def update_student_choice(item: UpdateStudentChoice):
    print("Update Choice", item.studentID, item.choice, item.courseID)
    query = f"""MATCH (s:Student {{id: '{item.studentID}'}})-[wants:WANTS]-(c:Course) WHERE wants.choice = '{item.choice}' DETACH DELETE wants"""
    query_neo4j(query)
    query = f"MATCH (s:Student {{id: '{item.studentID}'}}), (c:Course {{id: '{item.courseID}'}}) MERGE (s)-[:WANTS {{choice: '{item.choice}'}}]->(c)"
    query_neo4j(query)
    result = query_neo4j(query)
    return {"query": query, "result": result}


@app.put("/update/Room")
async def update_room(room: Room):
    query = f"""
    MATCH (r:Room {{id: '{room.id}'}})
    SET r.name = '{room.name}', r.type = '{room.type}', r.capacity = {room.capacity}, r.active = {room.active}
    RETURN r
    """
    result = query_neo4j(query)
    return {"query": query, "result": result}


@app.put("/update/TimeSlot")
async def update_time_slot(timeSlot: TimeSlot):
    query = f"""
    MATCH (t:TimeSlot {{id: '{timeSlot.id}'}})
    SET t.weekday = '{timeSlot.weekday}', t.startTime = '{timeSlot.startTime}', t.endTime = '{timeSlot.endTime}', 
     t.active = {timeSlot.active}
    RETURN t
    """
    result = query_neo4j(query)
    return {"query": query, "result": result}


@app.put("/update/strength")
async def update_strength(data: UpdateStrength):
    # print("T/C/S ", data.teacherID, data.courseID, data.strength)
    # query1 = f"MATCH (t:Teacher {{id: '{item.teacherID}'}}), (c:Course {{id: '{item.courseID}'}}) MERGE (t)-[r:TEACHES {{strength: '{item.strength}'}}]->(c)"
    query = f"""
    MATCH (t:Teacher), (c:Course)
    WHERE t.id = '{data.teacherID}' AND c.id = '{data.courseID}'
    MERGE (t)-[r:TEACHES]->(c)
    SET r.strength = {data.strength}
    RETURN t, r, c
    """
    result = query_neo4j(query)
    return {"query": query, "result": result}


### TODO: check time slot for merge
### Assignments
async def assign_student(studentID, eventID, timeSlotID):
    print("ASSIGN", studentID, eventID, timeSlotID)
    query = f"""MATCH (s:Student {{id: '{studentID}'}})-[attendance:ATTENDS]-(e:Event) WHERE e.timeSlotID = '{timeSlotID}' DETACH DELETE attendance"""
    query_neo4j(query)
    query = f"MATCH (s:Student {{id: '{studentID}'}}), (e:Event {{id: '{eventID}'}}) MERGE (s)-[:ATTENDS]->(e)"
    query_neo4j(query)


@app.put("/assign")
async def assign_students_course(data: Assign):
    for student in data.students:
        await assign_student(
            studentID=student, eventID=data.eventID, timeSlotID=data.timeSlotID
        )

    return {"assignments": "done"}


@app.get("/assignments")
async def get_assignments():
    query = """
    MATCH (s:Student)-[a:ATTENDS]->(e:Event) RETURN s.id as studentID, e.id as eventID
    """
    result = query_neo4j(query)
    records = [record.data() for record in result.records]
    return records


### IS_AVAILABLE
@app.get("/is_available/{entity:str}")
async def is_available(entity: str, id: str):
    query = f"""
    MATCH (node:{entity})-[r:IS_AVAILABLE]->(ts:TimeSlot) WHERE node.id = '{id}' RETURN ts
    """
    result = query_neo4j(query)
    records = [record.data() for record in result.records]
    return records


@app.get("/teacher_availabilities")
async def get_teacher_availabilities():
    query = """
    MATCH (t:Teacher)-[r:IS_AVAILABLE]->(ts:TimeSlot) RETURN t.id as teacherID, ts.id as timeSlotID
    """
    result = query_neo4j(query)
    records = [record.data() for record in result.records]
    return records


@app.get("/room_availabilities")
async def get_room_availabilities():
    query = """
    MATCH (r:Room)-[rel:IS_AVAILABLE]->(ts:TimeSlot) RETURN r.id as roomID, ts.id as timeSlotID
    """
    result = query_neo4j(query)
    records = [record.data() for record in result.records]
    return records


@app.put("/update/availability")
async def update_availability(data: UpdateAvailability):
    if data.isAvailable:
        query = f"MATCH (n:{data.entity} {{id: '{data.id}'}}), (ts:TimeSlot {{id: '{data.timeSlotID}'}}) MERGE (n)-[:IS_AVAILABLE]->(ts)"
    else:
        query = f"MATCH (n:{data.entity}  {{id: '{data.id}'}})-[r:IS_AVAILABLE]->(ts:TimeSlot {{id: '{data.timeSlotID}'}}) DELETE r"
    result = query_neo4j(query)
    return {"result": result}


### DASHBOARD
@app.get("/dashboard/student_choices")
async def get_student_choices():
    query = """
        MATCH (s:Student) WHERE s.active = true
        OPTIONAL MATCH (s)-[w:WANTS]->(c:Course) WITH s, 
            COLLECT({choice: w.choice, course: c}) as choices 
            RETURN s as student, choices ORDER BY s.firstName, s.lastName
    """
    result = query_neo4j(query)
    studentChoices = [record.data() for record in result.records]
    choices = []
    for item in studentChoices:
        flatChoices = {item["choice"]: item["course"] for item in item["choices"]}
        choices += [{**item["student"], **flatChoices}]
    # print("Choices: ", choices)
    return choices


async def get_student_choices_for_df():
    query = """
        MATCH (s:Student)-[w:WANTS]->(c:Course) WITH s, 
            COLLECT({choice: w.choice, course: c.code + ' ' + c.name}) as choices 
            RETURN s as student, choices ORDER BY s.firstName, s.lastName
    """
    result = query_neo4j(query)
    studentChoices = [record.data() for record in result.records]
    choices = []
    for item in studentChoices:
        flatChoices = {item["choice"]: item["course"] for item in item["choices"]}
        choices += [{**item["student"], **flatChoices}]
    # print("Choices: ", choices)
    return choices


@app.get("/dashboard/demand_by_course")
async def get_demand_by_course():
    df = pd.DataFrame(await get_student_choices_for_df())
    dfgrp = pd.DataFrame(
        [
            df.groupby(["IMon01"]).size(),
            df.groupby(["IMon02"]).size(),
            df.groupby(["IMon03"]).size(),
            df.groupby(["IWed01"]).size(),
            df.groupby(["IWed02"]).size(),
            df.groupby(["IWed03"]).size(),
            df.groupby(["IWed04"]).size(),
            df.groupby(["IWed05"]).size(),
            df.groupby(["GWed01"]).size(),
            df.groupby(["GWed02"]).size(),
            df.groupby(["GWed03"]).size(),
            df.groupby(["GWed04"]).size(),
            df.groupby(["GWed05"]).size(),
        ]
    ).T
    return dfgrp.fillna("").reset_index().values.tolist()


@app.get("/dashboard/demand_by_level")
async def get_demand_by_level():
    df = pd.DataFrame(await get_student_choices_for_df())
    dfgrp = pd.DataFrame(
        [
            df.groupby(["IMon01", "level"]).size(),
            df.groupby(["IMon02", "level"]).size(),
            df.groupby(["IMon03", "level"]).size(),
            df.groupby(["IWed01", "level"]).size(),
            df.groupby(["IWed02", "level"]).size(),
            df.groupby(["IWed03", "level"]).size(),
            df.groupby(["IWed04", "level"]).size(),
            df.groupby(["IWed05", "level"]).size(),
            df.groupby(["GWed01", "level"]).size(),
            df.groupby(["GWed02", "level"]).size(),
            df.groupby(["GWed03", "level"]).size(),
            df.groupby(["GWed04", "level"]).size(),
            df.groupby(["GWed05", "level"]).size(),
        ]
    ).T
    return dfgrp.fillna("").reset_index().values.tolist()


@app.get("/dashboard/get_student_assignments")
async def get_student_assignments():
    query = """
        MATCH (s:Student)
        OPTIONAL MATCH (s:Student)-[a:ATTENDS]->(e:Event) 
        RETURN s.id as studentID, s.firstName + ' ' + s.lastName as name, s.level as level, s.program as program, s.endDate as endDate,
        COLLECT({when: e.when, what: e.what, courseID: e.courseID, eventID: e.id}) as assignments 
        ORDER BY name
    """
    result = query_neo4j(query)
    studentEvents = [record.data() for record in result.records]
    # print("Student Events: ", studentEvents)
    return studentEvents


@app.get("/dashboard/demand_by_assignments")
async def get_demand_by_assignments():
    courses = await get_entities("Course")
    slots = await get_entities("TimeSlot", activeOnly=True)
    activeSlots = get_active_slots(slots)
    stdAssignments = await get_student_assignments()

    assignments = []
    for stdAssignment in stdAssignments:
        row = {
            "studentID": stdAssignment["studentID"],
            "name": stdAssignment["name"],
            "level": stdAssignment["level"],
            "program": stdAssignment["program"],
            "endDate": stdAssignment["endDate"],
        }
        for slot in activeSlots:
            row[slot] = {}
            for assignment in stdAssignment.get("assignments", {}):
                if assignment.get("when") == slot:
                    row[slot] = {
                        "what": assignment.get("what"),
                        "eventID": assignment.get("eventID"),
                        "courseCode": find_course(
                            courses, assignment.get("courseID", None)
                        ).get("code", ""),
                        "courseName": find_course(
                            courses, assignment.get("courseID", None)
                        ).get("name", ""),
                    }
        assignments.append(row)
    return assignments


# Create EVENT (CLASS)
@app.post("/dashboard/event")
async def update_event(event: Event):
    if event.id == "":
        event.id = uuid4()
    query = f"""
    MERGE (e:Event {{id: '{event.id}'}}) 
    SET  e.courseID = '{event.courseID}', e.what = '{event.what}', e.where = '{event.where}',
    e.roomID = '{event.roomID}', e.when = '{event.when}', e.timeSlotID = '{event.timeSlotID}',
    e.who = '{event.who}', e.teacherID = '{event.teacherID}', e.cycle = '{event.cycle}'
    RETURN e
    """
    query_neo4j(query)

    return {"message": "Event created successfully"}


### START SERVER
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000)
