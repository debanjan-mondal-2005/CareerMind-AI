import sqlite3
import hashlib
import random
from datetime import datetime

DB_NAME = "careermind.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_key TEXT UNIQUE NOT NULL,
        first_name TEXT NOT NULL,
        middle_name TEXT,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS onboarding_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER UNIQUE NOT NULL,
        degree TEXT,
        semester TEXT,
        specialization TEXT,
        career_goal TEXT,
        skills TEXT,
        weak_areas TEXT,
        daily_study_hours TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        user_message TEXT NOT NULL,
        ai_response TEXT NOT NULL,
        sources_used TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def generate_student_key(first_name):
    """
    Generate a unique student key in format: D2026-XXXX
    where XXXX is a random 4-digit number (0001-9999)
    """
    year = datetime.now().year
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Keep generating until we get a unique key
    while True:
        random_number = random.randint(1, 9999)
        student_key = f"D{year}-{random_number:04d}"
        
        cursor.execute("SELECT COUNT(*) FROM students WHERE student_key = ?", (student_key,))
        count = cursor.fetchone()[0]
        
        if count == 0:  # Key is unique
            break
    
    conn.close()
    return student_key


def register_student(first_name, middle_name, last_name, email, password):
    if not first_name or not last_name or not email or not password:
        return {
            "success": False,
            "message": "First name, last name, email and password are required"
        }

    conn = get_connection()
    cursor = conn.cursor()

    student_key = generate_student_key(first_name)
    password_hash = hash_password(password)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute("""
        INSERT INTO students (
            student_key,
            first_name,
            middle_name,
            last_name,
            email,
            password_hash,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            student_key,
            first_name,
            middle_name,
            last_name,
            email,
            password_hash,
            created_at
        ))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Student registered successfully",
            "student_key": student_key
        }

    except sqlite3.IntegrityError:
        conn.close()
        return {
            "success": False,
            "message": "Email already registered"
        }


def login_student(student_key, password):
    if not student_key or not password:
        return {
            "success": False,
            "message": "Student key and password are required"
        }

    conn = get_connection()
    cursor = conn.cursor()

    password_hash = hash_password(password)

    cursor.execute("""
    SELECT * FROM students
    WHERE student_key = ? AND password_hash = ?
    """, (student_key, password_hash))

    student = cursor.fetchone()
    conn.close()

    if student:
        return {
            "success": True,
            "message": "Login successful",
            "student": {
                "id": student["id"],
                "student_key": student["student_key"],
                "first_name": student["first_name"],
                "middle_name": student["middle_name"],
                "last_name": student["last_name"],
                "email": student["email"]
            }
        }

    return {
        "success": False,
        "message": "Invalid student key or password"
    }
    
def save_onboarding_answer(student_id, question, answer):
    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO onboarding_answers (student_id, question, answer, created_at)
    VALUES (?, ?, ?, ?)
    """, (student_id, question, answer, created_at))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Answer saved successfully"
    }
    
def get_onboarding_answers(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT question, answer FROM onboarding_answers
    WHERE student_id = ?
    ORDER BY id ASC
    """, (student_id,))

    answers = cursor.fetchall()
    conn.close()

    return answers


def save_student_profile(student_id, degree, semester, specialization, career_goal, skills, weak_areas, daily_study_hours):
    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT OR REPLACE INTO student_profiles (
        student_id,
        degree,
        semester,
        specialization,
        career_goal,
        skills,
        weak_areas,
        daily_study_hours,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id,
        degree,
        semester,
        specialization,
        career_goal,
        skills,
        weak_areas,
        daily_study_hours,
        created_at
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Student profile saved successfully"
    }
    
def save_chat_history(student_id, user_message, ai_response, sources_used):
    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO chat_history (
        student_id,
        user_message,
        ai_response,
        sources_used,
        created_at
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        student_id,
        user_message,
        ai_response,
        sources_used,
        created_at
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Chat history saved successfully"
    }