import os
import requests
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import uvicorn

app = FastAPI()
token = os.getenv("DISCORD_BOT_TOKEN")
guild_id = os.getenv("DISCORD_GUILD_ID")
category_id = os.getenv("DISCORD_USERS_CATEGORY_ID")
allowed_role_id = os.getenv("DISCORD_ALLOWED_ROLE_ID")
log_channel_id = "1393717563304710247"
headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
user_channels = {}
cmd_queue: Dict[str, List[Dict[str, str]]] = {}

def log_to_discord(text):
    requests.post(
        f"https://discord.com/api/v10/channels/{log_channel_id}/messages",
        headers=headers,
        json={"content": f"[LOG] {text}"}
    )

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
async def info_report(info: Info):
    if info.userid not in user_channels:
        payload = {"name": info.userid, "type": 0, "parent_id": category_id}
        r = requests.post(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=headers, json=payload)
        if r.status_code == 201:
            channel_id = r.json()["id"]
            user_channels[info.userid] = channel_id
        else:
            log_to_discord(f"Failed to create channel for {info.userid}: {r.text}")
            return {"error": "channel creation failed"}
    else:
        channel_id = user_channels[info.userid]

    payload = {
        "content": f"<@&{allowed_role_id}> online",
        "embeds": [{
            "title": "Player Info",
            "color": 5763719,
            "thumbnail": {"url": info.thumbnail},
            "fields": [
                {"name": "Username", "value": info.username, "inline": True},
                {"name": "Display Name", "value": info.displayname, "inline": True},
                {"name": "User ID", "value": info.userid, "inline": False},
                {"name": "Game", "value": info.game, "inline": False},
                {"name": "Place ID", "value": info.placeid, "inline": False},
                {"name": "Job ID", "value": info.jobid, "inline": False}
            ],
            "footer": {"text": "IQSM Bot • Auto Logger"}
        }],
        "components": [{
            "type": 1,
            "components": [
                {
                    "type": 2,
                    "style": 5,
                    "label": "User Profile",
                    "url": f"https://www.roblox.com/users/{info.userid}/profile"
                },
                {
                    "type": 2,
                    "style": 5,
                    "label": "Join Game",
                    "url": f"roblox://join?placeId={info.placeid}&jobId={info.jobid}"
                }
            ]
        }]
    }

    resp = requests.post(f"https://discord.com/api/v10/channels/{channel_id}/messages", headers=headers, json=payload)
    if resp.status_code != 200 and resp.status_code != 201:
        log_to_discord(f"Failed to send embed: {resp.status_code} - {resp.text}")

    return {"status": "ok"}

@app.post("/disconnect")
async def disconnect(info: Disconnect):
    if info.userid in user_channels:
        channel_id = user_channels.pop(info.userid)
        r = requests.delete(f"https://discord.com/api/v10/channels/{channel_id}", headers=headers)
        if r.status_code != 200:
            log_to_discord(f"Failed to delete channel for {info.userid}: {r.text}")
    return {"status": "disconnected"}

@app.post("/send_command/{userid}")
async def send_command(userid: str, request: Request):
    data = await request.json()
    command = data.get("command")
    if not command:
        raise HTTPException(status_code=400, detail="Missing 'command' in request body.")
    if userid not in cmd_queue:
        cmd_queue[userid] = []
    cmd_queue[userid].append({"command": command})
    return {"status": "queued"}

@app.get("/get_command/{userid}")
async def get_command(userid: str):
    if userid in cmd_queue and cmd_queue[userid]:
        return cmd_queue[userid].pop(0)
    return {"command": None}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
