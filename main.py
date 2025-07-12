from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Dict
import uvicorn

app = FastAPI()
player_data = {}
queued_commands: Dict[str, List[Dict[str, str]]] = {}

class PlayerInfo(BaseModel):
    userid: str
    username: str
    displayname: str
    game: str
    placeid: str
    jobid: str
    thumbnail: str

class DisconnectInfo(BaseModel):
    userid: str

@app.post("/info_report")
async def info_report(info: PlayerInfo):
    player_data[info.userid] = info.dict()
    print(f"[INFO] Player joined: {info.username}")
    return {"status": "ok"}

@app.get("/poll/{userid}")
async def poll(userid: str, username: str = "", gameid: str = "", jobid: str = ""):
    commands = queued_commands.pop(userid, [])
    print(f"[POLL] {username} ({userid}) requested commands")
    return commands

@app.post("/disconnect")
async def disconnect(info: DisconnectInfo):
    print(f"[DISCONNECT] Player {info.userid} disconnected")
    player_data.pop(info.userid, None)
    queued_commands.pop(info.userid, None)
    return {"status": "ok"}

@app.post("/send_command/{userid}")
async def send_command(userid: str, cmd: Dict[str, str]):
    if userid not in queued_commands:
        queued_commands[userid] = []
    queued_commands[userid].append(cmd)
    print(f"[COMMAND] Sent {cmd} to {userid}")
    return {"status": "command queued"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
