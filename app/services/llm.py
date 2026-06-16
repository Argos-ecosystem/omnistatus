import json
import re
import httpx
from typing import List, Dict, Any
from app.config import settings


def _aggregate_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group repeated events by source+text, accumulate counts and time range."""
    groups: Dict[str, Any] = {}
    for ev in events:
        source = (ev.get("source") or "unknown").strip()
        text = (ev.get("summary") or ev.get("text") or "").strip()
        key = f"{source}||{text[:80].lower()}"
        ts = str(ev.get("timestamp") or "")
        count = int(ev.get("event_count") or 1)
        score = ev.get("avg_score") if ev.get("avg_score") is not None else ev.get("score")

        if key not in groups:
            groups[key] = {
                "source": source,
                "text": text,
                "event_count": 0,
                "scores": [],
                "first_seen": ts,
                "last_seen": ts,
            }
        g = groups[key]
        g["event_count"] += count
        if score is not None:
            g["scores"].append(float(score))
        if ts and ts < g["first_seen"]:
            g["first_seen"] = ts
        if ts and ts > g["last_seen"]:
            g["last_seen"] = ts

    result = []
    for g in groups.values():
        entry: Dict[str, Any] = {
            "source": g["source"],
            "text": g["text"],
            "event_count": g["event_count"],
            "first_seen": g["first_seen"],
            "last_seen": g["last_seen"],
            "timestamp": g["last_seen"],
        }
        if g["scores"]:
            entry["avg_score"] = round(sum(g["scores"]) / len(g["scores"]), 3)
        result.append(entry)

    result.sort(key=lambda x: x.get("last_seen", ""), reverse=True)
    return result


def format_event_for_analysis(event: Dict[str, Any]) -> str:
    count = int(event.get("event_count") or 1)
    avg_score = event.get("avg_score")
    summary = event.get("summary") or event.get("text") or ""
    first_seen = event.get("first_seen")
    last_seen = event.get("last_seen")

    details = [f"x{count}"]
    if avg_score is not None:
        details.append(f"score={avg_score}")
    if first_seen and last_seen and first_seen != last_seen:
        details.append(f"{first_seen}..{last_seen}")
    elif first_seen:
        details.append(first_seen)

    return f"[{event.get('source')}] {summary} ({', '.join(details)})"


async def openai_analyze_events(
    events: List[Dict[str, Any]],
    *,
    model: str | None = None,
    prompt: str | None = None,
    system_prompt: str | None = None,
) -> Dict[str, Any]:
    aggregated = _aggregate_events(events)
    events_text = "\n".join(format_event_for_analysis(e) for e in aggregated) or "(no events)"

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
