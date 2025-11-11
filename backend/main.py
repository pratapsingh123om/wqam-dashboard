# main.py - ties endpoints together (small surface)
from fastapi import FastAPI, UploadFile, File, Depends, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db import init_db, get_session
from models import User, Upload, ActivityLog
from auth import hash_password, verify_password, create_access_token, decode_token
from sqlalchemy.exc import IntegrityError
import os
from rq import Queue
import redis
from tasks import parse_and_process_upload
import io

# init
init_db()
app = FastAPI(title="WQAM Backend (expanded)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

r = redis.from_url(os.getenv("REDIS_URL"))
q = Queue(connection=r)

# minimal register/login endpoints (demo)
@app.post("/auth/register")
def register(email: str, password: str, name: str = None):
    session = get_session()
    try:
        user = User(email=email, password_hash=hash_password(password), name=name, role="org_user")
        session.add(user)
        session.commit()
        return {"ok": True, "id": user.id}
    except IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        session.close()

@app.post("/auth/login")
def login(email: str, password: str):
    session = get_session()
    user = session.exec(__import__("sqlmodel").sqlmodel.select(User).where(User.email==email)).first()
    session.close()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

# upload endpoint: persists file to MinIO local storage or simple disk and enqueues worker
@app.post("/org/{org_id}/uploads")
async def upload_file(org_id: int, file: UploadFile = File(...), token: str = None):
    # token handling left for brevity - attach proper dependency in production
    contents = await file.read()
    session = get_session()
    u = Upload(org_id=org_id, file_path=file.filename, status="processing")
    session.add(u)
    session.commit()
    upload_id = u.id
    # enqueue parse job
    q.enqueue(parse_and_process_upload, upload_id, contents)
    session.close()
    return {"upload_id": upload_id}

# simple alerts & analytics endpoints
@app.get("/org/{org_id}/alerts")
def list_alerts(org_id: int):
    session = get_session()
    from sqlmodel import select
    res = session.exec(select(__import__("models").Alert).where(__import__("models").Alert.org_id==org_id)).all()
    session.close()
    return {"alerts": [r.dict() for r in res]}

# presence websocket for active users
clients = {}
@app.websocket("/ws/presence")
async def ws_presence(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            uid = data.get("user_id")
            clients[uid] = ws
            # broadcast count to all
            count = len(clients)
            for w in clients.values():
                try:
                    await w.send_json({"active_users": count})
                except:
                    pass
    except WebSocketDisconnect:
        # cleanup
        # remove any closed websockets
        to_remove = [k for k,v in clients.items() if v==ws]
        for k in to_remove:
            del clients[k]
