import hashlib
import random
import os
from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, create_mock_engine
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.declarative import declarative_base
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker
# pyrefly: ignore [missing-import]
from sqlalchemy.sql import text
from dotenv import load_dotenv

load_dotenv()

# --- Database Configuration ---
# Check for Cloud Database URL (Supabase). Fallback to local SQLite.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Local SQLite
    BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BACKEND_DIR, "careermind.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"
else:
    # Fix for Render/Heroku: replace postgres:// with postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Initialize SQLAlchemy with resilience for Cloud/Render
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL)
    print(f"📁 Using Local SQLite Database at: {DATABASE_URL}")
else:
    # Add timeout and pool recycling for Supabase/Render
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "connect_timeout": 10,
            "sslmode": "require"
        }
    )
    print("📡 Connected to Cloud Database (Supabase/PostgreSQL)")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Models ---
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    student_key = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    middle_name = Column(String)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    student_type = Column(String, nullable=True) # 'school' or 'college'
    email_sent_status = Column(String, nullable=True, default="pending") # pending, sent, failed
    email_sent_at = Column(String, nullable=True)
    created_at = Column(String, nullable=False)

class OnboardingAnswer(Base):
    __tablename__ = "onboarding_answers"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(String, nullable=False)

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), unique=True, nullable=False)
    full_name = Column(String)
    stream = Column(String)
    degree = Column(String)
    semester = Column(String)
    specialization = Column(String)
    career_goal = Column(String)
    skills = Column(Text)
    weak_areas = Column(Text)
    daily_study_hours = Column(String)
    created_at = Column(String, nullable=False)

class SchoolStudentProfile(Base):
    __tablename__ = "school_student_profiles"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), unique=True, nullable=False)
    full_name = Column(String)
    grade_class = Column(String)
    board = Column(String)
    stream_interest = Column(String)
    career_goal = Column(String)
    favorite_subjects = Column(Text)
    weak_subjects = Column(Text)
    skills_interested = Column(Text)
    current_skill_level = Column(String)
    learning_style = Column(String)
    future_target = Column(String)
    notes = Column(Text)
    created_at = Column(String, nullable=False)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    sources_used = Column(Text)
    created_at = Column(String, nullable=False)

# --- Database Core Functions ---

def create_tables():
    """Create all tables in the database (Works for both SQLite and Postgres)"""
    Base.metadata.create_all(bind=engine)

def migrate_student_table():
    print("[MIGRATION] Checking students table...")
    db = SessionLocal()
    try:
        # Detect existing columns
        if DATABASE_URL.startswith("sqlite"):
            columns_query = text("PRAGMA table_info(students)")
            result = db.execute(columns_query).fetchall()
            existing_columns = [row[1] for row in result]
        else:
            # Postgres
            columns_query = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'students'")
            result = db.execute(columns_query).fetchall()
            existing_columns = [row[0] for row in result]

        # Define columns to add
        new_columns = [
            ("email_sent_status", "VARCHAR", "DEFAULT 'pending'"),
            ("email_sent_at", "VARCHAR", "NULL")
        ]

        migration_happened = False
        for col_name, col_type, col_extra in new_columns:
            if col_name not in existing_columns:
                print(f"[MIGRATION] Adding {col_name} to students table...")
                alter_query = text(f"ALTER TABLE students ADD COLUMN {col_name} {col_type} {col_extra}")
                db.execute(alter_query)
                print(f"[MIGRATION] {col_name} column added")
                migration_happened = True
            else:
                print(f"[MIGRATION] {col_name} already exists")

        if migration_happened:
            db.commit()
            print("[MIGRATION] Migration complete and committed")
        else:
            print("[MIGRATION] No migration needed")

    except Exception as e:
        db.rollback()
        print(f"[MIGRATION] ERROR: {str(e)}")
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_student_key(first_name, db):
    import time
    start_time = time.perf_counter()
    year = datetime.now().year
    prefix = first_name[0].upper() if first_name else "S"
    attempts = 0
    max_attempts = 20
    
    while attempts < max_attempts:
        attempts += 1
        random_number = random.randint(1, 9999)
        student_key = f"{prefix}{year}-{random_number:04d}"
        exists = db.query(Student).filter(Student.student_key == student_key).first()
        if not exists:
            # print(f"[DEBUG] Key generated in {attempts} attempts")
            return student_key
    
    raise Exception("Could not generate a unique student key after 20 attempts")

# --- Business Logic Functions (API Compatible) ---

def register_student(first_name, middle_name, last_name, email, password):
    import time
    total_start = time.perf_counter()
    
    if not first_name or not last_name or not email or not password:
        return {"success": False, "message": "Required fields missing"}

    # Normalize email
    email = email.strip().lower()

    t_session = time.perf_counter()
    db = SessionLocal()
    t_session_end = time.perf_counter()
    print(f"[REGISTER] DB session opened: {t_session_end - t_session:.4f}s")

    try:
        # Check duplicate email before anything else
        t_dup = time.perf_counter()
        existing_email = db.query(Student).filter(Student.email == email).first()
        t_dup_end = time.perf_counter()
        print(f"[REGISTER] Duplicate check: {t_dup_end - t_dup:.4f}s")
        
        if existing_email:
            return {"success": False, "message": "This email is already registered."}

        t_key = time.perf_counter()
        student_key = generate_student_key(first_name, db)
        t_key_end = time.perf_counter()
        print(f"[REGISTER] Student key generated: {t_key_end - t_key:.4f}s")

        t_hash = time.perf_counter()
        pwd_hash = hash_password(password)
        t_hash_end = time.perf_counter()
        print(f"[REGISTER] Password hashed: {t_hash_end - t_hash:.4f}s")

        new_student = Student(
            student_key=student_key,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            password_hash=pwd_hash,
            student_type=None,
            email_sent_status="pending",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        t_add = time.perf_counter()
        db.add(new_student)
        t_add_end = time.perf_counter()
        print(f"[REGISTER] DB add: {t_add_end - t_add:.4f}s")

        t_commit = time.perf_counter()
        db.commit()
        t_commit_end = time.perf_counter()
        print(f"[REGISTER] DB commit: {t_commit_end - t_commit:.4f}s")

        total_end = time.perf_counter()
        print(f"[REGISTER] Total time: {total_end - total_start:.4f}s")
        
        return {"success": True, "message": "Registered successfully", "student_key": student_key}
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        print(f"Registration Error: {error_msg}")
        if "UNIQUE constraint failed" in error_msg or "duplicate key value" in error_msg.lower():
            return {"success": False, "message": "This email is already registered."}
        return {"success": False, "message": f"Registration failed: {error_msg[:100]}"}
    finally:
        db.close()

def login_student(student_key, password):
    print(f"[AUTH] Login attempt for student_key: {student_key}")
    db = SessionLocal()
    try:
        pwd_hash = hash_password(password)
        student = db.query(Student).filter(Student.student_key == student_key, Student.password_hash == pwd_hash).first()
        
        if student:
            if student.student_type == 'school':
                onboarding_completed = db.query(SchoolStudentProfile).filter(SchoolStudentProfile.student_id == student.id).first() is not None
            elif student.student_type == 'college':
                onboarding_completed = db.query(OnboardingAnswer).filter(OnboardingAnswer.student_id == student.id).first() is not None or db.query(StudentProfile).filter(StudentProfile.student_id == student.id).first() is not None
            else:
                onboarding_completed = False

            return {
                "success": True,
                "onboarding_completed": onboarding_completed,
                "student": {
                    "id": student.id,
                    "student_key": student.student_key,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "email": student.email,
                    "student_type": student.student_type
                }
            }
        return {"success": False, "message": "Invalid credentials"}
    except Exception as e:
        print(f"Login Error: {str(e)}")
        return {"success": False, "message": f"Login connection error: {str(e)[:100]}"}
    finally:
        db.close()

def save_onboarding_answer(student_id, question, answer):
    db = SessionLocal()
    try:
        ans = OnboardingAnswer(
            student_id=student_id,
            question=question,
            answer=answer,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(ans)
        db.commit()
        return {"success": True}
    finally:
        db.close()

def get_onboarding_answers(student_id):
    db = SessionLocal()
    try:
        return db.query(OnboardingAnswer.question, OnboardingAnswer.answer).filter(OnboardingAnswer.student_id == student_id).all()
    finally:
        db.close()

def get_student_profile_data(student_id):
    """Retrieve full student profile and name data (Hybrid compatible)"""
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.id == student_id).first()
        
        if not student:
            return None
            
        full_name = f"{student.first_name} {student.middle_name or ''} {student.last_name}".strip()
        full_name = " ".join(full_name.split())
        
        if student.student_type == 'school':
            profile = db.query(SchoolStudentProfile).filter(SchoolStudentProfile.student_id == student_id).first()
            if not profile:
                return {"full_name": full_name, "student_type": "school"}
            return {
                "full_name": profile.full_name or full_name,
                "student_type": "school",
                "grade_class": profile.grade_class,
                "board": profile.board,
                "stream": profile.stream_interest,
                "career_goal": profile.career_goal,
                "favorite_subjects": profile.favorite_subjects,
                "weak_subjects": profile.weak_subjects,
                "skills": profile.skills_interested,
                "skill_level": profile.current_skill_level,
                "learning_style": profile.learning_style,
                "future_target": profile.future_target,
                "notes": profile.notes
            }
        else:
            profile = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first()
            if not profile:
                return {"full_name": full_name, "student_type": "college"}
            return {
                "full_name": profile.full_name or full_name,
                "student_type": "college",
                "stream": profile.stream,
                "degree": profile.degree,
                "semester": profile.semester,
                "specialization": profile.specialization,
                "career_goal": profile.career_goal,
                "skills": profile.skills,
                "weak_areas": profile.weak_areas,
                "daily_study_hours": profile.daily_study_hours
            }
    finally:
        db.close()

def save_student_profile(student_id, full_name, stream, degree, semester, specialization, career_goal, skills, weak_areas, daily_study_hours):
    db = SessionLocal()
    try:
        profile = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first()
        if not profile:
            profile = StudentProfile(
                student_id=student_id,
                full_name=full_name,
                stream=stream,
                degree=degree,
                semester=semester,
                specialization=specialization,
                career_goal=career_goal,
                skills=skills,
                weak_areas=weak_areas,
                daily_study_hours=daily_study_hours,
                created_at=datetime.now().isoformat()
            )
            db.add(profile)
        else:
            profile.full_name = full_name
            profile.stream = stream
            profile.degree = degree
            profile.semester = semester
            profile.specialization = specialization
            profile.career_goal = career_goal
            profile.skills = skills
            profile.weak_areas = weak_areas
            profile.daily_study_hours = daily_study_hours
        db.commit()
        return {"success": True}
    finally:
        db.close()

def set_student_type(student_id, student_type):
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.id == student_id).first()
        if student:
            student.student_type = student_type
            db.commit()
            return {"success": True}
        return {"success": False, "message": "Student not found"}
    finally:
        db.close()

def save_school_student_profile(student_id, full_name, grade_class, board, stream_interest, career_goal, favorite_subjects, weak_subjects, skills_interested, current_skill_level, learning_style, future_target, notes):
    db = SessionLocal()
    try:
        profile = db.query(SchoolStudentProfile).filter(SchoolStudentProfile.student_id == student_id).first()
        if not profile:
            profile = SchoolStudentProfile(student_id=student_id)
            db.add(profile)
        
        profile.full_name = full_name
        profile.grade_class = grade_class
        profile.board = board
        profile.stream_interest = stream_interest
        profile.career_goal = career_goal
        profile.favorite_subjects = favorite_subjects
        profile.weak_subjects = weak_subjects
        profile.skills_interested = skills_interested
        profile.current_skill_level = current_skill_level
        profile.learning_style = learning_style
        profile.future_target = future_target
        profile.notes = notes
        profile.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        db.commit()
        return {"success": True}
    finally:
        db.close()

def get_school_student_profile_data(student_id):
    db = SessionLocal()
    try:
        profile = db.query(SchoolStudentProfile).filter(SchoolStudentProfile.student_id == student_id).first()
        if not profile:
            return None
        return {
            "full_name": profile.full_name,
            "grade_class": profile.grade_class,
            "board": profile.board,
            "stream_interest": profile.stream_interest,
            "career_goal": profile.career_goal,
            "favorite_subjects": profile.favorite_subjects,
            "weak_subjects": profile.weak_subjects,
            "skills_interested": profile.skills_interested,
            "current_skill_level": profile.current_skill_level,
            "learning_style": profile.learning_style,
            "future_target": profile.future_target,
            "notes": profile.notes
        }
    finally:
        db.close()


def save_chat_history(student_id, user_message, ai_response, sources_used):
    db = SessionLocal()
    try:
        history = ChatHistory(
            student_id=student_id,
            user_message=user_message,
            ai_response=ai_response,
            sources_used=sources_used,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(history)
        db.commit()
        return {"success": True}
    finally:
        db.close()

# Initialize tables on startup
if __name__ == "__main__":
    create_tables()
    print("✅ Database Tables initialized!")