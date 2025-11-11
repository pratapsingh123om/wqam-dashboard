# worker.py - RQ worker runner
import os
from rq import Worker, Queue, Connection
import redis
from dotenv import load_dotenv
load_dotenv()
redis_url = os.getenv("REDIS_URL","redis://redis:6379/0")
conn = redis.from_url(redis_url)
if __name__ == "__main__":
    with Connection(conn):
        q = Queue()
        w = Worker([q])
        w.work()
