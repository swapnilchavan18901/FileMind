# FileMind

**Turn your PDFs into intelligent AI chatbots for your Platforms.**

FileMind is a full-stack platform that lets users upload PDF documents, process them into vector embeddings, and create AI chatbots — embeddable on any website via a simple API key + bot ID over WebSockets.

---

## Architecture Overview

```
┌──────────────────┐   Presigned URL      ┌───────────────┐
│  Next.js Admin   │────────────────────►│   AWS S3       │
│  Dashboard       │ (direct PDF upload)  │  (PDF Storage) │
└────────┬─────────┘                      └───────▲───────┘
         │ REST API                               │ Pulls PDF
         ▼                                        │
┌──────────────────────────┐  ┌────────────┐ ┌────┴──────────┐
│  FastAPI Server          │─►│  RabbitMQ  │►│   Consumer    │
│  (REST + WebSocket +     │  │  (Queue)   │ │   Worker      │
│   Producer — single app) │  └────────────┘ └────┬──────────┘
└────┬─────────────▲───────┘                      │ Chunks, Embeds
     │ Prisma      │ Socket.IO                    │ & Stores
     ▼             │ (Bot ID + API Key)    ┌──────▼──────────┐
┌────────────┐  ┌──┴───────────────┐       │   Qdrant DB     │
│ PostgreSQL │  │  Any Website     │       │  (Vector Store)  │
│ (Database) │  │  (end users)     │       └─────────────────┘
└────────────┘  └──────────────────┘
```

> **How it works:** Bot owners manage everything through the admin dashboard.
> Their end users (website visitors) connect directly to the WebSocket server
> using a bot ID + API key — no FileMind frontend needed.

---

## Tech Stack

| Layer        | Technology                                      |
| ------------ | ----------------------------------------------- |
| Backend API  | FastAPI, Prisma ORM, Python-SocketIO             |
| Database     | PostgreSQL                                       |
| Vector Store | Qdrant                                           |
| Message Queue| RabbitMQ (aio-pika)                              |
| LLM          | OpenAI GPT (chat) + text-embedding-3-small       |
| File Storage | AWS S3 (presigned uploads)                       |
| Auth         | JWT (bcrypt password hashing)                    |

---

## Features

- **Bot Builder** — Create multiple AI bots, each with a custom system prompt and isolated document knowledge base.
- **PDF Upload & Processing** — Frontend uploads PDFs directly to S3 via presigned URLs; the consumer worker automatically chunks, embeds, and stores them in Qdrant.
- **Embeddable Chat** — Share a bot ID + API key with anyone; they connect via Socket.IO from **their own website** and let their visitors chat with the bot.
- **RAG Chat** — Each message retrieves relevant document chunks from Qdrant and generates context-aware answers using OpenAI.
- **API Key Management** — Generate, list, and revoke API keys per bot to control external access.
- **Chat Sessions** — Persistent conversation history with session management (start, resume, list).
- **Subscription & Plans** — Built-in plan/subscription models for usage limits (bots, documents, requests, tokens).
- **Async Everything** — Fully async backend with FastAPI, aio-pika, and AsyncOpenAI for high throughput.

---

## Producer-Consumer Pipeline

### Producer (FastAPI Server)

When a bot owner uploads a PDF through the dashboard:

1. Client requests a presigned S3 URL from the API.
2. Client uploads the PDF **directly to S3** (server never touches the file).
3. Client calls `POST /documents/{id}/complete` to finalize.
4. The server pushes a message `{ document_id, bot_id, user_id }` to RabbitMQ (`document_process_queue`, durable & persistent).

```
Client → S3 (presigned upload)
Client → POST /documents/{id}/complete
  → Validates ownership & prevents double-enqueue
  → publish_document_job() → RabbitMQ
```

### Consumer (Standalone Worker)

The **Consumer** runs as an independent async process, listening to RabbitMQ:

1. Picks up a job from `document_process_queue` (prefetch = 1).
2. **Pulls the PDF from S3**, extracts text using `pypdf`.
3. Splits text into overlapping chunks (1000 chars, 200 overlap).
4. Generates embeddings via OpenAI `text-embedding-3-small` (batched).
5. Upserts vectors into a Qdrant collection (one collection per bot).
6. Cleans up temp files.

**Error Handling:**
- Non-recoverable errors (404, corrupted PDF, empty content) → message is **rejected** (not requeued).
- Transient errors (network, S3 timeouts) → message is **requeued** for retry.

```
RabbitMQ → on_message()
  → Pull PDF from S3
  → Extract text → Chunk → Embed with OpenAI
  → Upsert to Qdrant
  → ACK message
```

---

## Project Structure

```
FileMind_Main/
├── FileMind/                    # Backend (Python)
│   ├── main.py                  # FastAPI app entrypoint
│   ├── prisma/
│   │   └── schema.prisma        # Database schema
│   ├── src/
│   │   ├── routes/              # REST API endpoints
│   │   │   ├── auth.py          #   Register / Login
│   │   │   ├── bots.py          #   CRUD bots
│   │   │   ├── api_key.py       #   API key management
│   │   │   ├── documenation.py  #   Document upload flow
│   │   │   ├── chats.py         #   Chat session/message history
│   │   │   └── testing.py       #   Bot testing endpoint
│   │   ├── sockets/
│   │   │   ├── ws_chats.py      #   Socket.IO server setup
│   │   │   └── handlers.py      #   WebSocket event handlers
│   │   ├── producer/
│   │   │   ├── producer.py      #   RabbitMQ job publisher
│   │   │   └── rabbit_mq.py     #   RabbitMQ connection
│   │   ├── llm/
│   │   │   ├── llm.py           #   OpenAI chat completion
│   │   │   └── prompt/          #   System prompts
│   │   ├── vector/              #   Qdrant retrieval (query-side)
│   │   └── utils/               #   JWT, S3, password, API key utils
│   ├── consumer/                # Consumer Worker (standalone)
│   │   ├── consumer.py          #   Main consumer loop
│   │   ├── rabbit_mq.py        #   RabbitMQ connection
│   │   ├── aws/
│   │   │   └── file_loader.py   #   S3 PDF loader
│   │   └── vector/
│   │       ├── insert.py        #   Chunk, embed, upsert to Qdrant
│   │       ├── qdrantdb.py      #   Qdrant client setup
│   │       └── vector.py        #   Collection management
│   └── requirements.txt
│
└── FileMind-FE/                 # Admin Dashboard (Next.js — separate repo)
```

---

## Environment Variables

Create a `.env` file in the `FileMind/` directory:

```env
DATABASE_URL=postgresql://...          DIRECT_URL=postgresql://...
JWT_SECRET=your-jwt-secret             ACCESS_TOKEN_EXPIRE_MINUTES=1440
AWS_REGION=us-east-1                   AWS_S3_BUCKET=your-bucket
AWS_ACCESS_KEY_ID=...                  AWS_SECRET_ACCESS_KEY=...
RABBIT_MQ_URL=amqp://...              RABBIT_MQ_API_KEY=...
OPENAI_API_KEY=sk-...
QDRANT_DB_CLUSTER_URL=https://...      QDRANT_DB_API_KEY=...
```

---

## Getting Started

```bash
# 1. Backend (Producer API)
cd FileMind && pip install -r requirements.txt
prisma generate && prisma db push
fastapi dev main.py                 # → http://localhost:8000

# 2. Consumer Worker (separate terminal)
cd FileMind && pip install -r consumer/requirements.txt
python -m consumer.consumer
```

> The frontend (Next.js admin dashboard) lives in `FileMind-FE/` — see its own README for setup.

---

## API Endpoints

| Method | Endpoint                              | Description                  |
| ------ | ------------------------------------- | ---------------------------- |
| POST   | `/auth/register`                      | Register a new user          |
| POST   | `/auth/login`                         | Login & get JWT token        |
| POST   | `/bots`                               | Create a bot                 |
| GET    | `/bots`                               | List user's bots             |
| PUT    | `/bots/{bot_id}`                      | Update a bot                 |
| DELETE | `/bots/{bot_id}`                      | Delete a bot                 |
| POST   | `/bots/{bot_id}/api-keys`             | Generate API key             |
| GET    | `/bots/{bot_id}/api-keys`             | List API keys                |
| DELETE | `/api-keys/{id}`                      | Revoke an API key            |
| POST   | `/bots/{bot_id}/documents/upload-url` | Get presigned upload URL     |
| POST   | `/documents/{id}/complete`            | Trigger document processing  |
| GET    | `/chats/sessions/{bot_id}`            | List chat sessions           |
| GET    | `/chats/sessions/{id}/messages`       | Get session messages         |
| POST   | `/testing/{bot_id}`                   | Test bot with a question     |

### WebSocket Events (Socket.IO)

| Event              | Direction | Description                        |
| ------------------ | --------- | ---------------------------------- |
| `connect`          | Client→   | Authenticate with API key + bot ID |
| `start_chat`       | Client→   | Start a new chat session           |
| `resume_chat`      | Client→   | Resume an existing session         |
| `user_message`     | Client→   | Send a message                     |
| `chat_started`     | →Client   | Session created confirmation       |
| `chat_resumed`     | →Client   | Session resumed confirmation       |
| `assistant_message`| →Client   | AI response                        |

### Embeddable Chat — How End Users Connect

FileMind is a **BaaS (Bot as a Service)**. The dashboard is for bot owners only. End users connect from **any website** using Socket.IO:

```js
// On the bot owner's website — their visitors chat with the bot
const socket = io("https://your-filemind-server", {
  auth: { apiKey: "fm_...", botId: "uuid-..." }
});

socket.emit("start_chat");
socket.on("chat_started", ({ sessionId }) => { /* ready */ });
socket.emit("user_message", { content: "How do I...?" });
socket.on("assistant_message", ({ content }) => { /* AI reply */ });
```

---

## Database Models

- **User** — Accounts with email/password auth
- **Bot** — AI bots with custom system prompts
- **ApiKey** — Hashed keys for bot access
- **Document** — Uploaded PDFs with processing status (`queued → processing → ready/failed`)
- **ChatSession / ChatMessage** — Conversation history
- **Plan / Subscription** — Usage-based billing
- **UsageMetric** — Per-key daily request/token tracking
