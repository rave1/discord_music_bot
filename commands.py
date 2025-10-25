from discord.ext import commands

from loguru import logger
import state
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

        if not state.song_queue:
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
                state.song_queue.pop(i - 1)
            await ctx.reply("✅ Removed selected items from the queue.")
        except IndexError as e:
            logger.error(e)
            await ctx.reply("Error")

    @bot.hybrid_command(
        name="loop",
        with_app_command=True,
        description="Toggle loop mode: off, one (current song), or all (whole queue).",
    )
    async def loop_command(ctx: commands.Context, mode: str = None):
        """
        /loop -> shows current mode
        /loop one -> loops current song
        /loop all -> loops the entire queue
        /loop off -> disables looping
        """

        valid_modes = {"off", "one", "all"}

        if mode is None:
            await ctx.reply(f"🔁 Current loop mode: **{state.loop_mode}**")
            return

        mode = mode.lower()
        if mode not in valid_modes:
            await ctx.reply("❌ Invalid mode. Use: `off`, `one`, or `all`.")
            return

        state.loop_mode = mode
        await ctx.reply(f"✅ Loop mode set to **{state.loop_mode}**.")

    @bot.hybrid_command(name="clear")
    async def clear_queue(ctx: commands.Context):
        state.song_queue.clear()
        await ctx.reply("Queue cleared.")
