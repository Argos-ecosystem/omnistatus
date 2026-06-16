import json
import re
import httpx
from typing import List, Dict, Any
from app.config import settings


def format_event_for_analysis(event: Dict[str, Any]) -> str:
    count = int(event.get("event_count") or 1)
    score = event.get("score")
    avg_score = event.get("avg_score")
    summary = event.get("summary") or event.get("text") or ""
    first_seen = event.get("first_seen")
    last_seen = event.get("last_seen")

    details = [f"count={count}"]
    if score is not None:
        details.append(f"score={score}")
    if avg_score is not None:
        details.append(f"avg_score={avg_score}")
    if first_seen and last_seen:
        details.append(f"seen={first_seen}..{last_seen}")

    samples = event.get("samples") or []
    samples_text = ""
    if samples:
        samples_text = " samples=" + " | ".join(str(sample) for sample in samples[:3])

    return (
        f"[{event.get('timestamp')}] {event.get('source')}: "
        f"{summary} ({', '.join(details)}){samples_text}"
    )


async def openai_analyze_events(
    events: List[Dict[str, Any]],
    *,
    model: str | None = None,
    prompt: str | None = None,
    system_prompt: str | None = None,
) -> Dict[str, Any]:
    seen: set[str] = set()
    unique_lines: list[str] = []
    for event in events:
        line = format_event_for_analysis(event)
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)
    events_text = "\n".join(unique_lines) or "(no events)"

    system_msg = system_prompt or settings.SYSTEM_PROMPT
    user_msg = f"{prompt or settings.PROMPT_ANALYSIS}\n\nEvents:\n{events_text}"

    payload = {
        "model": model or settings.OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )

        if r.status_code != 200:
            return {"score": 0.0, "text": f"OpenAI {r.status_code}: {r.text[:200]}"}

        content = r.json()["choices"][0]["message"]["content"]
        try:
            parsed = json.loads(content)
        except Exception:
            m = re.search(r"\{.*\}", content, flags=re.DOTALL)
            parsed = json.loads(m.group(0)) if m else {"score": 0.0, "text": "Parse error"}

        score = float(parsed.get("score", 0.0))
        text = parsed.get("text") or "No summary"
        return {"score": max(0.0, min(score, 1.0)), "text": text}

    except Exception as e:
        return {"score": 0.0, "text": f"Analysis error: {e}"}
