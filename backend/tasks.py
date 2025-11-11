# tasks.py - background tasks for RQ
import pandas as pd
import io
from db import get_session
from models import Upload, Parameter, Threshold, Alert
from sqlmodel import select
import os
import redis
from rq import get_current_job

r = redis.from_url(os.getenv("REDIS_URL"))

def parse_and_process_upload(upload_id: int, file_bytes: bytes):
    """
    - Parse CSV/XLSX bytes
    - Insert Parameter rows
    - Check thresholds and create Alert rows
    - Update Upload.status
    """

    session = get_session()
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception:
        df = pd.read_excel(io.BytesIO(file_bytes))

    # find time column
    time_cols = [c for c in df.columns if c.lower() in ("timestamp","time","date","datetime","date/time")]
    tcol = time_cols[0] if time_cols else df.columns[0]
    df[tcol] = pd.to_datetime(df[tcol], errors='coerce')

    # save parameters
    for _, row in df.iterrows():
        for col in df.columns:
            if col == tcol:
                continue
            try:
                val = float(row[col])
            except Exception:
                continue
            p = Parameter(upload_id=upload_id, org_id=0, parameter=col, value=val, measured_at=row.get(tcol))
            session.add(p)
    session.commit()

    # simplistic threshold checks (example)
    thr_q = session.exec(select(Threshold)).all()
    # build dict
    thr_map = {}
    for t in thr_q:
        thr_map.setdefault(t.parameter, []).append(t)

    parameters = session.exec(select(Parameter).where(Parameter.upload_id==upload_id)).all()
    for p in parameters:
        if p.parameter in thr_map:
            for t in thr_map[p.parameter]:
                exceeded = False
                if t.min_value is not None and p.value < t.min_value:
                    exceeded=True
                if t.max_value is not None and p.value > t.max_value:
                    exceeded=True
                if exceeded:
                    alert = Alert(org_id=p.org_id or 0, parameter=p.parameter, value=p.value, threshold_id=t.id)
                    session.add(alert)
    session.commit()

    # mark upload processed
    u = session.get(Upload, upload_id)
    if u:
        u.status = "processed"
        session.add(u)
        session.commit()

    session.close()
    return {"status":"ok"}
