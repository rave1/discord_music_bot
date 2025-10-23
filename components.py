import discord
from discord.ui import Select
from discord import VoiceProtocol
from discord.components import SelectOption
from schemas import TrackSchema
from utils import play_file


class SelectMusic(Select):
    def __init__(self, tracks: list[TrackSchema], voice_client: VoiceProtocol):
        options = [
            SelectOption(label=song["title"], value=song["url"]) for song in tracks
        ]
        self.voice_client = voice_client
        super().__init__(
            placeholder="Pick your poison",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        track_url: str = self.values[0]  # 0 is the value picked by the user
        await interaction.response.send_message(
            f"You chose **{self.values[0]}**!", ephemeral=True
        )
        if track_url and not self.voice_client.is_playing():
            await play_file(
                track_url=track_url,
                interaction=interaction,
                voice_client=self.voice_client,
            )
        else:
            await interaction.followup.send(
                "No valid URL or already playing.", ephemeral=True
            )
