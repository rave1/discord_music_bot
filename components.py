import discord
from discord.ui import Select
from discord import VoiceProtocol
from discord.components import SelectOption
from schemas import TrackSchema
from utils import play_file


class SelectMusic(Select):
    def __init__(
        self,
        tracks: list[TrackSchema],
        voice_client: VoiceProtocol,
        queue: list[str],
    ):
        options = [
            SelectOption(label=song["title"], value=song["url"]) for song in tracks
        ]
        super().__init__(
            placeholder="Pick your poison",
            options=options,
            min_values=1,
            max_values=1,
        )
        self.voice_client = voice_client
        self.track_queue = queue

    async def callback(self, interaction: discord.Interaction):
        # 0 is the value picked by the user
        track_url: str = self.values[0]
        if self.voice_client.is_playing():
            track = track_url
            if track:
                self.track_queue.append(track)
                await interaction.response.send_message(
                    f"**{track}** added to queue", ephemeral=False
                )
            else:
                await interaction.response.send_message(
                    "Could not find track information", ephemeral=True
                )
        else:
            await interaction.response.send_message(
                f"You chose **{track_url}**!", ephemeral=True
            )
            await play_file(
                track_url=track_url,
                interaction=interaction,
                voice_client=self.voice_client,
                queue=self.track_queue,
            )
