# To copy small DB
# CALL apoc.export.cypher.all("eftk.cypher");
# Then, just run the commands in eftk.cypher

import neo4j
import os

# For Local Deployment
from dotenv import load_dotenv

load_dotenv()

# For Vercel Deployment (For local, it loads from local .env file)
neo4j_uri = os.environ.get("NEO4J_URI")
neo4j_username = os.environ.get("NEO4J_USERNAME")
neo4j_password = os.environ.get("NEO4J_PASSWORD")

neo4j_db = "neo4j"

print("NEO4J URI: ", neo4j_uri)


# Neo4j
class Neo4j:
    def __init__(self, uri, user, password):
        self.driver = neo4j.GraphDatabase.driver(
            uri, auth=(user, password), max_connection_lifetime=200
        )

    def close(self):
        self.driver.close()


neo4jDriver = Neo4j(neo4j_uri, neo4j_username, neo4j_password)


# Execute Query
def query_neo4j(query):
    return neo4jDriver.driver.execute_query(query, database_=neo4j_db)


def query_neo4j_return_df(query):
    return neo4jDriver.driver.execute_query(
        query, result_transformer_=neo4j.Result.to_df, expand=True, database_=neo4j_db
    )
