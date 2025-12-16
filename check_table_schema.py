#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor

def check_table_schema():
    """Check the schema of chatbot_metrics table."""

    # Connection parameters
    conn_params = {
        'host': 'localhost',
        'port': '5554',
        'user': 'z_agent_user',
        'password': 'z_agent_password',
        'database': 'z_agent'
    }

    try:
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get table schema
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'chatbot_metrics'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()

        print("chatbot_metrics table schema:")
        print("=" * 50)
        for i, col in enumerate(columns, 1):
            print(f"{i:2d}. {col['column_name']} - {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")

        print(f"\nTotal columns: {len(columns)}")

        # Also check if there's an id column
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'chatbot_metrics'
            AND table_schema = 'public'
            AND column_name = 'id'
        """)

        id_col = cursor.fetchone()
        if id_col:
            print("\nNote: Table has an 'id' column (likely auto-increment)")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_table_schema()