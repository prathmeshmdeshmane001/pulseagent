from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class Evidence(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    source: str = Field(..., description="Source system: notion, gmail, or jira")
    permalink: str = Field(..., description="Direct URL to the source resource")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of the evidence record")
    snippet: str = Field(..., description="Excerpt or summary from the source content")
    page_title: str = Field(..., description="Title of the page, email subject, or issue summary")
    sub_question_id: Optional[str] = Field(None, description="Identifier of the sub-question that requested this evidence")
