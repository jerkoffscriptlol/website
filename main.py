import os
import requests
import pathlib
from typing import List, Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel

import discord
from discord.ext import commands
import threading

load_dotenv()

app = FastAPI()
token = os.getenv("DISCORD_BOT_TOKEN")
guild_id = os.getenv("DISCORD_GUILD_ID")
category_id = os.getenv("DISCORD_USERS_CATEGORY_ID")
allowed_role_id = os.getenv("DISCORD_ALLOWED_ROLE_ID")
dashboard_password = os.getenv("DASHBOARD_PASSWORD")
log_channel_id = "1393717563304710247"
headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

user_channels = {}
logs = []

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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
    logs.append({
        "username": info.username,
        "userid": info.userid,
        "displayname": info.displayname,
        "game": info.game,
        "placeid": info.placeid,
        "jobid": info.jobid,
        "thumbnail": info.thumbnail,
        "ip": ip
    })

    print(f"[INFO_REPORT RECEIVED] {info.username} ({info.userid})")

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
                    "content": f"<@&{allowed_role_id}>",
                    "embeds": [{
                        "title": f"{info.displayname} joined",
                        "thumbnail": {"url": info.thumbnail},
                        "fields": [
                            {"name": "Username", "value": info.username},
                            {"name": "User ID", "value": info.userid},
                            {"name": "Game", "value": info.game},
                            {"name": "Job ID", "value": info.jobid}
                        ],
                        "color": 0x00ffcc
                    }],
                    "components": [{
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "style": 5,
                                "label": "Profile",
                                "url": f"https://www.roblox.com/users/{info.userid}/profile"
                            },
                            {
                                "type": 2,
                                "style": 5,
                                "label": "Join Game",
                                "url": f"https://www.roblox.com/games/start?placeId={info.placeid}&gameId={info.jobid}"
                            }
                        ]
                    }]
                }
            )
    return {"status": "ok"}

@app.post("/disconnect")
async def disconnect_user(data: Disconnect):
    userid = data.userid
    if userid in user_channels:
        channel_id = user_channels[userid]
        r = requests.delete(f"https://discord.com/api/v10/channels/{channel_id}", headers=headers)
        if r.status_code == 200 or r.status_code == 204:
            print(f"[CHANNEL DELETED] {userid}'s channel was removed.")
        else:
            print(f"[DELETE FAILED] Could not delete channel for {userid}. Status code: {r.status_code}")
        del user_channels[userid]
    return {"status": "ok"}

@app.post("/auth")
async def auth(request: Request):
    data = await request.json()
    if data.get("password") == dashboard_password:
        return {"status": "ok"}
    raise HTTPException(status_code=403, detail="Unauthorized")

@app.get("/logs")
async def get_logs(request: Request):
    auth = request.headers.get("Authorization")
    if auth != dashboard_password:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return logs

dashboard_path = pathlib.Path("dashboard")
if dashboard_path.exists() and dashboard_path.is_dir():
    app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")

@bot.event
async def on_ready():
    print(f"[BOT ONLINE] Logged in as {bot.user} (ID: {bot.user.id})")

@bot.command()
async def ping(ctx):
    await ctx.send("pong 🏓")

def run_bot():
    bot.run(token)

threading.Thread(target=run_bot).start()
