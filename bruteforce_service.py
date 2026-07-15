import psycopg2
from datetime import datetime, timedelta

# =========================================================
# DATABASE CONFIG (Matches your app.py)
# =========================================================
DB_HOST = "localhost"
DB_NAME = "hawkins_cyber"
DB_USER = "postgres"
DB_PASS = "admin123"

MAX_ATTEMPTS = 5
LOCK_MINUTES = 15

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def initialize():
    """Creates the login_attempts table if it doesn't exist."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                username VARCHAR(255) PRIMARY KEY,
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Bruteforce DB Initialization Error: {e}")

def is_locked(username):
    """Checks if the user is currently locked out."""
    initialize()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT locked_until FROM login_attempts WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row and row[0]:
            lock_time = row[0]
            # If the current time is past the lock time, reset it
            if datetime.now() >= lock_time:
                reset_attempts(username)
                return False
            # Otherwise, they are still locked
            return True
            
        return False
    except Exception as e:
        print(f"Error checking lock status: {e}")
        return False

def register_failed_attempt(username):
    """Increments the failed attempt counter and locks the account if MAX_ATTEMPTS is reached."""
    initialize()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Upsert: Insert a new row if user doesn't exist, otherwise increment failed_attempts
        cur.execute("""
            INSERT INTO login_attempts (username, failed_attempts)
            VALUES (%s, 1)
            ON CONFLICT (username)
            DO UPDATE SET failed_attempts = login_attempts.failed_attempts + 1
            RETURNING failed_attempts;
        """, (username,))
        
        attempts = cur.fetchone()[0]

        # If attempts reach the maximum, apply the time lock
        if attempts >= MAX_ATTEMPTS:
            cur.execute("""
                UPDATE login_attempts
                SET locked_until = NOW() + INTERVAL '%s minutes'
                WHERE username = %s;
            """, (LOCK_MINUTES, username))
            
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error registering failed attempt: {e}")

def reset_attempts(username):
    """Clears failed attempts and removes any locks upon a successful login."""
    initialize()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE login_attempts
            SET failed_attempts = 0, locked_until = NULL
            WHERE username = %s;
        """, (username,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error resetting attempts: {e}")

def remaining_attempts(username):
    """Calculates how many attempts the user has left."""
    initialize()
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT failed_attempts FROM login_attempts WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            attempts = row[0]
            return max(0, MAX_ATTEMPTS - attempts)
            
        return MAX_ATTEMPTS
    except Exception as e:
        print(f"Error checking remaining attempts: {e}")
        return MAX_ATTEMPTS