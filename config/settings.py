import os
import psycopg2
from graph_db.connection import Neo4jConnection
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    db = Neo4jConnection(
        uri=os.getenv('URI'),
        user=os.getenv('USER'),
        password=os.getenv('PASSWORD')
    )
    postgres_conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        database=os.getenv('POSTGRES_WMS_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )

class Settings:
    is_testing = os.getenv('IS_TESTING', 'false').lower() == 'true'