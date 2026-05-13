# 🚀 CareerMind AI — The Future of Personalized Mentorship

<div align="center">

### 🧠 AI-Powered Career Mentorship Platform

**CareerMind AI** is a next-generation, full-stack AI mentorship ecosystem that combines **Retrieval-Augmented Generation (RAG)**, **real-time web intelligence**, and **generative AI** to deliver highly personalized career guidance for students and aspiring professionals.

Built with a modern asynchronous architecture, the platform bridges the gap between academic profiles and real-world industry trends.

---

**Designed & Developed by Debanjan Mondal ❤️**

</div>

---

# 📌 Table of Contents

* [✨ Overview](#-overview)
* [🚀 Core Features](#-core-features)
* [🧠 AI Capabilities](#-ai-capabilities)
* [🛠️ Tech Stack](#️-tech-stack)
* [🏗️ System Architecture](#️-system-architecture)
* [⚡ Backend Workflow](#-backend-workflow)
* [🌐 Deployment Workflow](#-deployment-workflow)
* [📂 Project Structure](#-project-structure)
* [🔒 Security Features](#-security-features)
* [📊 Future Enhancements](#-future-enhancements)
* [📜 License](#-license)

---

# ✨ Overview

**CareerMind AI** is an intelligent mentorship platform designed to help students make data-driven career decisions using advanced AI technologies.

The platform combines:

* 📄 Resume & PDF Intelligence
* 🧠 Large Language Models (LLMs)
* 🔎 Semantic Search & Vector Databases
* 🌐 Real-Time Web Intelligence
* 🎨 Generative AI Visualizations
* ⚡ Real-Time Streaming Responses

Unlike traditional career portals that provide generic advice, CareerMind AI creates **personalized career roadmaps** based on:

* Skills
* Academic performance
* Goals
* Resume analysis
* Industry trends
* Live job market data

---

# 🚀 Core Features

## 🧠 AI Career Mentorship

Powered by **Llama 3 via Groq Cloud**, the platform delivers:

* Personalized mentorship
* Career planning
* Interview preparation
* Learning roadmaps
* Skill gap analysis
* Real-time career recommendations
* **Hierarchical Academic Onboarding**: Smart dependency-based flow (Stream → Degree → Specialization) for precise profile mapping.
* **Dual-Track Support**: Tailored experiences for both School and College students with custom data collection.

---

## 📄 Precision PDF RAG Engine

Advanced Retrieval-Augmented Generation (RAG) system capable of:

* Reading resumes and academic PDFs
* Extracting:

  * CGPA
  * Skills
  * Certifications
  * Projects
  * Experience
* Semantic chunking with overlap
* Vector similarity search
* Context-aware retrieval

---

## 🌐 Goal-Aware Web Intelligence

A unique feature integrating **Tavily AI** with personal student profiles.

### Features:

* Live industry trend analysis
* Job market intelligence
* Technology demand tracking
* Dynamic roadmap generation
* Personalized web-enhanced recommendations

This allows CareerMind AI to connect:

> **Student Goals ↔ Real-Time Industry Needs**

---

## 🎨 Generative Career Visualization

Integrated **FLUX.1-schnell** image generation pipeline for:

* Career diagrams
* AI-generated learning paths
* Skill maps
* Professional visual roadmaps
* Educational infographics

---

## ⚡ Real-Time Streaming Responses

Asynchronous token streaming architecture enables:

* Instant AI response rendering
* Smooth chat experience
* Live Markdown rendering
* Real-time frontend updates
* High-performance interaction system

---

## 🔒 Secure Student Data Management

Enterprise-style persistence layer using:

* PostgreSQL (Supabase)
* SQLite fallback support
* Secure authentication architecture
* Cross-device chat synchronization
* Persistent onboarding data

---

# 🧠 AI Capabilities

## 🤖 Multi-Agent Intelligence System

CareerMind AI uses a modular AI agent ecosystem:

| Agent                  | Purpose                         |
| ---------------------- | ------------------------------- |
| Mentor Agent           | Personalized mentorship         |
| Roadmap Agent          | Career roadmap generation       |
| Skill Gap Agent        | Skill deficiency analysis       |
| Interview Agent        | Mock interview preparation      |
| Web Intelligence Agent | Real-time industry search       |
| RAG Retrieval Agent    | Semantic document retrieval     |
| Image Agent            | Career visualization generation |
| Profile Agent          | Structured academic profiling   |

---

## 🧩 Retrieval-Augmented Generation (RAG)

### Pipeline:

1. Document Upload
2. Text Extraction
3. Chunking with Overlap
4. Embedding Generation
5. Vector Storage
6. Similarity Search
7. Context Injection
8. LLM Response Generation

### Embedding Features:

* Semantic ranking
* Top-k retrieval
* Context optimization
* **Domain-Specific Knowledge Base**: 13+ specialized TXT archives covering AI, DevOps, Backend, Cybersecurity, and more for hyper-accurate mentorship.

---

# 🛠️ Tech Stack

# 🎨 Frontend

| Technology        | Usage                         |
| ----------------- | ----------------------------- |
| HTML5             | Application structure         |
| CSS3              | Glassmorphism UI              |
| JavaScript (ES6+) | Real-time interaction         |
| Markdown Renderer | Streaming response formatting |

---

# ⚙️ Backend

| Technology | Usage                          |
| ---------- | ------------------------------ |
| FastAPI    | Asynchronous backend framework |
| Python     | Core application logic         |
| SQLAlchemy | ORM & database handling        |
| Uvicorn    | ASGI server                    |
| PostgreSQL | Production database            |
| SQLite     | Local fallback database        |

---

# 🧠 AI & ML Ecosystem

| Technology       | Purpose                       |
| ---------------- | ----------------------------- |
| Groq Cloud       | Ultra-fast LLM inference      |
| Llama 3          | Conversational intelligence   |
| Hugging Face API | Embeddings & image generation |
| Tavily AI        | Real-time web intelligence    |
| FLUX.1-schnell   | Generative image AI           |

---

# ☁️ Cloud & DevOps

| Technology  | Purpose            |
| ----------- | ------------------ |
| Render      | Backend deployment |
| Supabase    | Database & storage |
| GitHub      | Version control    |
| CDN Hosting | Frontend delivery  |

---

# 🏗️ System Architecture

```text
+----------------------+
|      Frontend UI     |
|  HTML + CSS + JS     |
+----------+-----------+
           |
           v
+----------------------+
|      FastAPI API     |
|  Async Backend Core  |
+----------+-----------+
           |
  ---------------------
  |         |         |
  v         v         v

+--------+ +--------+ +----------------+
|  RAG   | | Groq   | | Tavily Search |
| Engine | | LLM    | | Web Intel     |
+--------+ +--------+ +----------------+

           |
           v

+----------------------+
| PostgreSQL Database  |
|   (Supabase Cloud)   |
+----------------------+
```

---

# ⚡ Backend Workflow

```text
User Query
    ↓
FastAPI Endpoint
    ↓
Authentication Check
    ↓
Profile & Chat Retrieval
    ↓
RAG Semantic Search
    ↓
Goal-Aware Web Search
    ↓
Context Assembly
    ↓
Groq Llama 3 Inference
    ↓
Streaming Response
    ↓
Frontend Rendering
```

---

# 🌐 Deployment Workflow

# 1️⃣ Database Layer — Supabase

* Deploy PostgreSQL instance
* Configure connection pooling
* Enable secure cloud storage
* Store persistent student data

---

# 2️⃣ Backend Layer — Render

Deploy FastAPI as a Web Service with:

* Auto deployments from GitHub
* Environment variable injection
* Async startup events
* Production-grade scalability

### Environment Variables

```env
GROQ_API_KEY=
HF_TOKEN=
DATABASE_URL=
TAVILY_API_KEY=
RESEND_API_KEY=
FROM_EMAIL=
```

---

# 3️⃣ Frontend Layer

Deploy frontend using static hosting:

* Global CDN delivery
* Optimized caching
* Zero-latency loading
* Mobile-responsive architecture

---

# 📂 Project Structure

```text
CareerMind-AI/
│
├── backend/
│   ├── agents/              # AI Agents
│   ├── rag/                 # RAG Pipeline
│   ├── database/            # SQLAlchemy Models
│   ├── image_ai/            # Image Generation
│   ├── mail/                # Email Services
│   ├── auth/                # Authentication Logic
│   ├── utils/               # Utility Functions
│   └── main.py              # FastAPI Entry Point
│
├── frontend/
│   ├── index.html           # Main Interface
│   ├── script.js            # Frontend Logic
│   └── style.css            # Glassmorphism Styling
│
├── requirements.txt
├── README.md
└── LICENSE
```

---

# 🔒 Security Features

CareerMind AI is designed with modern security practices:

* Password hashing
* Environment variable protection
* SQL injection prevention
* Secure API handling
* Persistent onboarding verification
* Cross-device session synchronization
* **Production Hardening**: Removed development reset tools, secured health endpoints, and strictly enforced onboarding states.

### Planned Security Enhancements

* Face Authentication
* Fingerprint Authentication
* OAuth2 Login
* Multi-Factor Authentication (MFA)
* Role-Based Access Control (RBAC)

---

# 📊 Future Enhancements

## 🚀 Planned Features

* Voice-based AI mentorship
* AI-generated mock interviews
* Resume ATS scoring
* Personalized job recommendations
* Real-time coding assessment
* AI-powered learning analytics
* Mobile application support
* Offline AI inference
* AI avatar mentor assistant

---

# 📜 License

```text
Copyright © 2026 Debanjan Mondal.
All Rights Reserved.

This project and its source code are proprietary.

No part of this project may be copied, modified,
distributed, published, or used in any form
without explicit written permission from
the author.
```

---

<div align="center">

## ❤️ Designed & Developed by Debanjan Mondal

### CareerMind AI — Transforming Career Guidance with Generative AI

</div>
