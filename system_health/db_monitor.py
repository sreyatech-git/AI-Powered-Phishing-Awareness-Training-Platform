import time
import psycopg2



DB_HOST = "localhost"
DB_NAME = "hawkins_cyber"
DB_USER = "postgres"
DB_PASS = ""
DB_PORT = "5432"




def get_database_health():

    start = time.perf_counter()

    try:

        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )

        latency = round((time.perf_counter() - start) * 1000, 2)

        cur = conn.cursor()

        # PostgreSQL Version
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]

        # Current Database
        cur.execute("SELECT current_database();")
        db_name = cur.fetchone()[0]

        # Number of Tables
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema='public';
        """)
        table_count = cur.fetchone()[0]

        # Database Size
        cur.execute("""
            SELECT pg_database_size(current_database());
        """)
        db_size = cur.fetchone()[0]

        # Active Connections
        cur.execute("""
            SELECT count(*)
            FROM pg_stat_activity
            WHERE datname=current_database();
        """)
        active_connections = cur.fetchone()[0]

        cur.close()
        conn.close()

        return {

            "status": "Healthy",

            "color": "green",

            "database": db_name,

            "latency": latency,

            "tables": table_count,

            "connections": active_connections,

            "size_mb": round(db_size / 1024 / 1024, 2),

            "version": version

        }

    except Exception as e:

        return {

            "status": "Offline",

            "color": "red",

            "error": str(e)

        }
