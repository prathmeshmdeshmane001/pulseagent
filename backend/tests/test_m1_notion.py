import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.tools.notion_mcp import search_notion

@pytest.mark.asyncio
async def test_notion_search():
    results = await search_notion("Project X architecture")
    assert len(results) > 0
    assert results[0].source == "notion"
    assert "Project X" in results[0].page_title or "Project X" in results[0].snippet
    assert results[0].permalink.startswith("https://notion.so")

@pytest.mark.asyncio
async def test_chat_m1_single_source():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/chat",
            json={"query": "What are the core goals of Project X?"}
        )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "evidence" in data
    assert len(data["evidence"]) > 0
    assert data["session_id"] is not None

    # Check trace endpoint
    session_id = data["session_id"]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        trace_res = await ac.get(f"/trace/{session_id}")
    assert trace_res.status_code == 200
    traces = trace_res.json()
    assert len(traces) >= 2 # retrieve_notion and synthesize
    node_names = [t["node_name"] for t in traces]
    assert "retrieve_multi" in node_names or "retrieve_notion" in node_names
    assert "synthesize" in node_names
