from fastapi import FastAPI
from app.api.logs import get_logs, add_log

app = FastAPI(title="Log Analyzer")

app.get("/logs")(get_logs)
app.post("/logs")(add_log)