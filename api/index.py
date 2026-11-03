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
BLOB_PATHNAME = "restroom-records/records.json"
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


def uses_blob_storage() -> bool:
    return bool(
        os.getenv("VERCEL")
        or os.getenv("BLOB_STORE_ID")
        or os.getenv("BLOB_READ_WRITE_TOKEN")
        or os.getenv("VERCEL_BLOB_READ_WRITE_TOKEN")
    )


def read_local_records() -> list[dict]:
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def read_records() -> list[dict]:
    if not uses_blob_storage():
        return read_local_records()

    from vercel.blob import sync as blob

    try:
        result = blob.get_blob(BLOB_PATHNAME, access="private")
    except blob.BlobNotFoundError:
        # Seed a new Blob store from the JSON file bundled with the deployment.
        return read_local_records()
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="無法讀取 Vercel Blob，請確認 Blob store 已連結至專案。",
        ) from error

    try:
        records = json.loads(result.body.decode("utf-8"))
        if not isinstance(records, list):
            raise ValueError("records.json must contain a JSON list")
        return records
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise HTTPException(
            status_code=500, detail="Vercel Blob 中的紀錄 JSON 格式無效。"
        ) from error


def write_records(records: list[dict]) -> None:
    contents = json.dumps(records, ensure_ascii=False, indent=2) + "\n"
    if uses_blob_storage():
        from vercel.blob import sync as blob

        try:
            blob.put_blob(
                BLOB_PATHNAME,
                contents.encode("utf-8"),
                access="private",
                content_type="application/json; charset=utf-8",
                allow_overwrite=True,
                cache_control_max_age=60,
            )
        except Exception as error:
            raise HTTPException(
                status_code=503,
                detail="無法寫入 Vercel Blob，請確認 Blob store 權限與設定。",
            ) from error
        return

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(contents, encoding="utf-8")


@app.get("/")
def home() -> FileResponse:
    return FileResponse(WEB_FILE)


@app.get("/api/records")
def list_records() -> list[dict]:
    return read_records()


@app.post("/api/records", status_code=201)
def create_record(payload: RecordInput) -> dict:
    record = {"id": str(uuid4()), **payload.model_dump()} # 隨機產生 id 再轉成字串
    with _write_lock:
        records = read_records()
        records.insert(0, record)
        write_records(records)
    return record


@app.put("/api/records/{record_id}")
def update_record(record_id: str, payload: RecordInput) -> dict:
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
    with _write_lock:
        records = read_records()
        remaining = [record for record in records if record.get("id") != record_id]
        if len(remaining) == len(records):
            raise HTTPException(status_code=404, detail="找不到這筆紀錄")
        write_records(remaining)
    return Response(status_code=204)
