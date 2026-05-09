import sys
import os
import json
import shutil
import uuid
import asyncio
from pathlib import Path
from typing import Optional, List

# ---------- MUST be first: add backend folder to sys.path ----------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Third-party imports
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
from watchdog.observers import Observer
# pyrefly: ignore [missing-import]
from watchdog.events import FileSystemEventHandler

# Local module imports
from image_ai.hf_image_client import HFImageClient
from llm.hf_client import HFClient
from document_ai.pdf_reader import extract_text_from_pdf
from document_ai.pdf_qa_agent import PDFQAAgent

# -----------------------------
# App & CORS
# -----------------------------
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
        await asyncio.to_thread(create_tables)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")

# -----------------------------
# Live Reload (WebSocket + Watchdog)
# -----------------------------
# (Imports moved to the top section)

class LiveReloadHandler(FileSystemEventHandler):
    def __init__(self, queue):
        self.queue = queue
    def on_modified(self, event):
        if not event.is_directory:
            # Signal a reload
            asyncio.run_coroutine_threadsafe(self.queue.put("reload"), loop)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()
reload_queue = asyncio.Queue()
loop = asyncio.get_event_loop()

@app.websocket("/ws-reload")
async def websocket_reload(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_reloads():
    while True:
        await reload_queue.get()
        # Debounce a bit to avoid double-reloads
        await asyncio.sleep(0.5)
        # Clear queue if multiple changes happened
        while not reload_queue.empty():
            reload_queue.get_nowait()
        print("File change detected! Refreshing all clients...")
        await manager.broadcast("reload")

@app.on_event("startup")
async def startup_event():
    # 1. Initialize DB (Blocking to ensure tables exist before first request)
    try:
        print("Initializing database tables...")
        from database.db import create_tables
        create_tables()
        print("✅ Database ready.")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

    # 2. Log environment status (Non-blocking)
    asyncio.create_task(init_db_task())

    # 3. Start the watchdog observer for frontend (dev only, safe to skip on Render)
    if not os.getenv("RENDER"):
        try:
            frontend_path = str(PROJECT_ROOT / "frontend")
            if os.path.exists(frontend_path):
                handler = LiveReloadHandler(reload_queue)
                observer = Observer()
                observer.schedule(handler, frontend_path, recursive=True)
                observer.start()
                app.state.observer = observer
                asyncio.create_task(broadcast_reloads())
        except Exception as e:
            print(f"Live reload watcher not started: {e}")

@app.on_event("shutdown")
def shutdown_event():
    if hasattr(app.state, "observer"):
        app.state.observer.stop()
        app.state.observer.join()

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

# -----------------------------
# Helper Functions
# -----------------------------

def authenticate_student(student_key, password):
    login_result = login_student(student_key, password)
    if not login_result["success"]:
        return None, login_result
    return login_result["student"], login_result

def is_valid_ai_response(answer):
    return "LLM error" not in answer and '"error"' not in answer

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
    
    # If it's a "What is" or "Who is" or "How to", it's NOT a simple chat
    if q.startswith(("what is", "who is", "how to", "tell me", "explain")):
        return False

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
        "env": {
            "HF_TOKEN": bool(os.getenv("HF_TOKEN")),
            "GROQ_API_KEY": bool(os.getenv("GROQ_API_KEY")),
            "TAVILY_API_KEY": bool(os.getenv("TAVILY_API_KEY")),
            "DATABASE_URL": bool(os.getenv("DATABASE_URL"))
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
def register(request: RegisterRequest):
    result = register_student(
        request.first_name,
        request.middle_name,
        request.last_name,
        request.email,
        request.password
    )
    email_result = None
    if result["success"]:
        email_result = send_registration_email(
            to_email=request.email,
            first_name=request.first_name,
            student_key=result["student_key"]
        )
    return {"registration": result, "email": email_result}

@app.post("/login")
def login(request: LoginRequest):
    return login_student(request.student_key, request.password)

@app.post("/onboarding")
def save_onboarding(request: OnboardingRequest):
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
        try:
            onboarding_answers = get_onboarding_answers(student["id"])
            if onboarding_answers:
                answers_list = [{"question": row["question"], "answer": row["answer"]} for row in onboarding_answers]
                profile_agent = ProfileBuilderAgent()
                profile_result = profile_agent.build_profile(answers_list)
                if profile_result["success"]:
                    profile = profile_result["profile"]
                    save_student_profile(
                        student_id=student["id"],
                        degree=profile.get("degree", ""),
                        semester=profile.get("semester", ""),
                        specialization=profile.get("specialization", ""),
                        career_goal=profile.get("career_goal", ""),
                        skills=json.dumps(profile.get("skills", [])) if isinstance(profile.get("skills"), list) else profile.get("skills", ""),
                        weak_areas=json.dumps(profile.get("weak_areas", [])) if isinstance(profile.get("weak_areas"), list) else profile.get("weak_areas", ""),
                        daily_study_hours=profile.get("daily_study_hours", "")
                    )
        except Exception as profile_error:
            print(f"Profile building error: {str(profile_error)}")
        return {"success": True, "message": "Onboarding answers saved and profile built successfully"}
    except Exception as e:
        return {"success": False, "message": f"Error saving onboarding answers: {str(e)}"}

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

    agent = CareerMentorAgent()
    agent.set_student_id(student["id"])

    pdf_data = PDF_MEMORY.get(student["id"])
    if pdf_data:
        agent.set_current_pdf(pdf_data["path"])

    result = agent.answer_question(profile, request.question)

    if is_valid_ai_response(result.get("answer", "")):
        try:
            save_chat_history(
                student_id=student["id"],
                user_message=request.question,
                ai_response=result.get("answer", ""),
                sources_used=json.dumps(result.get("sources", []))
            )
        except Exception as e:
            result["warning"] = f"Answer generated but chat history not saved: {str(e)}"

    return {
        "success": True,
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

    question = request.question.strip()

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
        **result
    }

    return {
        "success": True,
        "route": "local_rag_gemini",
        **result
    }

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

    question = request.question.strip()
    
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

    return StreamingResponse(token_generator(), media_type="text/plain")