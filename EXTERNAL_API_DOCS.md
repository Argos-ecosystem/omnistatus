# OmniStatus External API

This document provides the necessary information for external agents or tools to integrate with the OmniStatus database without affecting the primary internal systems.

## Base Configuration

All endpoints are hosted under the `/ext/` prefix.
You must provide the API key using the `X-API-Key` HTTP header.

**API Key Variable**: `EXTERNAL_API_KEY` (Stored in `.env`)
**Current Demo Key**: `ext-demo-key-12345`  _(Please change this in production)_

This external API is designed with safety in mind:
- **Read-Only**: Endpoints only permit querying data; modification or insertion is not allowed. 
- **Isolated Rate Limiting**: The external API has its own STRICT rate limiter (30 requests/minute) to prevent external agents from overwhelming the internal system.

---

## Endpoints

### 1. Health Check
Quick ping to verify connectivity and API key validity.

**Endpoint:** `GET /ext/health`
**Success Response:** (200 OK)
```json
{
  "ok": true,
  "ts": "2026-04-20T11:00:00.000000+00:00",
  "source": "external"
}
```

---

### 2. Query System Status
Get a quick snapshot of the security situation over the last `N` hours.

**Endpoint:** `GET /ext/status`
**Parameters:**
- `hours` (Query, integer, optional): Number of hours to look back (default: 1, min: 1, max: 24).

**Success Response:** (200 OK)
```json
{
  "ok": true,
  "ts": "2026-04-20T11:00:00.000000+00:00",
  "window_hours": 1,
  "event_count": 45,
  "avg_score": 0.45
}
```

---

### 3. Query Raw Events
Export historical events from the system with flexible filtering.

**Endpoint:** `GET /ext/events`
**Parameters:**
- `start` (Query, string, optional): ISO8601 start date (e.g., `2026-04-20T10:00:00Z`)
- `end` (Query, string, optional): ISO8601 end date.
- `source` (Query, string, optional): Filter by camera or system source.
- `text` (Query, string, optional): Regex search for specific keywords in the event description.
- `limit` (Query, integer, optional): Max records to return (Default: 100, Max: 500).

**Success Response:** (200 OK)
```json
{
  "count": 2,
  "items": [
    {
      "source": "camera_front_door",
      "text": "Person detected lingering at 2 AM",
      "score": 0.85,
      "timestamp": "2026-04-20T02:00:00Z"
    },
    ...
  ]
}
```

---

### 4. Aggregated Summary
Get grouped analytics of the security events per day or per 3-hour blocks. Useful for plotting graphs.

**Endpoint:** `GET /ext/events/summary`
**Parameters:**
- `mode` (Query, string, optional): Aggregation mode. Either `"day"` or `"3h"`. (Default: `"day"`).
- `limit` (Query, integer, optional): Max blocks to return. (Default: 100).

**Success Response (mode="day"):** (200 OK)
```json
{
  "count": 2,
  "items": [
    {
      "count": 150,
      "avg_score": 0.32,
      "tipo": "dia",
      "date": "2026-04-20"
    },
    {
      "count": 94,
      "avg_score": 0.12,
      "tipo": "dia",
      "date": "2026-04-19"
    }
  ]
}
```
