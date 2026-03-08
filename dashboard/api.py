"""
HuntAI Dashboard API
FastAPI backend with REST endpoints and WebSocket for real-time updates.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from database.db import (
    get_stats, get_recent_leads, get_recent_activity,
    get_campaigns, get_db, log_activity
)
from config.manager import ConfigManager

app = FastAPI(title="HuntAI Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = ConfigManager()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                dead.append(connection)
        for d in dead:
            self.active_connections.remove(d)

ws_manager = ConnectionManager()


# ── REST API ──────────────────────────────────────────────────────────────────

@app.get("/api/stats")
async def api_stats():
    """Get dashboard stats."""
    stats = get_stats()
    # Calculate rates
    sent = stats.get('emails_sent', 0)
    replies = stats.get('replies', 0)
    stats['reply_rate'] = f"{(replies/sent*100):.1f}%" if sent > 0 else "0%"
    return stats


@app.get("/api/leads")
async def api_leads(limit: int = 50, campaign_id: Optional[int] = None):
    """Get leads list."""
    conn = get_db()
    if campaign_id:
        rows = conn.execute(
            "SELECT * FROM leads WHERE campaign_id=? ORDER BY created_at DESC LIMIT ?",
            (campaign_id, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/campaigns")
async def api_campaigns():
    """Get all campaigns."""
    return get_campaigns()


@app.get("/api/activity")
async def api_activity(limit: int = 100):
    """Get recent activity log."""
    return get_recent_activity(limit)


@app.get("/api/email-log")
async def api_email_log(limit: int = 50):
    """Get email activity log."""
    conn = get_db()
    rows = conn.execute("""
        SELECT el.*, l.company_name, l.email as recipient_email
        FROM email_log el
        LEFT JOIN leads l ON el.lead_id = l.id
        ORDER BY el.sent_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/config")
async def api_config():
    """Get non-sensitive config."""
    c = config.all()
    # Remove sensitive fields
    for k in ['email_password', 'apify_api_key', 'smtp_password']:
        c.pop(k, None)
    return c


class CampaignRequest(BaseModel):
    name: str
    lead_count: int = 10
    industry: str = ""
    location: str = ""
    company_size: str = "any"


@app.post("/api/campaigns/start")
async def start_campaign(req: CampaignRequest):
    """Start a new campaign from the dashboard."""
    from background_worker.worker import BackgroundWorker
    worker = BackgroundWorker(config)
    campaign_id = worker.start_campaign(
        name=req.name,
        lead_count=req.lead_count,
        industry=req.industry or config.get('target_industry', ''),
        location=req.location or config.get('target_location', ''),
        company_size=req.company_size or config.get('ideal_client_size', 'any'),
    )
    await ws_manager.broadcast({"type": "campaign_started", "campaign_id": campaign_id, "name": req.name})
    return {"success": True, "campaign_id": campaign_id}


@app.get("/api/leads/export")
async def export_leads():
    """Export leads as CSV."""
    import csv
    import io
    conn = get_db()
    rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
    conn.close()

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows([dict(r) for r in rows])

    from fastapi.responses import Response
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=huntai_leads.csv"}
    )


@app.get("/api/ollama/status")
async def ollama_status():
    """Check Ollama status."""
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=3)
        models = r.json().get('models', [])
        return {"online": True, "models": [m['name'] for m in models]}
    except:
        return {"online": False, "models": []}


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time updates via WebSocket."""
    await ws_manager.connect(websocket)
    try:
        # Send initial stats
        stats = get_stats()
        await websocket.send_json({"type": "stats", "data": stats})

        while True:
            # Push stats every 5 seconds
            await asyncio.sleep(5)
            stats = get_stats()
            activity = get_recent_activity(10)
            await websocket.send_json({
                "type": "update",
                "stats": stats,
                "activity": activity,
                "timestamp": datetime.now().isoformat(),
            })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ── Serve Dashboard HTML ──────────────────────────────────────────────────────

DASHBOARD_HTML = Path(__file__).parent / "index.html"

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the dashboard SPA."""
    if DASHBOARD_HTML.exists():
        return FileResponse(str(DASHBOARD_HTML))
    return HTMLResponse("<h1>Dashboard not found. Run build.</h1>")
