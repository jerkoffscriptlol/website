import os
import requests
import time
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
admin_role_id = os.getenv("DISCORD_ADMIN_ROLE_ID")
dashboard_password = os.getenv("DASHBOARD_PASSWORD")
log_channel_id = "1393717563304710247"
headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

user_channels = {}
logs = []
cooldowns = {}
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

    if info.userid in user_channels:
        return {"detail": "Channel already exists"}

    channel_payload = {
        "name": info.userid,
        "type": 0,
        "parent_id": category_id
    }

    channel_response = requests.post(
        f"https://discord.com/api/v10/guilds/{guild_id}/channels",
        headers=headers,
        json=channel_payload
    )

    if channel_response.status_code != 201:
        raise HTTPException(status_code=500, detail="Failed to create channel")

    channel_id = channel_response.json()["id"]
    user_channels[info.userid] = channel_id

    embed = {
        "title": "Player Info",
        "color": 5763719,
        "fields": [
            {"name": "Username", "value": info.username, "inline": False},
            {"name": "Display Name", "value": info.displayname, "inline": False},
            {"name": "User ID", "value": info.userid, "inline": False},
            {"name": "Game", "value": info.game, "inline": False},
            {"name": "Place ID", "value": info.placeid, "inline": False},
            {"name": "Job ID", "value": info.jobid, "inline": False}
        ],
        "thumbnail": {"url": info.thumbnail}
    }

    message_payload = {
        "content": f"<@&{admin_role_id}>",
        "embeds": [embed],
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 5,
                        "label": "Roblox Profile",
                        "url": f"https://www.roblox.com/users/{info.userid}/profile"
                    },
                    {
                        "type": 2,
                        "style": 5,
                        "label": "Join Game",
                        "url": f"roblox://placeId={info.placeid}&gameInstanceId={info.jobid}"
                    }
                ]
            }
        ]
    }

    message_response = requests.post(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        headers=headers,
        json=message_payload
    )

    if message_response.status_code not in [200, 201, 204]:
        raise HTTPException(status_code=500, detail="Failed to send message")

    return {"detail": "Channel and message sent"}


@app.post("/disconnect")
async def disconnect(disconnect: Disconnect):
    user_id = disconnect.userid
    if user_id in user_channels:
        channel_id = user_channels[user_id]
        requests.delete(
            f"https://discord.com/api/v10/channels/{channel_id}",
            headers=headers
        )
        del user_channels[user_id]
    return {"detail": "Channel deleted if existed"}


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
            embed = {
                "title": "Player Info",
                "color": 5763719,
                "fields": [
                    {"name": "Username", "value": log["username"], "inline": False},
                    {"name": "Display Name", "value": log["displayname"], "inline": False},
                    {"name": "User ID", "value": log["userid"], "inline": False},
                    {"name": "Game", "value": log["game"], "inline": False},
                    {"name": "Place ID", "value": log["placeid"], "inline": False},
                    {"name": "Job ID", "value": log["jobid"], "inline": False}
                ],
                "thumbnail": {"url": log["thumbnail"]}
            }

            message_payload = {
                "content": f"<@&{admin_role_id}>",
                "embeds": [embed],
                "components": [
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 5,
                                "label": "Roblox Profile",
                                "url": f"https://www.roblox.com/users/{log['userid']}/profile"
                            },
                            {
                                "type": 2,
                                "style": 5,
                                "label": "Join Game",
                                "url": f"roblox://placeId={log['placeid']}&gameInstanceId={log['jobid']}"
                            }
                        ]
                    }
                ]
            }

            requests.post(
                f"https://discord.com/api/v10/channels/{log_channel_id}/messages",
                headers=headers,
                json=message_payload
            )
            return {"detail": "Sent"}
    raise HTTPException(status_code=404, detail="Log not found")


app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")
