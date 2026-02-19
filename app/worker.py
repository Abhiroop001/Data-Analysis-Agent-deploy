import pandas as pd
import json
import os
from redis import Redis
from app.agents.orchestrator import run_pipeline

redis_conn = Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True
)

def run_eda_job(job_id, file_path, prompt, target):

    try:
        # Large dataset safe loading
        if file_path.endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_parquet(file_path)

        result = run_pipeline(df, target=target)

        redis_conn.set(job_id, json.dumps({
            "insights": result.get("insights"),
            "profile_html": result.get("profile_html"),
            "visualizations": result.get("visualizations"),
            "anomalies": result.get("anomalies"),
            "scaledown": result.get("scaledown"),
            "automl": result.get("automl")
        }))

    except Exception as e:
        redis_conn.set(job_id, json.dumps({
            "error": str(e)
        }))

    finally:
        # Optional cleanup
        if os.path.exists(file_path):
            os.remove(file_path)
