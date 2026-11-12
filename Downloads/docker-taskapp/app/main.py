import json
import os
from contextlib import asynccontextmanager

import psycopg
import redis
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row
from pydantic import BaseModel

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_KEY, CACHE_TTL = "tasks:all", 10

cache = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                 id SERIAL PRIMARY KEY,
                 title TEXT NOT NULL,
                 done BOOLEAN NOT NULL DEFAULT FALSE,
                 created_at TIMESTAMPTZ NOT NULL DEFAULT now())"""
        )
    yield


app = FastAPI(title="Task Tracker", lifespan=lifespan)


class TaskIn(BaseModel):
    title: str


def clean(obj):
    return json.loads(json.dumps(obj, default=str))


@app.get("/health")
def health():
    with db() as conn:
        conn.execute("SELECT 1")
    cache.ping()
    return {"status": "ok"}


@app.post("/tasks", status_code=201)
def create_task(task: TaskIn):
    with db() as conn:
        row = conn.execute(
            "INSERT INTO tasks (title) VALUES (%s) RETURNING *", (task.title,)
        ).fetchone()
    cache.delete(CACHE_KEY)
    return clean(row)


@app.get("/tasks")
def list_tasks():
    cached = cache.get(CACHE_KEY)
    if cached:
        return {"source": "cache", "tasks": json.loads(cached)}
    with db() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    payload = clean(rows)
    cache.setex(CACHE_KEY, CACHE_TTL, json.dumps(payload))
    return {"source": "db", "tasks": payload}


@app.patch("/tasks/{task_id}/done")
def complete_task(task_id: int):
    with db() as conn:
        row = conn.execute(
            "UPDATE tasks SET done = TRUE WHERE id = %s RETURNING *", (task_id,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Task not found")
    cache.delete(CACHE_KEY)
    return clean(row)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    cache.delete(CACHE_KEY)
