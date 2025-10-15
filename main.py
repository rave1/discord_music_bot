import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import yt_dlp
import asyncio
import ffmpeg
from collections import deque

load_dotenv
token = os.getenv('DISCORD_TOKEN')

SONG_QUEUES = {}

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync() 
    print(f'Logged in as {bot.user}')

@bot.tree.command(name="play", description="play music duh")
async def play_music(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()

    voice_channel = interaction.user.voice.channel

    if voice_channel is None:
        msg = await interaction.followup.send("You must be in a voice channel")
        await cleanup(msg)
        return

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
    }

    query = f"ytsearch1:{song_query}"


    results = await search_ytdlp_async(query, ydl_options)
    tracks = results.get("entries", [])

    if not tracks:
        msg = await interaction.followup.send("No results found.")
        await cleanup(msg)
        return
    
    first_track = tracks[0]
    audio_url = first_track["url"]
    title = first_track.get("title", "Untitled")

    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()

    SONG_QUEUES[guild_id].append((audio_url, title))

    if voice_client.is_playing() or voice_client.is_paused():
        msg = await interaction.followup.send(f"Added to queue: **{title}**")
    else:
        msg = await interaction.followup.send(f"Now playing: **{title}**")
        await play_next_song(voice_client, guild_id, interaction.channel)

    await send_to_archive(f"Added to queue: **{title}**", 1427664996497621095)
    await cleanup(msg)


@bot.tree.command(name="skip", description="skip this song duh")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        msg = await interaction.response.send_message("Skipping current song")
    else:
        msg = await interaction.response.send_message("Not playing anything to skip")

    await cleanup(msg)

async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        audio_url, title = SONG_QUEUES[guild_id].popleft()

        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k",
        }

        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable="ffmpeg")


        def after_play(error):
            if error:
                print(f"error playing {title}: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)

        voice_client.play(source, after=after_play)
        asyncio.create_task(channel.send(f"Now playing: **{title}**", delete_after = 60))

    else:
        await voice_client.disconnect()
        SONG_QUEUES[guild_id] = deque()


async def send_to_archive(message, CHANNEL_ID):
    channel = bot.get_channel(CHANNEL_ID)
    print("kek")
    if channel:
        await channel.send(message)

async def cleanup(message):
    await asyncio.sleep(60)
    await message.delete()


bot.run(token)