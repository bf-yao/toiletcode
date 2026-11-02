from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "records.json"
WEB_FILE = ROOT / "public" / "index.html"
_write_lock = threading.Lock()

app = FastAPI(title="歐洲廁所地圖")


class RecordInput(BaseModel):
    country_code: str = Field(default="", max_length=3)
    country: str = Field(default="", max_length=80)
    restroom_code: str = Field(min_length=1, max_length=80)
    city: str = Field(default="", max_length=100)
    place: str = Field(default="", max_length=160)
    visited_on: str = Field(default="", max_length=10)
    notes: str = Field(default="", max_length=2000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


def read_records() -> list[dict]:
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def write_records(records: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def ensure_local_writes_enabled() -> None:
    if os.getenv("VERCEL"):
        raise HTTPException(
            status_code=501,
            detail="Vercel 的檔案系統不適合永久儲存。請接上資料庫或 Vercel Blob 後再啟用寫入。",
        )


@app.get("/")
def home() -> FileResponse:
    return FileResponse(WEB_FILE)


@app.get("/api/records")
def list_records() -> list[dict]:
    return read_records()


@app.post("/api/records", status_code=201)
def create_record(payload: RecordInput) -> dict:
    ensure_local_writes_enabled()
    record = {"id": str(uuid4()), **payload.model_dump()} # 隨機產生 id 再轉成字串
    with _write_lock:
        records = read_records()
        records.insert(0, record)
        print(records)
        write_records(records)
    return record


@app.put("/api/records/{record_id}")
def update_record(record_id: str, payload: RecordInput) -> dict:
    ensure_local_writes_enabled()
    with _write_lock:
        records = read_records()
        for index, record in enumerate(records):
            if record.get("id") == record_id:
                updated = {"id": record_id, **payload.model_dump()}
                records[index] = updated
                write_records(records)
                return updated
    raise HTTPException(status_code=404, detail="找不到這筆紀錄")


@app.delete("/api/records/{record_id}", status_code=204)
def delete_record(record_id: str) -> Response:
    ensure_local_writes_enabled()
    with _write_lock:
        records = read_records()
        remaining = [record for record in records if record.get("id") != record_id]
        if len(remaining) == len(records):
            raise HTTPException(status_code=404, detail="找不到這筆紀錄")
        write_records(remaining)
    return Response(status_code=204)
