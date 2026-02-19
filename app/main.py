from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from redis import from_url
from rq import Queue
import uuid
import os
import json

from app.worker import run_eda_job

app = FastAPI(title="Automated Data Science Agent")

# ✅ Correct Redis connection for Render
redis_conn = from_url(
    os.environ.get("REDIS_URL"),
    decode_responses=True
)

queue = Queue(connection=redis_conn)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/create-job")
async def create_job(
    file: UploadFile = File(...),
    prompt: str = Form(None),
    target: str = Form(None)
):
    job_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    queue.enqueue(
        run_eda_job,
        job_id,
        file_path,
        prompt,
        target,
        job_timeout=900
    )

    return {"job_id": job_id}


@app.get("/job-status/{job_id}")
def job_status(job_id: str):
    result = redis_conn.get(job_id)

    if result:
        return {
            "status": "completed",
            "result": json.loads(result)
        }

    return {"status": "running"}


@app.get("/")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )
