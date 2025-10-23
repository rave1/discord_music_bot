import yt_dlp
import discord
from discord import VoiceProtocol


async def play_file(
    track_url: str, interaction: discord.Interaction, voice_client: VoiceProtocol
):
    # yt-dlp options for audio extraction
    ydl_options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": False,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,  # stream
    }

    try:
        # Extract info from URL
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(track_url, download=False)
            if not info:
                await interaction.followup.send(
                    "Could not extract info from the URL.", ephemeral=True
                )
                return None
            stream_url = info.get("url")  # direct stream url

        if not stream_url:
            await interaction.followup.send(
                "No valid stream URL found.", ephemeral=True
            )
            return None

        try:
            source = discord.FFmpegOpusAudio(
                source=stream_url,
                **{
                    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                    "options": "-vn -c:a libopus -b:a 96k",
                },
                executable="/usr/bin/ffmpeg",
            )
            voice_client.play(source)
        except Exception as e:
            await interaction.followup.send(
                f"Error playing track: {str(e)}", ephemeral=True
            )

    except Exception as e:
        await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)
        if voice_client:
            await voice_client.disconnect()
