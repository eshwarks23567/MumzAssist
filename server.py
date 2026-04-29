"""FastAPI REST server wrapping the MumzAssist triage agent."""
import os, sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="MumzAssist API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class TriageRequest(BaseModel):
    message: str
    mode: str = "balanced"


@app.post("/triage")
async def run_triage(req: TriageRequest):
    try:
        from src.agent import triage
        result, meta = triage(req.message, mode=req.mode)
        return {"result": result.model_dump(), "meta": meta}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
async def health():
    return {"ok": True}
