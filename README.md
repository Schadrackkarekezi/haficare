# HafiCare

HafiCare is a multi-tenant clinic SaaS: an AI-assisted booking assistant clinics sign up for. Each clinic gets its own staff dashboard (manage doctors, schedules, appointments) and a patient-facing chat app (find a doctor, check symptoms, book an appointment) — sharing one login, one multi-tenant backend, and a LangGraph agent with a real MCP server for tool-calling.

---

## Product surfaces

- **Staff dashboard** (`/dashboard`) — manage a clinic's doctor roster and weekly availability, view/cancel all of the clinic's appointments.
- **Patient app** (`/app`) — chat-based symptom triage and doctor matching *scoped to the patient's own clinic*, with structured doctor recommendation cards, a real availability slot picker, and a persistent "My Appointments" view. Booking is not chat-only: a patient can also book directly from a recommendation card.
- One login page, role-based routing after auth (staff → dashboard, patient → app).
- A legacy single-tenant Streamlit demo (`app.py`) from an earlier iteration still works standalone (unscoped, global Rwanda-wide doctor directory) but is superseded by the product above — kept as-is, not built on further.

## Features

- **Doctor search (RAG)** — embeds the user's question and ranks a clinic's own doctor roster by cosine similarity (see "Neo4j clinic-scoping" below for why this isn't a naive ANN-index query). The legacy `app.py` path still uses a real Neo4j vector index over a global directory.
- **Pharmacy lookup** — queries a Neo4j graph of pharmacies by city. Shared across all clinics (not clinic-owned data).
- **Symptom triage (informational)** — vector search against a curated symptom/condition knowledge base in Neo4j, synthesized into a plain-language summary by an LLM. **Not a real diagnosis** — always includes a disclaimer and a recommendation to see a doctor. Shared across all clinics.
- **Appointment booking** — real doctor availability (staff-configured weekly hours), persisted in Postgres with double-booking prevention, cancellation, and hard tenant isolation (a clinic can never read or write another clinic's doctors/appointments/patients).
- **Auth** — hand-rolled JWT (bcrypt password hashing), stateless, clinic_id/role carried as token claims and enforced server-side on every request — never trusted from client input.

## Architecture

```text
Next.js frontend (frontend/)
   -> Route Handlers (BFF): browser only ever talks same-origin to these;
      they hold the JWT in an httpOnly cookie and proxy to FastAPI with a Bearer header
        -> FastAPI backend (api/): auth, clinics, doctors, appointments, chat
             -> chat endpoint wraps a LangGraph StateGraph (graph/)
                  -> planner node (LLM structured-output intent classification + slot extraction)
                  -> conditional routing -> {doctor, pharmacy, diagnosis, appointment} sub-agent nodes
                       -> each sub-agent node calls tools loaded from a local MCP server (mcp_server/) over stdio
                            -> MCP tools wrap real logic in features/ (Neo4j RAG for doctor/diagnosis,
                               Neo4j lookup for pharmacy, SQLAlchemy/Postgres for appointments/doctors)
```

The planner classifies user intent and extracts slots (e.g. city for pharmacy; doctor/date/time for appointments) via an LLM with structured output. If required slots are missing, it asks a follow-up question instead of routing to a sub-agent. `clinic_id`/`patient_user_id` are injected into the graph's state **server-side from the authenticated JWT** before the graph runs — never derived from message text or client input. Conversation state is tracked per patient via LangGraph's `MemorySaver` checkpointer, keyed by `{user_id}:{thread_id}`.

### Neo4j clinic-scoping

A naive `WHERE node.clinic_id = $clinic_id` filter bolted onto the ANN vector index (`db.index.vector.queryNodes`) is unsound: that call ranks the top-k nearest neighbors across *every* clinic combined, then filters — so a small clinic's doctors can fall outside the global top-k and searches return empty even when a real match exists, and this gets worse as more clinics sign up. Instead, the clinic-scoped path (`vector_search_doctors_for_clinic`) fetches the clinic's own (realistically small) doctor roster via a plain indexed Cypher match, then ranks by cosine similarity in Python. Revisit if a single clinic's roster ever grows into the hundreds.

## Known limitations

- The MCP server is spawned fresh (as a stdio subprocess) for each tool call rather than kept alive across turns. Deliberate simplification for this project's scale — it adds real per-turn latency. A production version would keep a persistent MCP session (e.g. over SSE/HTTP) instead.
- Neo4j and Postgres connections are opened per call rather than pooled long-term — noted as a future improvement rather than fixed here.
- JWTs are stateless with no revocation list — a deactivated account keeps API access until its token naturally expires (`JWT_EXPIRE_MINUTES`, default 24h).
- The symptom/condition knowledge base is a small, hand-authored, generic reference set — not sourced from real patient data or a medical database — and the diagnosis feature is explicitly informational, never a substitute for professional medical advice.
- Not yet built: public deployment, Terms of Service/privacy policy, billing, or any compliance program. The architecture is designed to make these possible, not to skip them — opening real public signups is a deliberate later decision, not a side effect of this codebase existing.

---

## Tech Stack

- **Python 3.11**, **FastAPI**, **LangGraph** for the planner + sub-agent orchestration
- **MCP** (Model Context Protocol) for tool-calling, via a local `mcp_server/`
- **Neo4j** for graph storage + vector search (doctors, pharmacies, symptom/condition knowledge base)
- **PostgreSQL** (via SQLAlchemy) for multi-tenant relational data: clinics, users, doctors, appointments, weekly hours
- **SQLite** (via SQLAlchemy) — legacy, still backs the standalone `app.py` demo only
- **OpenAI (GPT-4o)** for embeddings and LLM reasoning
- **Next.js** (App Router, TypeScript, Tailwind) + **Streamlit** (legacy demo UI)

---

## Running it locally

### 1. Backend

```bash
# from the repo root
uv venv --python 3.11 && source .venv/bin/activate   # or any Python 3.11+ venv
uv pip install -r requirements.txt
```

Fill in `.env` (see `.env` in the repo for the exact keys expected): `OPENAI_API_KEY_2`, `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`, and `DATABASE_URL` (a Postgres connection string — [Neon](https://neon.tech) free tier works well). `JWT_SECRET_KEY` is auto-generated already; keep it identical to `frontend/.env.local`'s copy.

```bash
python -m data.seed_demo_clinic   # creates a demo clinic + doctors + demo staff/patient logins
uvicorn api.main:app --reload --port 8001   # port 8000 may already be in use by something else on your machine
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000 by default
```

`frontend/.env.local` needs `JWT_SECRET_KEY` (must match the backend's) and `INTERNAL_API_BASE_URL` (defaults to `http://localhost:8001`, matching the backend port above).

### 3. Legacy Streamlit demo (optional, standalone)

```bash
streamlit run app.py
```

### Tests

```bash
pytest tests/   # backend: unit + cross-tenant isolation + real MCP protocol tests, no external credentials needed
cd frontend && npm run build && npm run lint   # frontend: type-check + lint
```

---

## Project Structure

```text
haficare/
├── api/            # FastAPI backend: auth, clinics, doctors, appointments, chat routers
├── data/           # CSV seed data, loaders, seed_demo_clinic.py
├── db/             # Neo4j interface, Postgres models (multi-tenant), SQLite models (legacy)
├── features/       # Core business logic: doctor/pharmacy search, diagnosis, appointments
├── frontend/       # Next.js app: staff dashboard + patient app, BFF route handlers, proxy.ts
├── graph/          # LangGraph planner + sub-agent nodes + state
├── llm/            # OpenAI client wrappers
├── mcp_server/     # Local MCP server exposing tool-calling endpoints
├── tests/          # pytest suite
├── app.py          # Legacy single-tenant Streamlit demo
├── requirements.txt
└── .gitignore
```
