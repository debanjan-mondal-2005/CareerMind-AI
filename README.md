# 🎯 CareerMind AI: The Future of Personalized Mentorship

**CareerMind AI** is a state-of-the-art, full-stack AI mentorship platform designed to empower students with data-driven career guidance. By integrating **Retrieval-Augmented Generation (RAG)** with real-time web intelligence and generative art, it provides a 360-degree ecosystem for career growth.

---

## 🚀 Executive Features

- **🧠 World-Class AI Mentorship**: Powered by Llama 3 (via Groq), providing ultra-fast, context-aware reasoning tailored to individual student profiles.
- **📄 Precision PDF RAG Engine**: Advanced document intelligence that "reads" and extracts specific academic data (CGPA, Projects, Skills) from CVs and Assignments with 100% semantic accuracy.
- **🌐 Goal-Aware Web Intelligence**: A unique feature that bridges the gap between personal data and the live job market using **Tavily AI**, providing roadmaps grounded in real-time trends.
- **🎨 Generative Career Visualization**: Integrated **FLUX.1-schnell** image generation for creating professional career diagrams and visual roadmaps.
- **⚡ Real-Time Streaming Architecture**: A high-performance asynchronous engine that streams AI responses token-by-token for an instantaneous user experience.
- **🔒 Secure Data Persistence**: Enterprise-grade student data management using **PostgreSQL**, ensuring chat histories and profiles are synced securely across all devices.

---

## 🛠️ Advanced Tech Stack

### Frontend Architecture
- **UI/UX**: Custom-engineered **Glassmorphism** design using Vanilla CSS3 (Dark Mode optimized).
- **Engine**: Pure JavaScript (ES6+) streaming client with real-time Markdown rendering.
- **Branding**: Bespoke "Design and Developed by Debanjan Mondal" signature integration.

### Backend Infrastructure
- **API Framework**: **FastAPI** (Python) for asynchronous, high-concurrency request handling.
- **Database**: **PostgreSQL (Supabase)** for production-grade reliability and SQLite for adaptive fallbacks.
- **Orchestration**: Custom-built Multi-Agent system for specialized career tasks (Skill Gap, Roadmaps, Interview Prep).

### AI & Cloud Ecosystem
- **Inference**: **Groq Cloud** for industry-leading response speeds.
- **Vision & Embeddings**: **Hugging Face Inference API** for document vectorization and image generation.
- **Connectivity**: **Resend API** for automated student registration and secure key delivery.

---

## 🏗️ Project Architecture

```text
CareerMind-AI/
├── backend/
│   ├── agents/           # Specialized AI Intelligence (Mentor, Web, Roadmap)
│   ├── rag/              # Vector Storage & Semantic Search Logic
│   ├── database/         # SQLAlchemy Models & Connection Pooling
│   ├── image_ai/         # Generative Art Clients
│   ├── mail/             # Automated Email Services
│   └── main.py           # Core FastAPI Application & Routing
├── frontend/
│   ├── index.html        # Main Application Interface
│   ├── script.js         # Frontend Logic & Streaming Engine
│   └── style.css         # Premium Glassmorphism Styling
├── requirements.txt      # Enterprise Dependencies
└── LICENSE               # Proprietary Licensing Terms

☁️ Production Deployment Workflow
1. Database Layer (Supabase)
Deploy a PostgreSQL instance on Supabase.
Configure the Connection Pooler for stable Render-to-Supabase connectivity.
Initialize Public Storage buckets for persistent image hosting.
2. Backend Logic Layer (Render)
Deploy as a Web Service with auto-deployments from GitHub.
Environment Variable injection for GROQ_API_KEY, HF_TOKEN, DATABASE_URL, and TAVILY_API_KEY.
Asynchronous startup configuration for non-blocking database migrations.
3. Frontend Presence
Hosted via high-performance static hosting.
Global CDN distribution for zero-latency UI loading.
📜 Intellectual Property & Licensing
Copyright © 2026 Debanjan Mondal. All rights reserved.

This project and its source code are proprietary. No part of this project may be copied, modified, distributed, published, or used in any form without explicit written permission from the author.

Designed and Developed with ❤️ by Debanjan Mondal.
