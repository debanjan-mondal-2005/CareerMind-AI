import sys
import os
import json
import shutil
import uuid
import asyncio
from pathlib import Path
from typing import Optional, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, BackgroundTasks
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
# Local module imports
from image_ai.hf_image_client import HFImageClient
from llm.hf_client import HFClient
from document_ai.pdf_reader import extract_text_from_pdf
from document_ai.pdf_qa_agent import PDFQAAgent
from rag.embedding_manager import get_model

app = FastAPI(
    title="CareerMind AI API",
    description="Multi-Agent RAG-Based Career Mentor API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from database.db import (
    create_tables,
    migrate_student_table,
    register_student,
    login_student,
    save_chat_history,
    save_onboarding_answer,
    save_student_profile,
    get_onboarding_answers,
    get_student_profile_data
)

from mail.email_service import send_registration_email
from agents.career_mentor_agent import CareerMentorAgent
from agents.profile_builder_agent import ProfileBuilderAgent
from agents.specialized_agents import (
    SkillGapAgent,
    CareerRoadmapAgent,
    ProjectRecommendationAgent,
    InterviewPreparationAgent
)
from agents.goal_web_agent import GoalAwareWebAgent

# -----------------------------
# Directory setup
# -----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMAGE_UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads" / "images"
IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

PDF_UPLOAD_DIR = PROJECT_ROOT / "backend" / "uploads" / "pdfs"
PDF_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Mount static directory for generated images
app.mount(
    "/generated-images",
    StaticFiles(directory=str(IMAGE_UPLOAD_DIR)),
    name="generated-images"
)

# In-memory PDF storage per student (reset on restart)
PDF_MEMORY = {}

# -----------------------------
# Startup Database Logic
# -----------------------------
async def init_db_task():
    try:
        print("Checking environment variables...")
        print(f"HF_TOKEN set: {bool(os.getenv('HF_TOKEN'))}")
        print(f"GROQ_API_KEY set: {bool(os.getenv('GROQ_API_KEY'))}")
        print(f"DATABASE_URL set: {bool(os.getenv('DATABASE_URL'))}")
        
        print("Initializing database tables (background task)...")
        # Run synchronous create_tables in a thread to not block event loop
        # Already handled in startup_event for safety, but keeping this for logging environment
        # await asyncio.to_thread(create_tables)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Environment check failed: {e}")



@app.on_event("startup")
async def startup_event():
    # 1. Initialize DB (Sync and Blocking to ensure tables exist before first request)
    try:
        print("🚀 Initializing database tables...")
        from database.db import create_tables, migrate_student_table
        create_tables()
        # Run migrations after tables are created/checked
        migrate_student_table()
        print("✅ Database ready and migrated.")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

    # 2. Run environment checks (Non-blocking background task)
    asyncio.create_task(init_db_task())

    # 3. Warm up embedding model (Disabled for Render Free Tier stability)
    # if os.getenv("USE_INDIC_EMBEDDINGS", "false").lower() == "true":
    #     asyncio.create_task(asyncio.to_thread(get_model))

    pass



# -----------------------------
# Request Models
# -----------------------------

class ImageGenerationRequest(BaseModel):
    student_key: str
    password: str
    prompt: str

class RegisterRequest(BaseModel):
    first_name: str
    middle_name: Optional[str] = ""
    last_name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    student_key: str
    password: str

class CareerChatRequest(BaseModel):
    student_key: str
    password: str
    question: str

class AgentRequest(BaseModel):
    student_key: str
    password: str

class OnboardingAnswerItem(BaseModel):
    question: str
    answer: str

class OnboardingRequest(BaseModel):
    student_key: str
    password: str
    answers: List[OnboardingAnswerItem]

class StudentTypeRequest(BaseModel):
    student_key: str
    password: str
    student_type: str

class SchoolOnboardingRequest(BaseModel):
    student_key: str
    password: str
    full_name: str
    grade_class: str
    board: str
    stream_interest: str
    career_goal: str
    favorite_subjects: str
    weak_subjects: str
    skills_interested: str
    current_skill_level: str
    learning_style: str
    future_target: str
    notes: Optional[str] = ""

class ProfileRequest(BaseModel):
    student_key: str
    password: str
    degree: str
    semester: str
    specialization: str
    career_goal: str
    skills: str
    weak_areas: str
    daily_study_hours: str

class ResendStudentKeyRequest(BaseModel):
    email: str

# In-memory resend cooldown storage
RESEND_COOLDOWN = {}
RESEND_WAIT_SECONDS = 60

# -----------------------------
# Helper Functions
# -----------------------------

def authenticate_student(student_key, password):
    login_result = login_student(student_key, password)
    if not login_result["success"]:
        return None, login_result
    return login_result["student"], login_result

def is_valid_ai_response(response: str) -> bool:
    """Check if the AI response is valid and not an error/empty."""
    if not response or not isinstance(response, str):
        return False
    error_keywords = ["error:", "failed to", "cannot find", "unable to", "api_key not found"]
    resp_lower = response.lower().strip()
    if any(kw in resp_lower for kw in error_keywords) and len(resp_lower) < 150:
        return False
    return len(resp_lower) > 5

async def error_gen(message: str):
    """Yield a simple error message for streaming endpoints."""
    yield f"⚠️ Error: {message}"

def get_student_full_name(student):
    first_name = student.get("first_name", "")
    middle_name = student.get("middle_name", "")
    last_name = student.get("last_name", "")
    full_name = f"{first_name} {middle_name} {last_name}".strip()
    full_name = " ".join(full_name.split())
    return full_name if full_name else "student"

def is_simple_chat_question(question):
    q = question.lower().strip().replace("?", "")
    greetings = [
        "hi", "hello", "hey", "hii", "hello ai", "hi ai", "hey ai", "hello mentor", "hi mentor",
        "good morning", "good afternoon", "good evening",
        "how are you", "how are you?", "how r u", "how are u",
        "are you there", "can you help me",
        "bye", "goodbye", "good bye", "see you", "see you later", "ok bye",
    ]
    if q in greetings:
        return True
    
    identity_keywords = ["who are you", "what is this", "what are we", "who developed", "who made", "about you"]
    if any(kw in q for kw in identity_keywords):
        return False # Pass to AI Agent for professional identity answer

    if len(q.split()) <= 2 and not is_career_related_question(q):
        return True
    return False

def is_career_related_question(question):
    q = question.lower()
    career_keywords = [
        "career", "skill", "skills", "learn", "roadmap", "project", "projects",
        "interview", "resume", "job", "jobs", "internship", "internships",
        "data scientist", "data science", "software engineer",
        "ai", "ml", "machine learning", "deep learning", "rag", "llm",
        "deployment", "docker", "fastapi", "sql", "python", "dsa",
        "salary", "company", "companies", "hiring"
    ]
    return any(keyword in q for keyword in career_keywords)

def needs_web_search(question):
    q = question.lower()
    web_keywords = [
        "latest", "current", "today", "now", "2025", "2026",
        "opening", "openings", "hiring", "internship", "internships",
        "job", "jobs", "salary", "companies", "company",
        "trend", "trends", "recent", "currently", "apply", "vacancy", "vacancies"
    ]
    return any(keyword in q for keyword in web_keywords)

# Quick PDF / Image intent detection (sync with CareerMentorAgent)
def is_image_generation_request(question: str) -> bool:
    image_keywords = [
        "generate image", "draw", "create picture", "make a diagram",
        "visualize", "illustrate", "create an image", "generate a diagram",
        "image of", "draw a", "paint a", "generate a picture"
    ]
    question_lower = question.lower()
    return any(kw in question_lower for kw in image_keywords)

def is_pdf_query_request(question: str, pdf_available: bool = False) -> bool:
    pdf_keywords = [
        "my pdf", "uploaded document", "the pdf", "my document",
        "my resume", "my cv", "my file", "the document",
        "resume", "cv"
    ]
    question_lower = question.lower()
    
    # Explicit PDF keywords
    if any(kw in question_lower for kw in pdf_keywords):
        return True
    
    # If PDF is available, check for personal info questions that could be in resume
    if pdf_available:
        personal_keywords = [
            "my name", "my email", "my phone", "my contact",
            "my experience", "my skills", "my education",
            "my projects", "my background", "my qualification",
            "from my", "about me", "tell me about"
        ]
        if any(kw in question_lower for kw in personal_keywords):
            return True
    
    return False

# ----------------------------------------------------------------------
# Basic Routes
# ----------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "CareerMind AI API is running"}

@app.get("/health")
def health_check():
    health = {
        "status": "healthy",
        "database": "unknown",
        "config": {
            "HF_TOKEN_SET": bool(os.getenv("HF_TOKEN")),
            "GROQ_API_KEY_SET": bool(os.getenv("GROQ_API_KEY")),
            "TAVILY_API_KEY_SET": bool(os.getenv("TAVILY_API_KEY")),
            "RESEND_API_KEY_SET": bool(os.getenv("RESEND_API_KEY"))
        }
    }
    try:
        # pyrefly: ignore [missing-import]
        from sqlalchemy import text
        from database.db import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "degraded"
    return health

# ----------------------------------------------------------------------
# Register / Login / Onboarding / Profile
# ----------------------------------------------------------------------
@app.post("/register")
async def register(request: RegisterRequest, background_tasks: BackgroundTasks):
    # Pass background_tasks to email sending later, but first register in DB
    result = await asyncio.to_thread(
        register_student,
        request.first_name,
        request.middle_name,
        request.last_name,
        request.email,
        request.password
    )
    if result["success"]:
        # Schedule email sending using BackgroundTasks
        background_tasks.add_task(
            send_registration_email,
            to_email=request.email,
            first_name=request.first_name,
            student_key=result["student_key"]
        )
        return {
            "registration": result,
            "email": {
                "status": "queued",
                "message": "Student Key email is being sent in background."
            }
        }
    return {"registration": result, "email": "Not sent due to registration failure"}

@app.post("/resend-student-key")
async def resend_student_key_endpoint(request: ResendStudentKeyRequest, background_tasks: BackgroundTasks):
    from database.db import SessionLocal, Student
    import time
    
    email = request.email.strip().lower()
    now = time.time()
    
    # 1. Rate limiting check
    if email in RESEND_COOLDOWN:
        elapsed = now - RESEND_COOLDOWN[email]
        if elapsed < RESEND_WAIT_SECONDS:
            remaining = int(RESEND_WAIT_SECONDS - elapsed)
            return {
                "success": False, 
                "message": f"Please wait {remaining} seconds before requesting again.",
                "remaining_seconds": remaining
            }
    
    # Update cooldown timestamp
    RESEND_COOLDOWN[email] = now
    
    # 2. Logic: find student by email
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.email == email).first()
        if student:
            print(f"[RESEND] Queuing email for: {email}")
            background_tasks.add_task(
                send_registration_email,
                to_email=student.email,
                first_name=student.first_name,
                student_key=student.student_key
            )
        else:
            print(f"[RESEND] Email not found (silent success): {email}")
            
        # 3. Safe response: do not expose whether email exists
        return {
            "success": True,
            "message": "If this email is registered, the Student Key will be sent shortly."
        }
    finally:
        db.close()

@app.post("/login")
def login(request: LoginRequest):
    res = login_student(request.student_key, request.password)
    if res.get("success") and "student" in res:
        from database.db import get_student_language
        res["language_mode"] = get_student_language(res["student"]["id"])
    return res

@app.post("/onboarding")
def save_onboarding(request: OnboardingRequest, background_tasks: BackgroundTasks):
    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return login_result
    try:
        for item in request.answers:
            save_onboarding_answer(
                student_id=student["id"],
                question=item.question,
                answer=item.answer
            )
        
        # Build AI Profile in background to reduce user wait time
        background_tasks.add_task(
            process_ai_profile_background,
            student_id=student["id"]
        )
        
        return {"success": True, "message": "Onboarding answers saved successfully. AI Profile is being built."}
    except Exception as e:
        return {"success": False, "message": f"Error saving onboarding answers: {str(e)}"}

def process_ai_profile_background(student_id: int):
    """Helper function to build AI profile in the background."""
    try:
        onboarding_answers = get_onboarding_answers(student_id)
        if onboarding_answers:
            answers_list = [{"question": row[0], "answer": row[1]} for row in onboarding_answers]
            profile_agent = ProfileBuilderAgent()
            profile_result = profile_agent.build_profile(answers_list)
            if profile_result["success"]:
                profile = profile_result["profile"]
                save_student_profile(
                    student_id=student_id,
                    full_name=profile.get("full_name", ""),
                    stream=profile.get("stream", ""),
                    degree=profile.get("degree", ""),
                    semester=profile.get("semester", ""),
                    specialization=profile.get("specialization", ""),
                    career_goal=profile.get("career_goal", ""),
                    skills=json.dumps(profile.get("skills", [])) if isinstance(profile.get("skills"), list) else profile.get("skills", ""),
                    weak_areas=json.dumps(profile.get("weak_areas", [])) if isinstance(profile.get("weak_areas"), list) else profile.get("weak_areas", ""),
                    daily_study_hours=profile.get("daily_study_hours", "")
                )
    except Exception as e:
        print(f"Background Profile Building Error: {e}")

@app.post("/set-student-type")
def set_student_type_endpoint(request: StudentTypeRequest):
    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return login_result
    from database.db import set_student_type
    result = set_student_type(student["id"], request.student_type)
    return result

@app.post("/school-onboarding")
def save_school_onboarding(request: SchoolOnboardingRequest):
    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return login_result
    from database.db import save_school_student_profile
    try:
        result = save_school_student_profile(
            student_id=student["id"],
            full_name=request.full_name,
            grade_class=request.grade_class,
            board=request.board,
            stream_interest=request.stream_interest,
            career_goal=request.career_goal,
            favorite_subjects=request.favorite_subjects,
            weak_subjects=request.weak_subjects,
            skills_interested=request.skills_interested,
            current_skill_level=request.current_skill_level,
            learning_style=request.learning_style,
            future_target=request.future_target,
            notes=request.notes
        )
        return {"success": True, "message": "School onboarding completed successfully"}
    except Exception as e:
        return {"success": False, "message": f"Error saving school onboarding: {str(e)}"}

@app.post("/save-profile")
def save_profile(request: ProfileRequest):
    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return login_result
    try:
        save_student_profile(
            student_id=student["id"],
            degree=request.degree,
            semester=request.semester,
            specialization=request.specialization,
            career_goal=request.career_goal,
            skills=request.skills,
            weak_areas=request.weak_areas,
            daily_study_hours=request.daily_study_hours
        )
        return {"success": True, "message": "Student profile saved successfully"}
    except Exception as e:
        return {"success": False, "message": f"Error saving profile: {str(e)}"}

# ----------------------------------------------------------------------
# Career Chat (with PDF support & retrieval-first logic)
# ----------------------------------------------------------------------
@app.post("/career-chat")
def career_chat(request: CareerChatRequest):
    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return login_result

    profile = get_student_profile_data(student["id"])
    if not profile:
        return {"success": False, "message": "Student profile not found. Please complete onboarding and profile builder first."}

    from database.db import get_student_language, update_student_language
    from utils.language_manager import detect_language_command

    question = request.question.strip()
    lang_mode = get_student_language(student["id"])
    switch_cmd = detect_language_command(question)
    if switch_cmd:
        lang_mode = switch_cmd
        update_student_language(student["id"], lang_mode)

    agent = CareerMentorAgent()
    agent.set_student_id(student["id"])

    pdf_data = PDF_MEMORY.get(student["id"])
    if pdf_data:
        agent.set_current_pdf(pdf_data["path"])

    result = agent.answer_question(profile, question)

    if is_valid_ai_response(result.get("answer", "")):
        try:
            save_chat_history(
                student_id=student["id"],
                user_message=question,
                ai_response=result.get("answer", ""),
                sources_used=json.dumps(result.get("sources", []))
            )
        except Exception as e:
            result["warning"] = f"Answer generated but chat history not saved: {str(e)}"

    return {
        "success": True,
        "language_mode": lang_mode,
        **result
    }

# ----------------------------------------------------------------------
# Smart Chat (with routing)
# ----------------------------------------------------------------------
@app.post("/smart-chat")
def smart_chat(request: CareerChatRequest):
    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return login_result

    profile = get_student_profile_data(student["id"])
    if not profile:
        return {"success": False, "message": "Student profile not found."}

    from database.db import get_student_language, update_student_language
    from utils.language_manager import detect_language_command

    question = request.question.strip()
    lang_mode = get_student_language(student["id"])
    switch_cmd = detect_language_command(question)
    if switch_cmd:
        lang_mode = switch_cmd
        update_student_language(student["id"], lang_mode)

    # Main AI Agent (CareerMentorAgent)
    agent = CareerMentorAgent()
    agent.set_student_id(student["id"])
    pdf_data = PDF_MEMORY.get(student["id"])
    if pdf_data:
        agent.set_current_pdf(pdf_data["path"])
    
    result = agent.answer_question(profile, question)
    
    if is_valid_ai_response(result.get("answer", "")):
        try:
            save_chat_history(
                student_id=student["id"],
                user_message=question,
                ai_response=result.get("answer", ""),
                sources_used=json.dumps({"route": "career_mentor_agent", "sources": result.get("sources", [])})
            )
        except: pass
    
    return {
        "success": True,
        "route": "career_mentor_agent",
        "language_mode": lang_mode,
        **result
    }

# ----------------------------------------------------------------------
# Development / Testing Tools
# ----------------------------------------------------------------------
# Specialized Multi-Agent APIs (unchanged)
# ----------------------------------------------------------------------
@app.post("/multi-agent/skill-gap")
def skill_gap(request: AgentRequest):
    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return login_result
    profile = get_student_profile_data(student["id"])
    if not profile:
        return {"success": False, "message": "Student profile not found"}
    agent = SkillGapAgent()
    result = agent.analyze(profile)
    return {"success": True, "agent": result["agent"], "answer": result["answer"], "sources": result["sources"]}

@app.post("/multi-agent/roadmap")
def roadmap(request: AgentRequest):
    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return login_result
    profile = get_student_profile_data(student["id"])
    if not profile:
        return {"success": False, "message": "Student profile not found"}
    agent = CareerRoadmapAgent()
    result = agent.generate_roadmap(profile)
    return {"success": True, "agent": result["agent"], "answer": result["answer"], "sources": result["sources"]}

@app.post("/multi-agent/projects")
def projects(request: AgentRequest):
    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return login_result
    profile = get_student_profile_data(student["id"])
    if not profile:
        return {"success": False, "message": "Student profile not found"}
    agent = ProjectRecommendationAgent()
    result = agent.recommend_projects(profile)
    return {"success": True, "agent": result["agent"], "answer": result["answer"], "sources": result["sources"]}

@app.post("/multi-agent/interview")
def interview(request: AgentRequest):
    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return login_result
    profile = get_student_profile_data(student["id"])
    if not profile:
        return {"success": False, "message": "Student profile not found"}
    agent = InterviewPreparationAgent()
    result = agent.prepare_interview(profile)
    return {"success": True, "agent": result["agent"], "answer": result["answer"], "sources": result["sources"]}

# ----------------------------------------------------------------------
# Goal-Aware Web Chat (unchanged)
# ----------------------------------------------------------------------
@app.post("/goal-web-chat")
def goal_web_chat(request: CareerChatRequest):
    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return login_result
    profile = get_student_profile_data(student["id"])
    if not profile:
        return {"success": False, "message": "Student profile not found."}
    agent = GoalAwareWebAgent()
    result = agent.answer_with_web_and_rag(profile, request.question)
    if is_valid_ai_response(result["answer"]):
        try:
            combined_sources = {
                "web_sources": result["web_sources"],
                "rag_sources": result["rag_sources"],
                "web_query": result["web_query"]
            }
            save_chat_history(
                student_id=student["id"],
                user_message=request.question,
                ai_response=result["answer"],
                sources_used=json.dumps(combined_sources)
            )
        except Exception as e:
            return {
                "success": True,
                "answer": result["answer"],
                "web_query": result["web_query"],
                "web_sources": result["web_sources"],
                "rag_sources": result["rag_sources"],
                "warning": f"Answer generated but chat history not saved: {str(e)}"
            }
    return {
        "success": True,
        "answer": result["answer"],
        "web_query": result["web_query"],
        "web_sources": result["web_sources"],
        "rag_sources": result["rag_sources"]
    }

# ----------------------------------------------------------------------
# PDF Upload & Ask (with vector DB)
# ----------------------------------------------------------------------
@app.post("/upload-pdf")
async def upload_pdf(
    student_key: str = Form(...),
    password: str = Form(...),
    file: UploadFile = File(...)
):
    student, login_result = authenticate_student(student_key, password)
    if not student:
        return login_result
    if not file.filename.lower().endswith(".pdf"):
        return {"success": False, "message": "Only PDF files are allowed."}
    safe_filename = f"{student['id']}_{uuid.uuid4().hex}_{file.filename}"
    pdf_path = PDF_UPLOAD_DIR / safe_filename
    try:
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        pdf_text = extract_text_from_pdf(pdf_path)
        if not pdf_text:
            return {"success": False, "message": "PDF uploaded, but no readable text found."}

        PDF_MEMORY[student["id"]] = {
            "filename": file.filename,
            "path": str(pdf_path),
            "text": pdf_text
        }

        # Build vector DB for this PDF
        from rag.pdf_vector_store import build_pdf_vector_db
        try:
            db_path, chunk_count = build_pdf_vector_db(student["id"], str(pdf_path))
            print(f"PDF vector DB created: {db_path} with {chunk_count} chunks")
        except Exception as e:
            print(f"PDF vector indexing failed: {e}")

        return {
            "success": True,
            "message": "PDF uploaded and processed successfully.",
            "filename": file.filename,
            "characters_extracted": len(pdf_text)
        }
    except Exception as e:
        return {"success": False, "message": f"PDF upload failed: {str(e)}"}

@app.post("/ask-pdf")
def ask_pdf(
    student_key: str = Form(...),
    password: str = Form(...),
    question: str = Form(...)
):
    student, login_result = authenticate_student(student_key, password)
    if not student:
        return login_result
    pdf_data = PDF_MEMORY.get(student["id"])
    if not pdf_data:
        return {"success": False, "message": "No PDF found. Please upload a PDF first."}
    agent = PDFQAAgent()
    result = agent.answer_pdf_question(pdf_data["text"], question)
    return {
        "success": result["success"],
        "answer": result["answer"],
        "filename": pdf_data["filename"],
        "fallback": result.get("fallback", False)
    }

# ----------------------------------------------------------------------
# Direct Image Generation (standalone)
# ----------------------------------------------------------------------
@app.post("/generate-image")
def generate_image(request: ImageGenerationRequest):
    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return login_result
    if not request.prompt.strip():
        return {"success": False, "message": "Image prompt cannot be empty."}
    agent = HFImageClient()
    result = agent.generate_image(prompt=request.prompt, output_dir=IMAGE_UPLOAD_DIR)
    if not result["success"]:
        return result
    # Use the cloud URL if available, otherwise use the relative path
    image_url = result.get("url", f"/generated-images/{result['filename']}")
    return {
        "success": True,
        "message": "Image generated successfully.",
        "image_url": image_url,
        "filename": result["filename"]
    }

# ----------------------------------------------------------------------
# Smart Chat STREAMING (with student ID and PDF)
# ----------------------------------------------------------------------
# pyrefly: ignore [missing-import]
from fastapi.responses import StreamingResponse

@app.post("/smart-chat-stream")
async def smart_chat_stream(request: CareerChatRequest):
    async def error_gen(msg):
        yield f"⚠️ {msg}"

    student, login_result = authenticate_student(request.student_key, request.password)
    if not student:
        return StreamingResponse(error_gen(login_result.get("message", "Authentication failed")), media_type="text/plain")

    profile = get_student_profile_data(student["id"])
    if not profile:
        return StreamingResponse(error_gen("Student profile not found. Please complete onboarding first."), media_type="text/plain")

    from database.db import get_student_language, update_student_language
    from utils.language_manager import detect_language_command

    question = request.question.strip()
    
    lang_mode = get_student_language(student["id"])
    switch_cmd = detect_language_command(question)
    if switch_cmd:
        lang_mode = switch_cmd
        update_student_language(student["id"], lang_mode)

    agent = CareerMentorAgent()
    agent.set_student_id(student["id"])
    pdf_data = PDF_MEMORY.get(student["id"])
    if pdf_data:
        agent.set_current_pdf(pdf_data["path"])
    
    async def token_generator():
        full_answer = ""
        try:
            for token in agent.stream_answer_question(profile, question):
                full_answer += token
                yield token
            
            # Save to SQL Database after completion
            if is_valid_ai_response(full_answer):
                save_chat_history(
                    student_id=student["id"],
                    user_message=question,
                    ai_response=full_answer,
                    sources_used="[]"
                )
        except Exception as e:
            yield f"\n\n⚠️ Error during streaming: {str(e)}"

    headers = {"X-Language-Mode": lang_mode, "Access-Control-Expose-Headers": "X-Language-Mode"}
    return StreamingResponse(token_generator(), media_type="text/plain", headers=headers)