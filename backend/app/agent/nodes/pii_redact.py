import time
import re
from typing import List
from app.agent.state import AgentState
from app.models.evidence import Evidence

EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
PHONE_REGEX = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

def _regex_redact(text: str) -> str:
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    text = SSN_REGEX.sub("[REDACTED_SSN]", text)
    return text

def anonymize_text(text: str) -> str:
    if not text:
        return text

    try:
        import spacy
        has_spacy_model = spacy.util.is_package("en_core_web_sm") or spacy.util.is_package("en_core_web_lg")
        if has_spacy_model:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine

            analyzer = AnalyzerEngine()
            anonymizer = AnonymizerEngine()

            results = analyzer.analyze(text=text, entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN"], language="en")
            if results:
                anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
                return anonymized.text
    except BaseException:
        # Graceful fallback to regex redaction if Presidio NLP model is missing or fails
        pass

    return _regex_redact(text)

async def pii_redact_node(state: AgentState) -> dict:
    start_time = time.perf_counter()

    redacted_draft = anonymize_text(state.draft_answer)
    
    redacted_evidence: List[Evidence] = []
    redacted_count = 0
    for ev in state.evidence:
        new_snippet = anonymize_text(ev.snippet)
        if new_snippet != ev.snippet:
            redacted_count += 1
        redacted_evidence.append(
            Evidence(
                source=ev.source,
                permalink=ev.permalink, # Permalinks are kept intact
                timestamp=ev.timestamp,
                snippet=new_snippet,
                page_title=ev.page_title, # Page titles kept intact
                sub_question_id=ev.sub_question_id
            )
        )

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    trace_entry = {
        "node_name": "pii_redact",
        "input_summary": f"Inspected draft answer and {len(state.evidence)} evidence snippets",
        "output_summary": f"PII pass complete. Redacted items: {redacted_count + (1 if redacted_draft != state.draft_answer else 0)}",
        "tokens_used": 0,
        "latency_ms": latency_ms
    }

    return {
        "draft_answer": redacted_draft,
        "final_answer": redacted_draft,
        "evidence": redacted_evidence,
        "total_latency_ms": state.total_latency_ms + latency_ms,
        "trace_logs": state.trace_logs + [trace_entry]
    }
