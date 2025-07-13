import os
import requests
import pathlib
from typing import List, Dict

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

app = FastAPI()
token = os.getenv("DISCORD_BOT_TOKEN")
guild_id = os.getenv("DISCORD_GUILD_ID")
category_id = os.getenv("DISCORD_USERS_CATEGORY_ID")
allowed_role_id = os.getenv("DISCORD_ALLOWED_ROLE_ID")
dashboard_password = os.getenv("DASHBOARD_PASSWORD")
admin_role_id = os.getenv("DISCORD_ADMIN_ROLE_ID")
log_channel_id = "1393717563304710247"
headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

user_channels = {}
logs = []
security = HTTPBearer()


class Info(BaseModel):
    userid: str
    username: str
    displayname: str
    game: str
    placeid: str
    jobid: str
    thumbnail: str


class Disconnect(BaseModel):
    userid: str


@app.post("/info_report")
async def info_report(info: Info, request: Request):
    ip = request.client.host
    log = info.dict()
    log["ip"] = ip
    logs.append(log)

    message = {
        "content": f"<@&{admin_role_id}>",
        "embeds": [{
            "title": info.username,
            "description": f"{info.displayname} is playing **{info.game}**\nPlace ID: {info.placeid}\nJob ID: {info.jobid}",
            "thumbnail": {"url": info.thumbnail}
        }]
    }

    requests.post(f"https://discord.com/api/v10/channels/{log_channel_id}/messages", headers=headers, json=message)
    return {"detail": "Reported"}


@app.post("/disconnect")
async def disconnect(disconnect: Disconnect):
    return {"detail": "Disconnected"}


@app.get("/logs")
async def get_logs(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != dashboard_password:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return logs


@app.post("/auth")
async def auth(req: Dict[str, str]):
    if req.get("password") != dashboard_password:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"message": "Authorized"}


@app.delete("/logs/{userid}")
async def delete_log(userid: str, creds: HTTPAuthorizationCredentials = Depends(security)):
    global logs
    logs = [log for log in logs if log["userid"] != userid]
    return {"detail": "Deleted"}


@app.post("/send_log/{userid}")
async def send_log(userid: str, creds: HTTPAuthorizationCredentials = Depends(security)):
    for log in logs:
        if log["userid"] == userid:
            message = {
                "content": f"<@&{admin_role_id}>",
                "embeds": [{
                    "title": log["username"],
                    "description": f"{log['displayname']} is playing **{log['game']}**\nPlace ID: {log['placeid']}\nJob ID: {log['jobid']}",
                    "thumbnail": {"url": log["thumbnail"]}
                }]
            }
            requests.post(f"https://discord.com/api/v10/channels/{log_channel_id}/messages",
                          headers=headers, json=message)
            return {"detail": "Sent"}
    raise HTTPException(status_code=404, detail="Log not found")


app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")
