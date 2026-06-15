import httpx

from app.config import settings


async def send_telegram_message(text: str) -> dict:
    if not settings.ENABLE_TELEGRAM:
        return {"sent": False, "reason": "telegram_disabled"}

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return {"sent": False, "reason": "telegram_not_configured"}

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, json=payload)
        if response.status_code >= 400:
            return {
                "sent": False,
                "reason": f"telegram_{response.status_code}",
                "detail": response.text[:300],
            }
        return {"sent": True}
    except Exception as exc:
        return {"sent": False, "reason": str(exc)}
