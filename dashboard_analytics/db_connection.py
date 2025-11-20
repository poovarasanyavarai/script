import os
import psycopg2

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "z_agent"),
        user=os.getenv("DB_USER", "z_agent_user"),
        password=os.getenv("DB_PASSWORD", "z_agent_password"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5666")
    )
