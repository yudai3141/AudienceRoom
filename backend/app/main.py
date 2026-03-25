from fastapi import FastAPI

from app.api.routes.ai_characters import router as ai_characters_router
from app.api.routes.health import router as health_router
from app.api.routes.practice_sessions import router as practice_sessions_router
from app.api.routes.session_participants import router as session_participants_router
from app.api.routes.users import router as users_router

app = FastAPI(title="AudienceRoom API")

app.include_router(health_router)
app.include_router(users_router)
app.include_router(ai_characters_router)
app.include_router(practice_sessions_router)
app.include_router(session_participants_router)