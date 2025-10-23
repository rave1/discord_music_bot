import discord

from discord.ext import commands
from dotenv import load_dotenv
from discord.ui.view import View
from components import SelectMusic
import os
import yt_dlp
import asyncio
from schemas import TrackSchema
from utils import play_file

from typing import Any

load_dotenv
token = os.getenv("DISCORD_TOKEN")

if not token:
    raise Exception("Token not found.")

SONG_QUEUES = {}


async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))


def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)


intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)
QUEUE = []


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")


@bot.tree.command(name="play", description="play music duh")
async def play_music(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()

    voice_channel = interaction.user.voice.channel

    if voice_channel is None:
        await interaction.followup.send("You must be in a voice channel")
        return None

    voice_client = interaction.guild.voice_client

    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_client != voice_client.channel:
        await voice_client.move_to(voice_channel)

    ydl_options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
    }

    query = f"ytsearch5:{song_query}"  # ytsearch5 means first five results, yikes

    result = query.split("&")
    query = result[0]

    results = await search_ytdlp_async(query, ydl_options)
    tracks: list[dict[str, Any]] = results.get("entries", [])

    if not tracks:
        await interaction.followup.send("No results found.")
        return

    first_five_tracks: list[dict[str, Any]] = tracks[:5]
    first_five_titles: list[TrackSchema] = [
        {"title": track["title"], "url": track["url"]} for track in first_five_tracks
    ]

    tracks_view = View()
    tracks_view.add_item(
        SelectMusic(tracks=first_five_titles, voice_client=voice_client, queue=QUEUE)
    )
    await interaction.followup.send("Pick one", view=tracks_view, ephemeral=True)


@bot.tree.command(name="stop", description="stop song nigga")
async def stop(interaction: discord.Interaction):
    interaction.guild.voice_client.stop()
    await interaction.response.send_message("Stopping nigga.")


@bot.tree.command(name="skip", description="skip song ludologia")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (
        interaction.guild.voice_client.is_playing()
        or interaction.guild.voice_client.is_paused()
    ):
        voice_client = interaction.guild.voice_client
        voice_client.stop()
        if not QUEUE:
            await interaction.response.send_message(
                "Queue is empty, stopping playback.", ephemeral=True
            )
            return None

        msg = await interaction.response.send_message("Skipping current song")

        next_track = QUEUE.pop(0)
        await play_file(
            track_url=next_track,
            interaction=interaction,
            voice_client=interaction.guild.voice_client,
            queue=QUEUE,
        )
    else:
        await interaction.response.send_message("Not playing anything to skip")
        return None


@bot.tree.command(name="queue", description="queue")
async def queue(interaction: discord.Interaction):
    if not queue:
        await interaction.response.send_message(content="kJU EMPTI")

    message = f"```{QUEUE}```"
    await interaction.response.send_message(content=message)


bot.run(token)
