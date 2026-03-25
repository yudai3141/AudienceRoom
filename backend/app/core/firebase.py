import firebase_admin
from firebase_admin import credentials

from app.core.config import settings

_app: firebase_admin.App | None = None


def init_firebase() -> firebase_admin.App:
    global _app
    if _app is not None:
        return _app

    cred = credentials.ApplicationDefault() if not _is_emulator() else None
    _app = firebase_admin.initialize_app(
        cred, {"projectId": settings.FIREBASE_PROJECT_ID}
    )
    return _app


def _is_emulator() -> bool:
    import os
    return bool(os.getenv("FIREBASE_AUTH_EMULATOR_HOST"))
