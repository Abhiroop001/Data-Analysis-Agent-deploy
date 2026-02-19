import os
from redis import from_url
from rq import Worker, Connection
redis_conn = from_url(os.environ.get("REDIS_URL"))
if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker(["default"])
        worker.work()
