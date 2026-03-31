from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ai_characters import router as ai_characters_router
from app.api.routes.auth import router as auth_router
from app.api.routes.conversation import router as conversation_router
from app.api.routes.feedback_metrics import router as feedback_metrics_router
from app.api.routes.health import router as health_router
from app.api.routes.practice_sessions import router as practice_sessions_router
from app.api.routes.session_feedback import router as session_feedback_router
from app.api.routes.session_messages import router as session_messages_router
from app.api.routes.session_participants import router as session_participants_router
from app.api.routes.users import router as users_router

app = FastAPI(title="AudienceRoom API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers (prefix is defined in each router) ---
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(ai_characters_router)
app.include_router(practice_sessions_router)
app.include_router(session_participants_router)
app.include_router(session_messages_router)
app.include_router(session_feedback_router)
app.include_router(feedback_metrics_router)
app.include_router(conversation_router)
