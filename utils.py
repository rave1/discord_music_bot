import yt_dlp
import discord
from discord import VoiceProtocol
from loguru import logger
import asyncio
import state
import re


YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "extract_flat": True,
    "skip_download": True,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn -c:a libopus -b:a 96k",
}

FFMPEG_PATH = "/usr/bin/ffmpeg"


async def play_file(
    interaction: discord.Interaction,
    voice_client: VoiceProtocol,
    loop: asyncio.AbstractEventLoop,
    track_url: str,
):
    """Play a YouTube track and handle looping behavior."""
    global current_song

    async def create_source(url: str):
        """Fetch a fresh, valid stream URL from YouTube."""
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise RuntimeError("Failed to extract video info.")
            stream_url = info.get("url")
            if not stream_url:
                raise RuntimeError("No valid stream URL.")
        return discord.FFmpegOpusAudio(
            source=stream_url, executable=FFMPEG_PATH, **FFMPEG_OPTIONS
        )

    async def start_playback(url: str):
        """Start playback and handle completion."""
        global current_song
        current_song = url

        source = await create_source(url)

        def after_playback(error: Exception | None):
            if error:
                logger.error(f"Playback error: {error}")

            async def handle_next():
                global current_song

                if state.loop_mode == "one" and current_song:
                    # 🔁 Replay the same song
                    logger.info("Looping current song...")
                    await start_playback(current_song)
                    return

                # Normal queue behavior
                if state.song_queue:
                    next_song = state.song_queue.pop(0)
                    current_song = next_song
                    await start_playback(next_song)
                else:
                    current_song = None
                    await interaction.channel.send("✅ Queue finished.")

            loop.create_task(handle_next())

        # Start the audio playback
        voice_client.play(source, after=after_playback)
        await interaction.channel.send(f"🎶 Now playing: {url}")

    try:
        await start_playback(track_url)
    except Exception as e:
        logger.error(f"Error in play_file: {e}")
        await interaction.channel.send(f"❌ {e}")
        if voice_client:
            await voice_client.disconnect()


def parse_item_numbers(raw: str) -> list[int]:
    raw = raw.strip()

    # Single number
    if re.fullmatch(r"\d+", raw):
        return [int(raw)]

    # Comma-separated list (e.g., 1,2,3)
    if re.fullmatch(r"\d+(,\d+)+", raw):
        return [int(x) for x in raw.split(",")]

    # Range (e.g., 2-5)
    if re.fullmatch(r"\d+-\d+", raw):
        start, end = map(int, raw.split("-"))
        if start > end:
            raise ValueError("Start of range cannot be greater than end.")
        return list(range(start, end + 1))

    # Otherwise invalid
    raise ValueError("Invalid format. Use a number, comma list, or dash range.")
