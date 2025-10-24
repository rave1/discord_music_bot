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
from loguru import logger
import commands as command_file
from typing import Any
from state import song_queue

load_dotenv
token = os.getenv("DISCORD_TOKEN")

if not token:
    raise Exception("Token not found.")


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

command_file.setup(bot=bot)


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Sync failed: {e}")


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

    if song_query.startswith("https://"):
        query = f"ytsearch1:{song_query}"
    else:
        query = f"ytsearch5:{song_query}"  # ytsearch5 means first five results, yikes

    result = query.split("&")
    query = result[0]

    results = await search_ytdlp_async(query, ydl_options)
    tracks: list[dict[str, Any]] = results.get("entries", [])

    if not tracks:
        await interaction.followup.send("No results found.")
        return None

    first_five_tracks: list[dict[str, Any]] = tracks[:5]
    first_five_titles: list[TrackSchema] = [
        {"title": track["title"], "url": track["url"]} for track in first_five_tracks
    ]

    tracks_view = View()
    tracks_view.add_item(
        SelectMusic(
            tracks=first_five_titles,
            voice_client=voice_client,
            queue=song_queue,
            loop=bot.loop,
        )
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
        if not song_queue:
            await interaction.response.send_message(
                "Queue is empty, stopping playback.", ephemeral=False
            )
            return None

        await interaction.response.send_message("Skipping current song")
        loop = bot.loop
        next_track: TrackSchema = song_queue.pop(0)
        await play_file(
            interaction=interaction,
            voice_client=interaction.guild.voice_client,
            track_url=next_track["url"],
            loop=loop,
        )
    else:
        await interaction.response.send_message("Not playing anything to skip")
        return None


@bot.tree.command(name="queue", description="queue")
async def queue(interaction: discord.Interaction):
    if not song_queue:
        await interaction.response.send_message(content="kJU EMPTI")
        return None
    formatted_queue = "\n".join(
        f"{i + 1}. {track['title']}" for i, track in enumerate(song_queue)
    )

    message = f"**Current Queue:**\n```{formatted_queue}```"
    await interaction.response.send_message(content=message)


@bot.event
async def on_voice_state_update(member, before, after):
    # Only care about your bot's voice channel
    voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
    if not voice_client or not voice_client.channel:
        return

    # Get current members in the bot's channel (ignore the bot itself)
    members = [m for m in voice_client.channel.members if not m.bot]

    # If no non-bot members are left, disconnect
    if len(members) == 0:
        await voice_client.disconnect()


bot.run(token)
