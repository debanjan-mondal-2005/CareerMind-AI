# 🎯 CareerMind AI: Your Ultimate AI Career Mentor

CareerMind AI is a premium, full-stack AI mentorship platform designed to empower students and professionals with personalized career guidance. Combining the power of **Retrieval-Augmented Generation (RAG)** with **Generative AI Art**, it offers a unique, interactive experience for career exploration.

---

## 🚀 Key Features

- **🧠 Intelligent Mentorship**: Context-aware AI that understands your profile, goals, and skills.
- **📄 Smart PDF Analysis**: Upload your resume or career documents. The AI "reads" them and provides specific advice based on your own data.
- **🎨 AI Image Generation**: Generate career-related visualizations (e.g., "A modern data science workspace") using the FLUX model via Hugging Face.
- **💾 Persistent History**: Secure, user-isolated chat history. Your conversations and generated images are saved and synced across sessions.
- **📊 Interactive Profile**: Onboarding system that builds a personalized student profile for tailored guidance.
- **🌐 Web-Enhanced Search**: Real-time access to the latest career trends and job market data via Tavily.

---

## 🛠️ Tech Stack

### Frontend
- **HTML5/CSS3**: Custom vanilla CSS with Glassmorphism and modern Dark Mode aesthetics.
- **JavaScript (Vanilla)**: High-performance streaming engine for real-time AI responses.
- **FontAwesome**: Premium iconography.

### Backend
- **FastAPI**: High-performance Python web framework.
- **SQLAlchemy**: Database abstraction (SQLite for local, PostgreSQL for cloud).
- **LangChain**: Orchestration for RAG and AI agent logic.

### AI & Models
- **LLM**: Groq (Llama 3) for ultra-fast conversational intelligence.
- **Image Gen**: Hugging Face Inference API (FLUX model).
- **Search**: Tavily AI for real-time web grounding.
- **Embeddings**: Hugging Face Transformers for local vectorization.

---

## 💻 Local Setup (Quick Start)

### 1. Prerequisites
- Python 3.9+
- A [Groq API Key](https://console.groq.com/)
- A [Hugging Face Token](https://huggingface.co/settings/tokens)
- A [Tavily API Key](https://tavily.com/)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-username/CareerMind-AI.git
cd CareerMind-AI

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_key_here
HF_TOKEN=your_token_here
TAVILY_API_KEY=your_key_here
HF_IMAGE_MODEL=black-forest-labs/FLUX.1-dev
```

### 4. Run the Project
```bash
python run_all.py
```
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000

---

## ☁️ Cloud Deployment (A-to-Z Workflow)

To deploy CareerMind AI for **FREE**, follow this verified professional workflow:

### Phase 1: Database & Storage (Supabase)
1. Create a free project on [Supabase](https://supabase.com/).
2. Get your **Connection String** (PostgreSQL) and **Project URL/Key**.
3. Create a Storage Bucket named `career-images` and set it to "Public".

### Phase 2: Backend (Render.com)
1. Link your GitHub repository to [Render](https://render.com/).
2. Select **Web Service** and use the command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
3. Add all variables from your `.env` to the **Environment** tab.
4. Add `DATABASE_URL` (from Supabase).

### Phase 3: Frontend (Vercel)
1. Link your repository to [Vercel](https://vercel.com/).
2. Set the `ROOT_DIRECTORY` to `frontend`.
3. In `script.js`, ensure the `API_BASE_URL` points to your Render URL.

---

## 🏗️ Project Structure

```text
CareerMind-AI/
├── backend/
│   ├── agents/           # AI Mentorship logic
│   ├── image_ai/         # Hugging Face image client
│   ├── rag/              # PDF processing & Vector DB
│   ├── db.py             # Database models & sessions
│   └── main.py           # FastAPI endpoints
├── frontend/
│   ├── index.html        # Main UI
│   ├── script.js         # Frontend logic & API calls
│   └── style.css         # Modern Dark UI styling
├── requirements.txt      # Python dependencies
└── run_all.py            # Local development runner
```

---

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements.

---

**Built with ❤️ by the CareerMind AI Team.**
