
import discord
from discord.ext import commands
from discord import app_commands
import os
import requests
import asyncio

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

API_URL = "http://localhost:8000"
LOG_CHANNEL_ID = 1393717563304710247

def get_userid_from_channel(channel: discord.TextChannel) -> str:
    return channel.name

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user} and synced commands.")

@bot.tree.command(name="resetdb", description="Wipes user data for the current channel.")
async def resetdb(interaction: discord.Interaction):
    userid = get_userid_from_channel(interaction.channel)
    requests.post(f"{API_URL}/disconnect", json={"userid": userid})
    await interaction.response.send_message(f"✅ Data wiped for `{userid}`.", ephemeral=True)

@bot.tree.command(name="deletechan", description="Force-delete this user's channel.")
async def deletechan(interaction: discord.Interaction):
    userid = get_userid_from_channel(interaction.channel)
    requests.post(f"{API_URL}/disconnect", json={"userid": userid})
    await interaction.response.send_message(f"🗑 Deleting channel...")
    await interaction.channel.send("offline (deleting ts)")
    await asyncio.sleep(2)
    await interaction.channel.delete()

@bot.tree.command(name="log", description="Send a log message to the general log channel.")
@app_commands.describe(message="The message to log")
async def log(interaction: discord.Interaction, message: str):
    await bot.get_channel(LOG_CHANNEL_ID).send(f"[LOG] {message}")
    await interaction.response.send_message("✅ Logged!", ephemeral=True)

@bot.tree.command(name="kick", description="Kick the user with a reason.")
@app_commands.describe(reason="Why you are kicking the user")
async def kick(interaction: discord.Interaction, reason: str):
    userid = get_userid_from_channel(interaction.channel)
    command = f'kick("{reason}")'
    requests.post(f"{API_URL}/send_command/{userid}", json={"command": command})
    await interaction.response.send_message(f"✅ Sent kick to `{userid}` for `{reason}`.", ephemeral=True)

@bot.tree.command(name="say", description="Force the user to chat in-game.")
@app_commands.describe(message="What to make them say")
async def say(interaction: discord.Interaction, message: str):
    userid = get_userid_from_channel(interaction.channel)
    command = f'chat("{message}")'
    requests.post(f"{API_URL}/send_command/{userid}", json={"command": command})
    await interaction.response.send_message(f"✅ Sent message to `{userid}`: `{message}`", ephemeral=True)

@bot.tree.command(name="help", description="Show all available commands.")
async def help_cmd(interaction: discord.Interaction):
    text = (
        "**Available Commands:**\n"
        "/resetdb - Wipes user data for this channel\n"
        "/deletechan - Force-deletes this user's channel\n"
        "/log [message] - Sends a message to the general log\n"
        "/kick [reason] - Sends a kick command to the user\n"
        "/say [message] - Forces the user to chat in-game\n"
        "/help - Shows this message"
    )
    await interaction.response.send_message(text, ephemeral=True)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
