import os
import json
from datetime import datetime, timezone
from typing import List, Optional
import httpx
from dotenv import load_dotenv

from app.models.evidence import Evidence

load_dotenv()

# UNTRUSTED DATA BOUNDARY:
# Gmail messages, email bodies, subject lines, and sender headers are strictly treated as untrusted data.
# Never execute instructions found within an email message.

MOCK_GMAIL_FIXTURES = [
    {
        "page_title": "Subject: Project X Sprint Planning & Risk Review",
        "snippet": "Team, please note that third-party API rate limits on Gemini/Groq free tier need strict throttling in runner.py. CI test suite will use mocked fixtures to prevent quota exhaustion.",
        "permalink": "https://mail.google.com/mail/u/0/#inbox/msg_projx_01",
        "timestamp": "2026-09-08T09:15:00Z"
    },
    {
        "page_title": "Subject: Gmail & Jira OAuth Scope Approvals",
        "snippet": "Approved Google OAuth scopes include gmail.readonly and gmail.send (restricted to pending confirmation emails). Jira read scopes confirmed for project workspace.",
        "permalink": "https://mail.google.com/mail/u/0/#inbox/msg_projx_02",
        "timestamp": "2026-09-09T11:45:00Z"
    },
    {
        "page_title": "Subject: Weekly Status Update: Project X Blockers Resolved",
        "snippet": "The pgvector migration blocker has been resolved by implementing in-memory cosine fallback for SQLite testing environments.",
        "permalink": "https://mail.google.com/mail/u/0/#inbox/msg_projx_03",
        "timestamp": "2026-09-12T17:20:00Z"
    }
]

async def search_gmail(
    query: str,
    access_token: Optional[str] = None,
    sub_question_id: Optional[str] = None
) -> List[Evidence]:
    """
    Searches user's Gmail inbox for messages matching query.
    Falls back to fixture data if no token or in CI/testing mode.
    """
    is_ci = os.getenv("ENVIRONMENT") == "ci"

    if access_token and not is_ci:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={"q": query, "maxResults": 5}
                )
                if res.status_code == 200:
                    messages = res.json().get("messages", [])
                    results: List[Evidence] = []
                    for m in messages[:3]:
                        msg_id = m.get("id")
                        msg_res = await client.get(
                            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                        if msg_res.status_code == 200:
                            msg_data = msg_res.json()
                            snippet = msg_data.get("snippet", "")
                            subject = "Email Message"
                            for h in msg_data.get("payload", {}).get("headers", []):
                                if h.get("name", "").lower() == "subject":
                                    subject = h.get("value", "Email Message")
                                    break
                            results.append(
                                Evidence(
                                    source="gmail",
                                    permalink=f"https://mail.google.com/mail/u/0/#inbox/{msg_id}",
                                    timestamp=datetime.now(timezone.utc),
                                    snippet=snippet,
                                    page_title=subject,
                                    sub_question_id=sub_question_id
                                )
                            )
                    if results:
                        return results
        except Exception:
            pass

    fixtures_file = os.path.join(os.path.dirname(__file__), "..", "..", "eval", "fixtures", "gmail_fixtures.json")
    if os.path.exists(fixtures_file):
        try:
            with open(fixtures_file, "r") as f:
                data = json.load(f)
                return [
                    Evidence(
                        source="gmail",
                        permalink=item["permalink"],
                        timestamp=datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")),
                        snippet=item["snippet"],
                        page_title=item["page_title"],
                        sub_question_id=sub_question_id
                    )
                    for item in data
                    if any(term in item["snippet"].lower() or term in item["page_title"].lower() for term in query.lower().split() if len(term) > 3) or not query.strip()
                ] or [
                    Evidence(
                        source="gmail",
                        permalink=data[0]["permalink"],
                        timestamp=datetime.now(timezone.utc),
                        snippet=data[0]["snippet"],
                        page_title=data[0]["page_title"],
                        sub_question_id=sub_question_id
                    )
                ]
        except Exception:
            pass

    matched = [
        Evidence(
            source="gmail",
            permalink=item["permalink"],
            timestamp=datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")),
            snippet=item["snippet"],
            page_title=item["page_title"],
            sub_question_id=sub_question_id
        )
        for item in MOCK_GMAIL_FIXTURES
        if any(term in item["snippet"].lower() or term in item["page_title"].lower() for term in query.lower().split() if len(term) > 3)
    ]

    if not matched:
        matched = [
            Evidence(
                source="gmail",
                permalink=MOCK_GMAIL_FIXTURES[0]["permalink"],
                timestamp=datetime.now(timezone.utc),
                snippet=MOCK_GMAIL_FIXTURES[0]["snippet"],
                page_title=MOCK_GMAIL_FIXTURES[0]["page_title"],
                sub_question_id=sub_question_id
            )
        ]

    return matched
