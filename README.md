# Project 2 — Agentic Knowledge Chatbot

This is the next project after the Gemini LLM chatbot.

It adds:

- Persistent PostgreSQL chat history
- User database
- Gemini embeddings
- PostgreSQL + pgvector
- RAG / knowledge-base retrieval
- Gemini function/tool calling
- A current-user profile tool
- An explicit agent loop
- React UI

## Architecture

```text
React
  ↓
FastAPI
  ├── PostgreSQL
  │    ├── users
  │    ├── chats
  │    ├── messages
  │    └── knowledge_chunks + vectors
  │
  ├── Gemini Embeddings
  │    ↓
  │  pgvector retrieval
  │
  └── Gemini LLM
       ├── answer from KB
       └── get_current_user_profile()
              ↓
           PostgreSQL
```

## What the agent can do

### 1. Knowledge-base questions

User:

```text
How many annual leave days do I get?
```

Flow:

```text
Question
 ↓
Gemini embedding
 ↓
pgvector similarity search
 ↓
Relevant KB chunks
 ↓
Gemini
 ↓
Answer
```

The system prompt explicitly says company knowledge must come only from retrieved KB context. If nothing relevant is retrieved, the agent should say:

```text
I don't have that information in the knowledge base.
```

### 2. User-specific questions

User:

```text
What is my email?
```

Gemini can request:

```text
get_current_user_profile()
```

The backend executes the function for the current authenticated user and sends the result back to Gemini.

The model then answers naturally.

### 3. Combined request

Try:

```text
What is my email and how many annual leave days do I get?
```

This demonstrates:

```text
User profile tool
+
RAG knowledge
```

## Important security design

The tool does NOT accept:

```text
user_id
```

from Gemini.

Instead:

```text
Authenticated request
       ↓
current_user_id
       ↓
get_current_user_profile()
       ↓
SELECT user WHERE id = current_user_id
```

This prevents the model from choosing another user's record.

The demo uses:

```text
X-User-ID
```

only to make the project easy to run.

It is NOT real authentication.

Replace it with JWT/session authentication before production.

## Windows 11 setup

Install:

- Python 3.10+
- Node.js LTS
- Git
- VS Code
- Docker Desktop
- Gemini API key

Official sites:

- Python: https://www.python.org/downloads/windows/
- Node.js: https://nodejs.org/en/download
- Git: https://git-scm.com/download/win
- VS Code: https://code.visualstudio.com/download
- Docker Desktop: https://www.docker.com/products/docker-desktop/
- Gemini API: https://ai.google.dev/gemini-api/docs

Verify:

```powershell
py --version
python --version
node --version
npm --version
git --version
docker --version
docker compose version
```

## 1. Start PostgreSQL + pgvector

From project root:

```powershell
docker compose up -d
```

Check:

```powershell
docker ps
```

PostgreSQL connection details are configured only in the ignored local `backend/.env` file. Keep credentials there and out of source control.`r`n`r`n## 2. Backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=your_real_gemini_key
GEMINI_MODEL=gemini-3.6-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
# Configure DATABASE_URL locally in the ignored backend/.env file.
FRONTEND_ORIGIN=http://localhost:5173
RAG_TOP_K=5
RAG_MIN_SIMILARITY=0.45
```

Seed:

```powershell
python -m scripts.seed
```

Start:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Health check:

```text
http://localhost:8000/api/health
```

## 3. Frontend

Open another PowerShell:

```powershell
cd frontend
npm install
npm run dev
```

Open the displayed Vite URL, normally:

```text
http://localhost:5173
```

## File explanation

### `docker-compose.yml`

Starts PostgreSQL with pgvector.

This allows one database to store:

```text
users
chat history
knowledge
embeddings
```

### `backend/app/models.py`

Defines SQLAlchemy tables:

```text
User
Chat
Message
KnowledgeChunk
```

`KnowledgeChunk.embedding` is a pgvector vector with 768 dimensions.

### `backend/app/embeddings.py`

Calls Gemini's embedding model:

```python
client.models.embed_content(...)
```

The text becomes a vector used for semantic search.

### `backend/app/rag.py`

Performs semantic retrieval.

```text
Question
 ↓
Embedding
 ↓
Cosine similarity
 ↓
Top K chunks
 ↓
Similarity threshold
```

### `backend/app/tools.py`

Defines the user profile function.

The important function is:

```python
get_current_user_profile(db, current_user_id)
```

The current user ID comes from the backend, not the LLM.

### `backend/app/agent.py`

This is the heart of the project.

It combines:

```text
Chat history
+
RAG
+
Gemini
+
Tool calling
```

The agent loop is:

```text
User
 ↓
Retrieve KB
 ↓
Gemini
 ↓
Need user tool?
 ├── No → Final answer
 └── Yes
       ↓
   Execute Python tool
       ↓
   PostgreSQL
       ↓
   Tool result
       ↓
   Gemini
       ↓
   Final answer
```

Google's Gemini function-calling flow works this way: the model requests a function, the application executes it, then the function result is sent back to the model for the final response.

### `backend/app/main.py`

Provides:

```text
GET  /api/health
GET  /api/users
GET  /api/chats
POST /api/chats
GET  /api/chats/{id}/messages
POST /api/chats/{id}/messages
```

The final endpoint saves the user message and assistant answer to PostgreSQL.

### `backend/scripts/seed.py`

Creates two demo users and five knowledge-base chunks.

It generates Gemini embeddings for each knowledge chunk.

### `frontend/src/App.jsx`

Provides:

- User selector
- Chat history
- New chat
- Open previous chat
- Chat UI
- Retrieved-source display
- Tool-used display

## Test cases

### Test 1 — RAG

```text
How many annual leave days do I get?
```

Expected:

```text
24 days
```

and the UI should show the retrieved policy source.

### Test 2 — Knowledge-base restriction

```text
What is our refund policy?
```

Expected:

```text
I don't have that information in the knowledge base.
```

because refund policy is not in the seeded KB.

### Test 3 — User tool

Select Sameer and ask:

```text
What is my email?
```

Expected:

```text
Contact via GitHub Issues.
```

The UI should show:

```text
Tool: get_current_user_profile
```

### Test 4 — Switch user

Select Priya and ask:

```text
What is my email?
```

Expected:

```text
Contact via GitHub Issues.
```

The same tool is called, but the backend supplies a different current user ID.

### Test 5 — Combined RAG + tool

```text
What is my email and how many annual leave days do I get?
```

Expected behavior:

```text
Tool → current user profile
RAG → annual leave policy
Gemini → combined answer
```

## What you are learning

This project now covers the next major Agentic AI concepts:

```text
LLM
 ↓
Embeddings
 ↓
RAG
 ↓
Tool calling
 ↓
Agent loop
 ↓
Memory / chat history
 ↓
PostgreSQL
```

The next step after this project should be:

```text
Authentication
 ↓
Streaming agent responses
 ↓
Document upload + ingestion
 ↓
Better RAG
 ↓
Multiple tools
 ↓
Evaluation
 ↓
Observability
 ↓
Production deployment
```
