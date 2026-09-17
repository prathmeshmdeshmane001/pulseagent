import os
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import httpx
from dotenv import load_dotenv

from app.db.session import get_db
from app.models.db_models import OAuthToken
from app.auth.crypto import encrypt_token, decrypt_token

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

async def get_decrypted_token(provider: str, user_id: str, db: AsyncSession) -> Optional[str]:
    stmt = select(OAuthToken).where(OAuthToken.provider == provider, OAuthToken.user_id == user_id)
    res = await db.execute(stmt)
    token_record = res.scalars().first()
    if token_record and token_record.access_token_encrypted:
        return decrypt_token(token_record.access_token_encrypted)
    return None

async def store_token(
    provider: str,
    user_id: str,
    access_token: str,
    refresh_token: Optional[str],
    expires_in: Optional[int],
    db: AsyncSession
):
    # Remove existing
    await db.execute(delete(OAuthToken).where(OAuthToken.provider == provider, OAuthToken.user_id == user_id))
    
    expires_at = None
    if expires_in:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    record = OAuthToken(
        user_id=user_id,
        provider=provider,
        access_token_encrypted=encrypt_token(access_token),
        refresh_token_encrypted=encrypt_token(refresh_token) if refresh_token else None,
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc)
    )
    db.add(record)
    await db.commit()

@router.get("/status")
async def auth_status(user_id: str = "default_user", db: AsyncSession = Depends(get_db)):
    stmt = select(OAuthToken.provider).where(OAuthToken.user_id == user_id)
    res = await db.execute(stmt)
    connected_providers = set(res.scalars().all())
    return {
        "providers": {
            "notion": "notion" in connected_providers,
            "gmail": "gmail" in connected_providers,
            "jira": "jira" in connected_providers
        }
    }

# --- Notion OAuth ---
@router.get("/notion/login")
async def notion_login(request: Request):
    client_id = os.getenv("NOTION_OAUTH_CLIENT_ID")
    redirect_uri = os.getenv("NOTION_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/notion/callback")
    
    # Detect caller frontend origin from referer or default to FRONTEND_URL
    origin = FRONTEND_URL
    referer = request.headers.get("referer")
    if referer:
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        if parsed.scheme and parsed.netloc:
            origin = f"{parsed.scheme}://{parsed.netloc}"

    if not client_id:
        return RedirectResponse(url=f"{origin}/connect?status=missing_notion_client_id")
    
    url = f"https://api.notion.com/v1/oauth/authorize?owner=user&client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&state={origin}"
    return RedirectResponse(url=url)

@router.get("/notion/callback")
async def notion_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    target_frontend = state if state and state.startswith("http") else FRONTEND_URL
    client_id = os.getenv("NOTION_OAUTH_CLIENT_ID", "")
    client_secret = os.getenv("NOTION_OAUTH_CLIENT_SECRET", "")
    redirect_uri = os.getenv("NOTION_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/notion/callback")

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.notion.com/v1/oauth/token",
                auth=(client_id, client_secret),
                headers={"Notion-Version": "2022-06-28"},
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri
                }
            )
            if res.status_code != 200:
                print(f"Notion OAuth Error: {res.status_code} - {res.text}")
                return RedirectResponse(url=f"{target_frontend}/connect?error=notion_auth_failed")
            data = res.json()
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            if access_token:
                await store_token("notion", "default_user", access_token, refresh_token, None, db)

        return RedirectResponse(url=f"{target_frontend}/connect?status=notion_connected")
    except Exception as e:
        print(f"Notion OAuth exception: {e}")
        return RedirectResponse(url=f"{target_frontend}/connect?error=notion_auth_failed")

# --- Google / Gmail OAuth ---
@router.get("/gmail/login")
async def gmail_login():
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/gmail/callback")
    if not client_id:
        return RedirectResponse(url=f"{FRONTEND_URL}/connect?status=missing_google_client_id")
    
    scopes = "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send"
    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}&access_type=offline&prompt=consent"
    )
    return RedirectResponse(url=url)

@router.get("/gmail/callback")
async def gmail_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/gmail/callback")

    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
        )
        if res.status_code != 200:
            return RedirectResponse(url=f"{FRONTEND_URL}/connect?error=gmail_auth_failed")
        data = res.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in")
        if access_token:
            await store_token("gmail", "default_user", access_token, refresh_token, expires_in, db)

    return RedirectResponse(url=f"{FRONTEND_URL}/connect?status=gmail_connected")

# --- Atlassian Jira OAuth ---
# --- Atlassian Jira OAuth ---
@router.get("/jira/login")
async def jira_login(request: Request):
    client_id = os.getenv("JIRA_OAUTH_CLIENT_ID")
    redirect_uri = os.getenv("JIRA_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/jira/callback")
    
    origin = FRONTEND_URL
    referer = request.headers.get("referer")
    if referer:
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        if parsed.scheme and parsed.netloc:
            origin = f"{parsed.scheme}://{parsed.netloc}"

    if not client_id:
        return RedirectResponse(url=f"{origin}/connect?status=missing_jira_client_id")
    
    import urllib.parse
    scopes = os.getenv("JIRA_OAUTH_SCOPES", "read:jira-work read:jira-user offline_access")
    params = {
        "audience": "api.atlassian.com",
        "client_id": client_id,
        "scope": scopes,
        "redirect_uri": redirect_uri,
        "state": origin,
        "response_type": "code",
        "prompt": "consent"
    }
    url = f"https://auth.atlassian.com/authorize?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=url)

@router.get("/jira/callback")
async def jira_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    target_frontend = state if state and state.startswith("http") else FRONTEND_URL
    client_id = os.getenv("JIRA_OAUTH_CLIENT_ID", "")
    client_secret = os.getenv("JIRA_OAUTH_CLIENT_SECRET", "")
    redirect_uri = os.getenv("JIRA_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/jira/callback")

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://auth.atlassian.com/oauth/token",
                json={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri
                }
            )
            if res.status_code != 200:
                print(f"Jira OAuth Error: {res.status_code} - {res.text}")
                return RedirectResponse(url=f"{target_frontend}/connect?error=jira_auth_failed")
            data = res.json()
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            expires_in = data.get("expires_in")
            if access_token:
                await store_token("jira", "default_user", access_token, refresh_token, expires_in, db)

        return RedirectResponse(url=f"{target_frontend}/connect?status=jira_connected")
    except Exception as e:
        print(f"Jira OAuth exception: {e}")
        return RedirectResponse(url=f"{target_frontend}/connect?error=jira_auth_failed")
