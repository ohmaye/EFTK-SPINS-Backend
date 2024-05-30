from neo4jDriver import query_neo4j
from fastapi_setup import app
from fastapi import FastAPI
from models import DeleteEntity

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
