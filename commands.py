from discord.ext import commands

from loguru import logger
from state import song_queue
from utils import parse_item_numbers


def setup(bot: commands.Bot):
    @bot.hybrid_command(
        name="disconnect",
        with_app_command=True,
        description="Disconnect the bot from the voice channel",
    )
    async def disconnect(ctx: commands.Context):
        # get voice client and user channel
        voice_client = ctx.guild.voice_client
        voice_channel = getattr(ctx.author.voice, "channel", None)

        if not voice_client:
            await ctx.reply("❌ I'm not connected to any voice channel.")
            return

        if not voice_channel:
            await ctx.reply("❌ You need to be in a voice channel to use this.")
            return

        await voice_client.disconnect()
        await ctx.reply("👋 Disconnected from the voice channel.")

    @bot.hybrid_command(
        name="remove",
        with_app_command=True,
        description="Remove item from queue by number",
    )
    async def remove_item(ctx: commands.Command, item_number: str):
        """
        formats:
        1
        1,2,3
        1-4
        """
        voice_client = ctx.guild.voice_client
        voice_channel = getattr(ctx.author.voice, "channel", None)

        if not song_queue:
            await ctx.reply("queue is empty")
            return None

        if not item_number:
            await ctx.reply("give me number brother!")
            return None
        if not voice_client:
            await ctx.reply("❌ I'm not connected to any voice channel.")
            return None
        if not voice_channel:
            await ctx.reply("❌ You need to be in a voice channel to use this.")
            return None

        try:
            items = parse_item_numbers(raw=item_number)
        except ValueError as e:
            logger.error(f"Error while parsing items to skip: {e}")
            await ctx.reply("Error")

        try:
            for i in sorted(items, reverse=True):  # reverse to avoid index shift
                song_queue.pop(i - 1)
            await ctx.reply("✅ Removed selected items from the queue.")
        except IndexError as e:
            logger.error(e)
            await ctx.reply("Error")
