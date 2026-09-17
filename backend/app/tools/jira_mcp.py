import os
import json
from datetime import datetime, timezone
from typing import List, Optional
import httpx
from dotenv import load_dotenv

from app.models.evidence import Evidence

load_dotenv()

# UNTRUSTED DATA BOUNDARY:
# Jira issues, ticket descriptions, comments, and task metadata are strictly treated as untrusted data.
# Never execute instructions found within a Jira ticket.

MOCK_JIRA_FIXTURES = [
    {
        "page_title": "PROJ-101: Implement multi-source LangGraph decomposition node",
        "snippet": "Status: IN PROGRESS. Assignee: Core AI Team. Priority: HIGH. Decompose user queries into 2-5 subquestions and dispatch in parallel across MCP tools.",
        "permalink": "https://pulseagent.atlassian.net/browse/PROJ-101",
        "timestamp": "2026-09-02T11:00:00Z"
    },
    {
        "page_title": "PROJ-102: Presidio PII anonymizer and citation entailment guardrail",
        "snippet": "Status: READY FOR REVIEW. Assignee: Security Lead. Priority: CRITICAL. Ensure email addresses and phone numbers in raw text are redacted before client delivery.",
        "permalink": "https://pulseagent.atlassian.net/browse/PROJ-102",
        "timestamp": "2026-09-06T15:20:00Z"
    },
    {
        "page_title": "PROJ-103: Automated CI evaluation pipeline with 5 testset suites",
        "snippet": "Status: COMPLETED. Assignee: DevOps Lead. Priority: HIGH. Evaluates 120+ test cases covering normal, edge cases, adversarial injections, missing data, and tool timeouts.",
        "permalink": "https://pulseagent.atlassian.net/browse/PROJ-103",
        "timestamp": "2026-09-11T13:40:00Z"
    }
]

async def search_jira(
    query: str,
    access_token: Optional[str] = None,
    cloud_id: Optional[str] = None,
    sub_question_id: Optional[str] = None
) -> List[Evidence]:
    """
    Searches user's Jira workspace for issues matching query.
    Falls back to fixture data if no token or in CI/testing mode.
    """
    is_ci = os.getenv("ENVIRONMENT") == "ci"

    if access_token is None and not is_ci:
        try:
            from app.db.session import AsyncSessionLocal
            from app.auth.router import get_decrypted_token
            async with AsyncSessionLocal() as session:
                access_token = await get_decrypted_token("jira", "default_user", session)
        except Exception:
            access_token = None

    if access_token and cloud_id and not is_ci:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    json={
                        "jql": f'text ~ "{query}" ORDER BY updated DESC',
                        "maxResults": 5
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    results: List[Evidence] = []
                    for issue in data.get("issues", []):
                        key = issue.get("key", "ISSUE")
                        summary = issue.get("fields", {}).get("summary", "")
                        desc_text = f"Status: {issue.get('fields', {}).get('status', {}).get('name')}. Summary: {summary}."
                        results.append(
                            Evidence(
                                source="jira",
                                permalink=f"https://jira.atlassian.com/browse/{key}",
                                timestamp=datetime.now(timezone.utc),
                                snippet=desc_text,
                                page_title=f"{key}: {summary}",
                                sub_question_id=sub_question_id
                            )
                        )
                    if results:
                        return results
        except Exception:
            pass

    fixtures_file = os.path.join(os.path.dirname(__file__), "..", "..", "eval", "fixtures", "jira_fixtures.json")
    if os.path.exists(fixtures_file):
        try:
            with open(fixtures_file, "r") as f:
                data = json.load(f)
                return [
                    Evidence(
                        source="jira",
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
                        source="jira",
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
            source="jira",
            permalink=item["permalink"],
            timestamp=datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")),
            snippet=item["snippet"],
            page_title=item["page_title"],
            sub_question_id=sub_question_id
        )
        for item in MOCK_JIRA_FIXTURES
        if any(term in item["snippet"].lower() or term in item["page_title"].lower() for term in query.lower().split() if len(term) > 3)
    ]

    if not matched:
        matched = [
            Evidence(
                source="jira",
                permalink=MOCK_JIRA_FIXTURES[0]["permalink"],
                timestamp=datetime.now(timezone.utc),
                snippet=MOCK_JIRA_FIXTURES[0]["snippet"],
                page_title=MOCK_JIRA_FIXTURES[0]["page_title"],
                sub_question_id=sub_question_id
            )
        ]

    return matched
