"""Helpers to interact with the Firebase Auth Emulator in tests."""

import os

import httpx

EMULATOR_HOST = os.getenv("FIREBASE_AUTH_EMULATOR_HOST", "localhost:9099")
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "demo-audienceroom")
API_KEY = "fake-api-key"


def create_emulator_user(email: str, password: str = "testpass123") -> dict:
    """Create a user in the emulator and return the signUp response."""
    url = (
        f"http://{EMULATOR_HOST}/identitytoolkit.googleapis.com/v1"
        f"/accounts:signUp?key={API_KEY}"
    )
    resp = httpx.post(url, json={
        "email": email,
        "password": password,
        "returnSecureToken": True,
    })
    resp.raise_for_status()
    return resp.json()


def sign_in_emulator_user(email: str, password: str = "testpass123") -> dict:
    """Sign in with email/password and return the response including idToken."""
    url = (
        f"http://{EMULATOR_HOST}/identitytoolkit.googleapis.com/v1"
        f"/accounts:signInWithPassword?key={API_KEY}"
    )
    resp = httpx.post(url, json={
        "email": email,
        "password": password,
        "returnSecureToken": True,
    })
    resp.raise_for_status()
    return resp.json()


def clear_emulator_users() -> None:
    """Delete all users from the emulator."""
    url = (
        f"http://{EMULATOR_HOST}/emulator/v1/projects/{PROJECT_ID}/accounts"
    )
    httpx.delete(url).raise_for_status()
