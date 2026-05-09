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
    degree = Column(String)
    semester = Column(String)
    specialization = Column(String)
    career_goal = Column(String)
    skills = Column(Text)
    weak_areas = Column(Text)
    daily_study_hours = Column(String)
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_student_key(first_name):
    year = datetime.now().year
    db = SessionLocal()
    while True:
        random_number = random.randint(1, 9999)
        student_key = f"D{year}-{random_number:04d}"
        exists = db.query(Student).filter(Student.student_key == student_key).first()
        if not exists:
            db.close()
            return student_key

# --- Business Logic Functions (API Compatible) ---

def register_student(first_name, middle_name, last_name, email, password):
    if not first_name or not last_name or not email or not password:
        return {"success": False, "message": "Required fields missing"}

    db = SessionLocal()
    try:
        student_key = generate_student_key(first_name)
        new_student = Student(
            student_key=student_key,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            password_hash=hash_password(password),
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(new_student)
        db.commit()
        return {"success": True, "message": "Registered successfully", "student_key": student_key}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": "Email already registered or connection error"}
    finally:
        db.close()

def login_student(student_key, password):
    db = SessionLocal()
    try:
        pwd_hash = hash_password(password)
        student = db.query(Student).filter(Student.student_key == student_key, Student.password_hash == pwd_hash).first()
        
        if student:
            onboarding_count = db.query(OnboardingAnswer).filter(OnboardingAnswer.student_id == student.id).count()
            return {
                "success": True,
                "onboarding_completed": onboarding_count > 0,
                "student": {
                    "id": student.id,
                    "student_key": student.student_key,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "email": student.email
                }
            }
        return {"success": False, "message": "Invalid credentials"}
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
        profile = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first()
        student = db.query(Student).filter(Student.id == student_id).first()
        
        if not student:
            return None
            
        full_name = f"{student.first_name} {student.middle_name or ''} {student.last_name}".strip()
        full_name = " ".join(full_name.split())
        
        if not profile:
            return {"full_name": full_name}

        return {
            "full_name": full_name,
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

def save_student_profile(student_id, degree, semester, specialization, career_goal, skills, weak_areas, daily_study_hours):
    db = SessionLocal()
    try:
        profile = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first()
        if not profile:
            profile = StudentProfile(student_id=student_id)
            db.add(profile)
        
        profile.degree = degree
        profile.semester = semester
        profile.specialization = specialization
        profile.career_goal = career_goal
        profile.skills = skills
        profile.weak_areas = weak_areas
        profile.daily_study_hours = daily_study_hours
        profile.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        db.commit()
        return {"success": True}
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