import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_NAME: str = "OmniStatus"
    SERVER_PORT: int = 8001
    EXTERNAL_API_KEY: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1"
    COMPLEX_ANALYSIS_MODEL: str = "gpt-4o-mini"

    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "omnistatus"
    MONGO_COLL_NAME: str = "events"
    MONGO_COLL_VICTORIA: str = "victoria_history"

    # Analysis
    SYSTEM_PROMPT: str = (
        "You are a video surveillance monitoring assistant. "
        "You analyze detection events from security cameras (people, vehicles, objects, motion, intrusions). "
        "Given a list of camera events, write a concise summary in Spanish of what happened during the time window. "
        "Focus on: number of detections, unusual activity, recurring patterns, potential threats, or anything notable. "
        "You must respond EXCLUSIVELY with valid JSON containing keys: "
        "{\"score\": float between 0 and 1, \"text\": string}. "
        "score=0 means fully normal (no activity or routine), score=1 means critical (intrusion, threat, unusual activity). "
        "The 'text' field must not exceed 200 characters. "
        "Do not include anything outside the JSON object."
    )
    PROMPT_ANALYSIS: str = "Summarize the camera detections and return JSON {\"score\":float,\"text\":string}. text max 200 chars."

    # Alerts
    ALERT_SCORE_THRESHOLD: float = 0.5
    WINDOW_SECONDS: int = 300
    ANALYZE_INTERVAL: int = 300
    ENABLE_COMPLEX_ANALYSIS_CRON: int = 1
    COMPLEX_ANALYSIS_LOOKBACK_HOURS: int = 3
    COMPLEX_ANALYSIS_CRON_HOURS: int = 3
    COMPLEX_ANALYSIS_SUMMARY_MAX_CHARS: int = 200
    COMPLEX_ANALYSIS_MAX_EVENTS: int = 500
    COMPLEX_ANALYSIS_PROMPT: str = (
        "You are analyzing video surveillance camera detections for the provided time window. "
        "Summarize what was detected: people, vehicles, motion, objects, or any suspicious activity. "
        "Highlight the most relevant detections, recurring patterns, and anything that could indicate a threat or intrusion. "
        "Return JSON with keys score (0=normal/routine, 1=critical/threat) and text. "
        "text must be a concise summary in Spanish, max 200 characters."
    )

    # Telegram
    ENABLE_TELEGRAM: int = 0
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # TTS
    ENABLE_TTS: int = 0
    TTS_URL: str = "https://api.openai.com/v1/audio/speech"
    TTS_MODEL: str = "gpt-4o-mini-tts"
    TTS_VOICE: str = "verse"
    TTS_OUTPUT: str = "alerta.mp3"
    TTS_MESSAGE: str = "Security alert detected"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
