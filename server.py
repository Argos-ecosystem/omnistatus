#!/usr/bin/env python3

from app.main import app


if __name__ == "__main__":
    import uvicorn
    from app.config import settings

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.SERVER_PORT, reload=False)
